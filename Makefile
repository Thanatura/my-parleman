build_prefect_worker: ## Build image for GCP (Linux/amd64 platform)
	@echo "Building the image for GCP..."
	docker build --platform linux/amd64 -t europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/prefect-worker -f infra/prefect/worker.Dockerfile . 

push_prefect_worker: build_prefect_worker ## Build and push image to Artifact Registry
	docker push europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/prefect-worker

build_prefect_server: ## Build image for GCP (Linux/amd64 platform)
	@echo "Building the image for GCP..."
	docker build --platform linux/amd64 -t europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/prefect-server -f infra/prefect/server.Dockerfile . 

push_prefect_server: build_prefect_server ## Build and push image to Artifact Registry
	docker push europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/prefect-server

build_backend: ## Build backend image for GCP (Linux/amd64 platform)
	@echo "Building the backend image for GCP..."
	docker build --platform linux/amd64 -t europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/parleman-backend -f infra/app/backend.Dockerfile . 

push_backend: build_backend ## Build and push backend image to Artifact Registry
	docker push europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/parleman-backend

build_frontend: ## Build frontend image for GCP (Linux/amd64 platform)
	@echo "Building the frontend image for GCP..."
	docker build --platform linux/amd64 -t europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/parleman-frontend -f infra/app/frontend.Dockerfile . 

push_frontend: build_frontend ## Build and push frontend image to Artifact Registry
	docker push europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/parleman-frontend

push_all_images: push_prefect_worker push_prefect_server push_backend push_frontend ## Build and push all images to Artifact Registry
	@echo "All images have been built and pushed to Artifact Registry"

setup_prefect_variables:
	@set -euo pipefail; \
	TF_DIR="infra/terraform"; \
	ARTIFACT_REPO="$$(terraform -chdir="$$TF_DIR" output -raw artifact_registry_repository)"; \
	RAW_PREFECT_API_URL="$${PREFECT_API_URL:-}"; \
	if [ -z "$$RAW_PREFECT_API_URL" ]; then \
		echo "PREFECT_API_URL is required"; \
		exit 1; \
	fi; \
	BASE_PREFECT_URL="$$(printf '%s' "$$RAW_PREFECT_API_URL" | sed -E 's#/*$$##; s#/dashboard/api$$##; s#/dashboard$$##; s#/api$$##')"; \
	EFFECTIVE_PREFECT_API_URL="$$BASE_PREFECT_URL/api"; \
	DOCKER_REGISTRY="$$ARTIFACT_REPO"; \
	export PREFECT_API_URL="$$EFFECTIVE_PREFECT_API_URL"; \
	export PREFECT_API_AUTH_STRING="$${PREFECT_API_AUTH_STRING:-}"; \
	echo "Using PREFECT_API_URL=$$EFFECTIVE_PREFECT_API_URL"; \
	uv run --project ingest prefect variable set prefect-api-url "$$EFFECTIVE_PREFECT_API_URL"; \
	uv run --project ingest prefect variable set docker-registry "$$DOCKER_REGISTRY"; \
	uv run --project ingest prefect variable set gcp-project "$$GCP_PROJECT"; \
	uv run --project ingest prefect variable set bq-dataset "$$BQ_DATASET"; \
	uv run --project ingest prefect variable set debat-url "$$DEBAT_URL"; \
	uv run --project ingest prefect variable set deputes-url "$$DEPUTES_URL"; \
	uv run --project ingest prefect variable set scrutins-url "$$SCRUTINS_URL"; \
	uv run --project ingest prefect variable set dossiers-legislatifs-url "$$DOSSIERS_LEGISLATIFS_URL"; \
	uv run --project ingest prefect variable set amendements-url "$$AMENDEMENTS_URL"; \
	uv run --project ingest prefect variable set questions-ecrites-url "$$QUESTIONS_ECRITES_URL"
	@set -euo pipefail; \
	TF_DIR="infra/terraform"; \
	RUNNER_SA_KEY_JSON="$$(terraform -chdir="$$TF_DIR" output -raw runner_service_account_key_json)"; \
	RUNNER_SA_KEY_JSON="$$RUNNER_SA_KEY_JSON" uv run --project ingest python -c 'import os; from prefect.blocks.system import Secret; Secret(value=os.environ["RUNNER_SA_KEY_JSON"]).save("gcp-service-account-info", overwrite=True)'; \
	echo "Updated Prefect Secret block: gcp-service-account-info"

deploy_all_flows:
	@set -euo pipefail; \
	set -a; . ./.env; set +a; \
	uv run --project ingest prefect deploy --all; \
	echo "All flows have been deployed to Prefect"

run_all_flows:
	@set -euo pipefail; \
	set -a; . ./.env; set +a; \
	for d in \
		an-deputes-pipeline/deputes \
		debat-flow/debats \
		scrutin-flow/scrutins \
		dossiers-legislatifs-flow/dossiers_legislatifs \
		amendements-flow/amendements \
		questions-ecrites-flow/questions_ecrites; do \
		echo "Triggering deployment: $$d"; \
		uv run --project ingest prefect deployment run "$$d" & \
	done; \
	wait; \
	echo "All non-dbt deployments have been triggered"

run_marts_api:
	@set -euo pipefail; \
	set -a; . ./.env; set +a; \
	PYTHONPATH="$$(pwd):$$(pwd)/app" uv run --project app uvicorn app.backend.main:app --reload --host 0.0.0.0 --port 8000

run_marts_ui:
	@set -euo pipefail; \
	set -a; . ./.env; set +a; \
	PYTHONPATH="$$(pwd):$$(pwd)/app" PARLEMAN_API_URL="$${PARLEMAN_API_URL:-http://127.0.0.1:8000}" uv run --project app streamlit run app/frontend/App.py
