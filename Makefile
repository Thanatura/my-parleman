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
	PREFECT_SERVER_URL="$$(terraform -chdir="$$TF_DIR" output -raw prefect_server_url)"; \
	ARTIFACT_REPO="$$(terraform -chdir="$$TF_DIR" output -raw artifact_registry_repository)"; \
	PREFECT_API_URL="$${PREFECT_SERVER_URL%/}/api"; \
	DOCKER_REGISTRY="$$ARTIFACT_REPO"; \
	prefect variable set prefect-api-url "$$PREFECT_API_URL"; \
	prefect variable set docker-registry "$$DOCKER_REGISTRY"; \
	prefect variable set gcp-project "$$GCP_PROJECT"; \
	prefect variable set bq-dataset "$$BQ_DATASET"; \
	prefect variable set debat-url "$$DEBAT_URL"; \
	prefect variable set deputes-url "$$DEPUTES_URL"; \
	prefect variable set scrutins-url "$$SCRUTINS_URL"; \
	prefect variable set dossiers-legislatifs-url "$$DOSSIERS_LEGISLATIFS_URL"; \
	prefect variable set amendements-url "$$AMENDEMENTS_URL"; \
	prefect variable set questions-ecrites-url "$$QUESTIONS_ECRITES_URL"

setup_prefect_secret_blocks:
	@set -euo pipefail; \
	TF_DIR="infra/terraform"; \
	RUNNER_SA_KEY_JSON="$$(terraform -chdir="$$TF_DIR" output -raw runner_service_account_key_json)"; \
	RUNNER_SA_KEY_JSON="$$RUNNER_SA_KEY_JSON" uv run python -c 'import os; from prefect.blocks.system import Secret; Secret(value=os.environ["RUNNER_SA_KEY_JSON"]).save("gcp-service-account-info", overwrite=True)'; \
	echo "Updated Prefect Secret block: gcp-service-account-info"