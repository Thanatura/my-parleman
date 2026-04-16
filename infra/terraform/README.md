# Terraform (GCP)

This directory contains the main infrastructure stack for ParlemAN.

## What This Stack Provisions

- required GCP services (BigQuery, IAM, Cloud Run, etc.),
- BigQuery dataset,
- service account for BigQuery loading (`parleman-bq-runner` by default),
- service account for Cloud Run worker (`parleman-prefect-worker` by default),
- IAM bindings for runner and worker,
- Cloud Run Prefect worker service,
- Cloud Run Prefect server service.

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