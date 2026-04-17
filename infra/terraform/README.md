# Terraform (GCP)

This directory contains the main infrastructure stack for ParlemAN.

## What This Stack Provisions

- required GCP services (BigQuery, IAM, Cloud Run, etc.),
- BigQuery dataset,
- service account for BigQuery loading (`parleman-bq-runner` by default),
- service account for Cloud Run worker (`parleman-prefect-worker` by default),
- IAM bindings for runner and worker,
- PostgreSQL VM module for Prefect metadata database (`vm_db`),
- Cloud Run Prefect worker service,
- Cloud Run Prefect server service.

Security defaults in this stack:

- Prefect server is public by default but protected by an auth string (`prefect_server_allow_unauthenticated = true`, `prefect_server_api_auth_string`),
- Cloud Run Prefect server runs with a dedicated service account,
- SSH firewall rule on DB VM is disabled by default (`vm_db_enable_ssh = false`),
- PostgreSQL firewall defaults to an open allow-list unless you tighten `vm_db_postgres_source_ranges`.

To expose Prefect server publicly while keeping API access protected, set:

- `prefect_server_allow_unauthenticated = true`
- `prefect_server_api_auth_string = "<username>:<password>"`

Then configure clients/workers with `PREFECT_API_AUTH_STRING`.

Image references are built from variables:

- worker image: `<region>-docker.pkg.dev/<project>/<repo>/<worker_image>:<tag>`
- server image: `<region>-docker.pkg.dev/<project>/<repo>/<server_image>:<tag>`

By default, both images are expected in Artifact Registry repository `parleman-artifact-repo`.

## Bootstrap Stack (Required First)

The bootstrap stack in `infra/terraform/bootstrap` creates:

- Terraform state bucket (`my-parleman-tf-state` by default),
- Artifact Registry repository (`parleman-artifact-repo` by default).

Run bootstrap first:

```bash
cd infra/terraform/bootstrap
terraform init
terraform apply
```

Avoid destroying bootstrap unless you intentionally want to remove state storage and Artifact Registry.

## Build and Push Images

From repository root:

```bash
make push_prefect_worker
make push_prefect_server
```

## Build and Push Backend / Frontend Images

The backend (FastAPI) and frontend (Streamlit) services are deployed as Cloud Run services in the main stack.

### Build Backend and Frontend Images

From repository root:

```bash
# Build backend image
docker build --platform linux/amd64 -t ${REGION}-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/parleman-backend . -f infra/backend.Dockerfile

# Push backend image
docker push ${REGION}-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/parleman-backend

# Build frontend image
docker build --platform linux/amd64 -t ${REGION}-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/parleman-frontend . -f infra/frontend.Dockerfile

# Push frontend image
docker push ${REGION}-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/parleman-frontend
```

Or add these commands to your `Makefile` for convenience:

```makefile
build_backend:
	docker build --platform linux/amd64 -t ${REGION}-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/parleman-backend . -f infra/backend.Dockerfile

push_backend: build_backend
	docker push ${REGION}-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/parleman-backend

build_frontend:
	docker build --platform linux/amd64 -t ${REGION}-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/parleman-frontend . -f infra/frontend.Dockerfile

push_frontend: build_frontend
	docker push ${REGION}-docker.pkg.dev/${GCP_PROJECT}/${DOCKER_REGISTRY}/parleman-frontend
```

## Cloud Run Services (Backend + Frontend)

The main Terraform stack provisions two additional Cloud Run services:

- **Backend (FastAPI)**: Exposes mart data from BigQuery via REST API on port 8000
- **Frontend (Streamlit)**: Connects to backend and visualizes data on port 8501

Both services are publicly invokable and run with minimal permissions.

### Configuration

Add to `terraform.tfvars`:

```hcl
cloud_run_backend_image_name    = "parleman-backend"
cloud_run_backend_image_tag     = "latest"
cloud_run_backend_service_name  = "parleman-backend"
cloud_run_frontend_image_name   = "parleman-frontend"
cloud_run_frontend_image_tag    = "latest"
cloud_run_frontend_service_name = "parleman-frontend"
parleman_api_key                = "YOUR_SECURE_API_KEY_HERE"
```

### Environment Variables (Set at Deploy Time)

Backend receives:

- `GCP_PROJECT`: From `var.project_id`
- `BQ_DATASET`: From `var.bq_dataset_id`
- `PARLEMAN_API_KEY`: From `var.parleman_api_key`

Frontend receives:

- `PARLEMAN_API_URL`: Set to backend service URL automatically
- `PARLEMAN_API_KEY`: From `var.parleman_api_key`
- `STREAMLIT_SERVER_HEADLESS=true`, `STREAMLIT_SERVER_ADDRESS=0.0.0.0`, `STREAMLIT_SERVER_PORT=8501`

### Service Accounts

- `parleman-backend` service account:
  - `roles/bigquery.dataViewer` (read marts)
  - `roles/bigquery.jobUser` (execute queries)
  - `roles/artifactregistry.reader` (pull image)

- `parleman-frontend` service account:
  - `roles/artifactregistry.reader` (pull image)

### After Terraform Apply

Once deployed, Terraform outputs the service URLs:

```bash
terraform output backend_url
terraform output frontend_url
```

Access the frontend at the output URL. It will automatically connect to the backend.

## Configure Variables

You can use `terraform.tfvars`, `terraform.tfvars.example`, or environment variables.

Minimal env var setup:

```bash
export TF_VAR_project_id="$GCP_PROJECT"
export TF_VAR_bq_dataset_id="$BQ_DATASET"
```

Important: `prefect_server_public_url` is no longer used in this stack.

The worker `PREFECT_API_URL` is computed automatically as:

- `<prefect_server_cloud_run_uri>/api`

via Terraform local value `prefect_api_url`.

The server gets `PREFECT_API_DATABASE_CONNECTION_URL` from `module.vm_db.connection_string`.

If you want to tighten PostgreSQL access, override `vm_db_postgres_source_ranges` with the CIDRs you want to allow.

## Apply Main Stack

```bash
cd infra/terraform
terraform init -reconfigure
terraform plan
terraform apply
```

## Common Variables

Defined in `variables.tf`:

- `project_id`
- `region` (default `europe-west1`)
- `bq_dataset_id`
- `bq_location` (default `EU`)
- `artifact_registry_repository_id`
- `cloud_run_worker_image_name`
- `cloud_run_worker_image_tag`
- `cloud_run_server_image_name`
- `cloud_run_server_image_tag`
- `prefect_server_allow_unauthenticated`
- `prefect_server_api_auth_string` (sensitive)
- `server_service_account_id`
- `vm_db_zone`
- `prefect_db_user`
- `prefect_db_password` (sensitive)
- `prefect_db_name`
- `vm_db_postgres_source_ranges`
- `vm_db_enable_ssh`
- `vm_db_ssh_source_ranges`
- `cloud_run_env_vars` (extra env vars merged into worker env)

## Outputs

Main outputs from `outputs.tf`:

- `bigquery_dataset_id`
- `artifact_registry_repository`
- `cloud_run_worker_url`
- `prefect_server_url`
- `runner_service_account_email`
- `worker_service_account_email`
- `worker_image`
- `prefect_db_public_ip`
- `prefect_server_database_connection_url` (sensitive)