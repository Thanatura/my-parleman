# ParlemAN

Pipeline for fetching/parsing French National Assembly data, with BigQuery loading and Metabase visualization.

## Project Structure

```text
config/           # Configuration templates
flows/            # Prefect pipeline orchestration
infra/            # Docker Compose stack
lib/              # Core modules (parsing, loading, validation)
scripts/          # Utility scripts and SQL views
tests/            # Unit tests
.env              # Environment variables (do not commit with real values)
.env.example      # Template for .env
pyproject.toml    # Project metadata and dependencies
README.md         # This file
```

## Installation

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. *(Optional)* Install [direnv](https://direnv.net/docs/installation.html) for automatic environment loading:
   ```bash
   # macOS
   brew install direnv

   # Linux
   curl -sfL https://direnv.net/install.sh | bash
   ```
   Then allow the project directory:
   ```bash
   direnv allow
   ```
3. Sync dependencies
4. Install pre-commit hooks *(optional but recommended)*

```bash
uv sync
uv run pre-commit install
uv run pre-commit autoupdate
```

## Configuration

All configuration is centralized in `.env`. Copy from the template and customize as needed:

```bash
cp .env.example .env
```

Edit `.env` to override defaults:
- `GCP_PROJECT`: BigQuery project ID (default: parleman-491810)
- `BQ_DATASET`: BigQuery dataset name (default: ParlemAN_tests)
- `DATA_URL`: Assembly open data archive URL (defaults to latest)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to GCP service account JSON

### Environment Loading

**Python**: Configuration loads from `.env` via `python-dotenv` in runtime modules

**Shell**: If [direnv](https://direnv.net/) is installed, variables auto-load when entering the directory via `.envrc`

> Never commit `.env` or `.secrets/` to git. Use `.env.example` as a template.

## GCP Setup

1. Create service accounts:

For runner (runs flow code):
```bash
export GCP_PROJECT="parleman-491810"
export SA_RUNNER_NAME="parleman-bq-runner"

gcloud iam service-accounts create "$SA_RUNNER_NAME" \
  --project "$GCP_PROJECT" \
  --display-name "ParlemAN BigQuery Runner"
```

For worker (invokes jobs on Cloud Run):
```bash
export SA_WORKER_NAME="parleman-prefect-worker"

gcloud iam service-accounts create "$SA_WORKER_NAME" \
  --project "$GCP_PROJECT" \
  --display-name "ParlemAN Prefect Worker"
```

2. Grant minimal roles:

For runner:
```bash
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member "serviceAccount:${SA_RUNNER_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com" \
  --role "roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member "serviceAccount:${SA_RUNNER_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/bigquery.dataEditor"
```

For worker:
```bash
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member "serviceAccount:${SA_WORKER_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/run.invoker"

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member "serviceAccount:${SA_WORKER_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/artifactregistry.reader"

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member "serviceAccount:${SA_WORKER_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/iam.serviceAccountUser"
```


3. Create local key:

```bash
mkdir -p .secrets
gcloud iam service-accounts keys create .secrets/parleman-sa.json \
  --iam-account "${SA_RUNNER_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com" \
  --project "$GCP_PROJECT"
```

4. Set environment variable in `.env`:

```bash
GOOGLE_APPLICATION_CREDENTIALS=.secrets/parleman-sa.json
```

## Run Pipeline

```bash
uv run python -m flows.upload_deputes_bg
```

## Metabase (local)

Requires: Docker + Docker Compose.

1. Setup environment:

```bash
cp config/metabase.env.example config/metabase.env
```

2. Set strong encryption key in `config/metabase.env`

3. Start Metabase:

```bash
cd infra
docker compose up -d
```

Access:
- Metabase: http://localhost:3000
- Adminer (inspect internal PostgreSQL): http://localhost:8080

Adminer credentials:
- System: PostgreSQL
- Server: metabase-db
- Username: metabase
- Password: metabase
- Database: metabase

Configure BigQuery connection in Metabase:
- Admin settings > Databases > Add database
- Type: BigQuery
- Project ID: parleman-491810
- Dataset: ParlemAN_tests
- Authentication: Upload service account JSON

Stop Metabase:

```bash
cd infra
docker compose down
```

## Prefect (local)

```bash
docker run -p 4200:4200 -d --rm prefecthq/prefect:3-latest -- prefect server start --host 0.0.0.0
```

## Prefect Deployment (Cloud Run)

### Prerequisites

- GCP project configured (`parleman-491810`)
- `gcloud` CLI authenticated
- Prefect Cloud account

### 1. Setup GCP Region

```bash
gcloud config set run/region my-region
```

### 2. Create Prefect Variables

Store environment variables in Prefect:

```bash
make setup_prefect_variables
```
Store sensitive service account JSON and github token variables (names «github-token» and «gcp-service-account-info»):

```bash
prefect block create secret
```

### 3. Deploy Prefect Worker

Deploy a Prefect worker to Cloud Run:

```bash
gcloud run deploy prefect-worker \
  --image=europe-west1-docker.pkg.dev/${GCP_PROJECT}/parleman-artifact-repo/prefect-worker \
  --set-env-vars PREFECT_API_URL=${PREFECT_API_URL} \
  --service-account ${SA_WORKER_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com \
  --no-cpu-throttling \
  --min-instances 1 \
  --memory=2Gi \
  --startup-probe httpGet.port=8080,httpGet.path=/health,initialDelaySeconds=100,periodSeconds=20,timeoutSeconds=20 \
  --args "prefect","worker","start","--install-policy","never","--with-healthcheck","-p","parleman-work-pool","-t","cloud-run"
```

### 4. Deploy Flows

```bash
prefect deploy
```

This reads configuration from `prefect.yaml` and deploys flows to your work pool.


### Using the starter dbt parlemAn project

Try running the following commands:
- pip install dbt-bigquery
- dbt debug
- dbt run
- dbt test

## Security

- **Never commit real `.env` files**: Use `.env.example` as a template for team distribution
- **Never commit `.secrets/` directory**: Contains sensitive GCP service account keys
- **`.envrc` is safe to commit**: It's configuration for loading `.env`, not secrets themselves
- Rotate service account keys regularly (keep max 2 keys per service account)
- Use minimal IAM roles (`bigquery.jobUser` + `bigquery.dataEditor`) for service accounts
