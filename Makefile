build_metabase: ## Build image for GCP (Linux/amd64 platform)
	@echo "Building the image for GCP..."
	docker pull --platform linux/amd64 metabase/metabase:v0.56.3
	docker tag metabase/metabase:v0.56.3 europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/${METABASE_IMAGE}

push_metabase: build_metabase ## Build and push image to Artifact Registry
	docker push europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/${METABASE_IMAGE}


build_prefect_worker: ## Build image for GCP (Linux/amd64 platform)
	@echo "Building the image for GCP..."
	docker build --platform linux/amd64 -t europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/prefect-worker -f infra/prefect/Dockerfile . 

push_prefect_worker: build_prefect_worker ## Build and push image to Artifact Registry
	docker push europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/prefect-worker

deploy_prefect_worker:
	gcloud run deploy prefect-worker \
		--image=europe-west1-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/prefect-worker \
		--set-env-vars PREFECT_API_URL=${PREFECT_API_URL} \
		--service-account ${SA_WORKER_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com \
		--no-cpu-throttling \
		--min-instances 1 --memory=2Gi \
		--startup-probe httpGet.port=8080,httpGet.path=/health,initialDelaySeconds=100,periodSeconds=20,timeoutSeconds=20 \
		--args "prefect","worker","start","--install-policy","never","--with-healthcheck","-p","parleman-work-pool","-t","cloud-run"

deploy_flows_on_work_pool: push_prefect_worker deploy_prefect_worker
	prefect deploy

setup_prefect_variables:
	prefect variable set gcp-project ${GCP_PROJECT}
	prefect variable set bq-dataset ${BQ_DATASET}

	# Docker et images
	prefect variable set docker-registry ${DOCKER_REGISTRY}
	prefect variable set metabase-image ${METABASE_IMAGE}

	# API et infrastructure
	prefect variable set prefect-api-url ${PREFECT_API_URL}

	# URLs externes des données
	prefect variable set debat-url ${DEBAT_URL}
	prefect variable set deputes-url ${DEPUTES_URL}
	prefect variable set scrutins-url ${SCRUTINS_URL}
	prefect variable set dossiers-legislatifs-url ${DOSSIERS_LEGISLATIFS_URL}
	prefect variable set amendements-url ${AMENDEMENTS_URL}
	prefect variable set questions-ecrites-url ${QUESTIONS_ECRITES_URL}