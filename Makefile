build_metabase: ## Build image for GCP (Linux/amd64 platform)
	@echo "Building the image for GCP..."
	docker pull --platform linux/amd64 metabase/metabase:v0.56.3
	docker tag metabase/metabase:v0.56.3 europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/metabase

push_metabase: build_metabase ## Build and push image to Artifact Registry
	docker push europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/metabase


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
	uv run prefect variable set prefect-api-url "$$EFFECTIVE_PREFECT_API_URL"; \
	uv run prefect variable set docker-registry "$$DOCKER_REGISTRY"; \
	uv run prefect variable set gcp-project "$$GCP_PROJECT"; \
	uv run prefect variable set bq-dataset "$$BQ_DATASET"; \
	uv run prefect variable set debat-url "$$DEBAT_URL"; \
	uv run prefect variable set deputes-url "$$DEPUTES_URL"; \
	uv run prefect variable set scrutins-url "$$SCRUTINS_URL"; \
	uv run prefect variable set dossiers-legislatifs-url "$$DOSSIERS_LEGISLATIFS_URL"; \
	uv run prefect variable set amendements-url "$$AMENDEMENTS_URL"; \
	uv run prefect variable set questions-ecrites-url "$$QUESTIONS_ECRITES_URL"

setup_prefect_secret_blocks:
	@set -euo pipefail; \
	TF_DIR="infra/terraform"; \
	RUNNER_SA_KEY_JSON="$$(terraform -chdir="$$TF_DIR" output -raw runner_service_account_key_json)"; \
	RUNNER_SA_KEY_JSON="$$RUNNER_SA_KEY_JSON" uv run python -c 'import os; from prefect.blocks.system import Secret; Secret(value=os.environ["RUNNER_SA_KEY_JSON"]).save("gcp-service-account-info", overwrite=True)'; \
	echo "Updated Prefect Secret block: gcp-service-account-info"

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
		uv run prefect deployment run "$$d" & \
	done; \
	wait; \
	echo "All non-dbt deployments have been triggered"
