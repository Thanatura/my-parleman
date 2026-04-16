# ParlemAN

Data pipeline for the French National Assembly datasets:
- extract and parse raw open data,
- load curated tables into BigQuery,
- run dbt transformations,
- orchestrate everything with Prefect.

## Repository Overview

```text
config/                  # Config templates (Metabase, settings)
dbt_parlemAn/            # dbt project (staging/intermediate/marts)
flows/                   # Prefect flows (ingestion + dbt build)
infra/                   # Local infra (docker-compose) and Terraform
lib/                     # Parsing + BigQuery loading logic
tests/                   # Unit tests
.env.example             # Required environment variables template
prefect.yaml             # Prefect deployments configuration
```

## Prerequisites

- Python 3.13
- uv
- Docker (for local Metabase and image builds)
- gcloud CLI (for GCP deployments)
- Terraform >= 1.8 (for infra provisioning)

## Local Setup

Install dependencies:

```bash
uv sync
```

Optional quality tooling:

```bash
uv run pre-commit install
```

Create your local environment file:

```bash
cp .env.example .env
```

`SERVICE_ACCOUNT_INFO` must contain a JSON object (single-line JSON) for a GCP service account key.

Example:

```bash
export SERVICE_ACCOUNT_INFO="$(jq -c . /path/to/service-account.json)"
```

## Environment Variables

Main variables used by flows and deployments:

- `SERVICE_ACCOUNT_INFO`
- `GCP_PROJECT`
- `BQ_DATASET`
- `PREFECT_API_URL`
- `DOCKER_REGISTRY`
- `DEBAT_URL`
- `DEPUTES_URL`
- `SCRUTINS_URL`
- `QUESTIONS_ECRITES_URL`
- `DOSSIERS_LEGISLATIFS_URL`
- `AMENDEMENTS_URL`

Additional helper variables in `.env.example`:

- `SA_WORKER_NAME`
- `SA_RUNNER_NAME`
- `TF_VAR_project_id`
- `TF_VAR_bq_dataset_id`

## Run Flows Locally

You need to run a Prefect server locally or have access to a remote one, and set `PREFECT_API_URL` accordingly

```bash
uv run prefect server start
```

Run one ingestion flow directly:

```bash
uv run python -m flows.upload_deputes_bq
```

Other entrypoints:

- `flows.upload_debats_bq`
- `flows.upload_scrutins_bq`
- `flows.upload_dossiers_legislatifs_bq`
- `flows.upload_amendements_bq`
- `flows.upload_questions_ecrites_bq`
- `flows.run_dbt_build`

## dbt

`flows/run_dbt_build.py` runs `dbt build` against `dbt_parlemAn/` using a generated temporary `profiles.yml` from runtime env vars.

If you want to run dbt manually:

```bash
uv run pip install dbt-bigquery
cd dbt_parlemAn
dbt build
```

## Prefect Deployments

Deployments are defined in `prefect.yaml` and target the `parleman-work-pool` work pool.

Before deploying:

1. Ensure required Prefect variables exist (from your shell env):

```bash
make setup_prefect_variables
```

2. Create/update Prefect secret block `gcp-service-account-info`.

3. Build and push runtime images:

```bash
make push_prefect_worker
make push_prefect_server
```

Deploy all flows:

```bash
prefect deploy
```

## Terraform Infrastructure

Terraform files are in `infra/terraform`.

The Terraform stack provisions:
- BigQuery dataset,
- service accounts and IAM bindings,
- Cloud Run Prefect worker,
- Cloud Run Prefect server,
- required APIs.

Read `infra/terraform/README.md` for bootstrap + apply steps.

## Metabase (Local)

Prepare config:

```bash
cp config/metabase.env.example config/metabase.env
```

Start:

```bash
cd infra
docker compose up -d
```

Access:
- Metabase: http://localhost:3000
- Adminer: http://localhost:8080

Stop:

```bash
cd infra
docker compose down
```

## Tests

```bash
uv run pytest
```

## Security Notes

- Do not commit real `.env` files.
- Do not commit service account keys.
- Keep IAM permissions minimal.
