# ParlemAN

Pipeline de données pour les jeux open data de l'Assemblée nationale :
- extraction et parsing,
- chargement dans BigQuery,
- transformations dbt,
- orchestration avec Prefect.

## Prérequis

- Python 3.13
- uv
- Docker
- gcloud CLI
- Terraform >= 1.8
- Prefect CLI (installé via les dépendances Python du projet)
- pre-commit (installé via le projet tooling racine)

Préparer votre contexte GCP :

```bash
gcloud auth login
gcloud config set project <VOTRE_PROJECT_ID>
gcloud auth application-default login
```

Important :
- le projet GCP doit avoir la facturation active,
- vous devez avoir les droits IAM suffisants pour créer IAM/Cloud Run/BigQuery/Artifact Registry.

## Variables à renseigner

Copier le template :

```bash
cp .env.example .env
```

Variables minimales à renseigner dans `.env` :

- `GCP_PROJECT`
- `BQ_DATASET`
- `PREFECT_DB_PASSWORD`
- `PREFECT_API_AUTH_STRING`
- `DEBAT_URL`
- `DEPUTES_URL`
- `SCRUTINS_URL`
- `QUESTIONS_ECRITES_URL`
- `DOSSIERS_LEGISLATIFS_URL`
- `AMENDEMENTS_URL`

Notes:
- `TF_VAR_project_id` et `TF_VAR_bq_dataset_id` peuvent référencer `GCP_PROJECT` et `BQ_DATASET`.
- `TF_VAR_prefect_db_password` doit être aligné avec `PREFECT_DB_PASSWORD`.
- `TF_VAR_prefect_server_api_auth_string` doit être aligné avec `PREFECT_API_AUTH_STRING`.
- `SERVICE_ACCOUNT_INFO` est nécessaire pour des runs locaux de flows, mais pas pour le chemin Cloud Run + Prefect (le secret Prefect est alimenté via Terraform output et `make setup_prefect_variables`).

Exemple `.env` minimal pour la partie sécurité Prefect :

```bash
PREFECT_DB_PASSWORD="<mot_de_passe_fort>"
PREFECT_API_AUTH_STRING="admin:${PREFECT_DB_PASSWORD}"
TF_VAR_prefect_db_password="${PREFECT_DB_PASSWORD}"
TF_VAR_prefect_server_api_auth_string="${PREFECT_API_AUTH_STRING}"
```

## Structure du repo

```text
config/                  # Config templates (settings)
dbt_parlemAn/            # Projet dbt
ingest/                  # Code ingestion (flows Prefect + parsing + chargement BQ)
infra/                   # Docker compose local + Terraform
app/                     # API FastAPI + UI Streamlit
pyproject.toml           # Projet tooling racine (pre-commit)
.env.example             # Variables d'environnement
prefect.yaml             # Deployments Prefect
```

## Déploiement complet sur un projet GCP

### 1) Bootstrap Terraform (state bucket + Artifact Registry)

```bash
terraform -chdir=infra/terraform/bootstrap init
terraform -chdir=infra/terraform/bootstrap apply
```

### 2) Build et push des images runtime

Depuis la racine :

```bash
make push_all_images
```

Cette commande pousse les 4 images nécessaires :
- `prefect-worker`
- `prefect-server`
- `parleman-backend`
- `parleman-frontend`

Alternative (si besoin) :

```bash
make push_prefect_worker
make push_prefect_server
make push_backend
make push_frontend
```

### 3) Provisionnement stack principale

```bash
terraform -chdir=infra/terraform init 
terraform -chdir=infra/terraform apply
```

Cette stack provisionne notamment :
- BigQuery dataset,
- service accounts + IAM,
- VM PostgreSQL pour metadata Prefect,
- Cloud Run Prefect server,
- Cloud Run Prefect worker.

#### Changements de sécurité récents

- le service `prefect_server` est public par défaut mais protégé par une clé (`prefect_server_allow_unauthenticated = true`, `prefect_server_api_auth_string`),
- le serveur Prefect utilise un service account dédié (`server_service_account_id`),
- la VM PostgreSQL n'ouvre pas SSH par défaut (`vm_db_enable_ssh = false`),
- le firewall PostgreSQL peut rester ouvert par défaut ou être restreint via `vm_db_postgres_source_ranges`.

Option d'exposition publique avec clé :

- définir `prefect_server_allow_unauthenticated = true`,
- définir `prefect_server_api_auth_string = "<username>:<password>"`,
- fournir `PREFECT_API_AUTH_STRING` aux clients et au worker.

Pour vérifier les ranges effectivement autorisés côté DB :

```bash
terraform -chdir=infra/terraform output vm_db_postgres_source_ranges
```

#### Accès au serveur Prefect

Le service Cloud Run `prefect-server` est public, mais protégé par `PREFECT_SERVER_API_AUTH_STRING`.

### 4) Initialisation des variables et secrets Prefect

Depuis la racine:

```bash
make setup_prefect_variables
```

Important:
- `make setup_prefect_variables` doit être rejoué après recréation/migration du serveur Prefect.
- Si ce step est omis, `prefect deploy --all` peut échouer avec `Block document not found` sur `prefect.blocks.secret.gcp-service-account-info`.

### 5) Déployer les flows

```bash
make deploy_all_flows
```

Commande équivalente :

```bash
uv run --project ingest prefect deploy --all
```


## Pour vérifier que tout fonctionne

1. Dans Prefect UI, les deployments sont visibles (deputes, debats, scrutins, dossiers_legislatifs, amendements, questions_ecrites, dbt_build).
2. Un run manuel d'au moins un flow d'ingestion se termine en succès.
3. Le run `dbt_build` se termine en succès.
4. Les tables cibles existent dans le dataset BigQuery configuré.

## Exécution locale

Installer les dépendances :

```bash
uv sync --project . --dev
uv sync --project app
uv sync --project ingest
```

Installer et lancer pre-commit (depuis la racine) :

```bash
uv run --project . pre-commit install
uv run --project . pre-commit run --all-files
```

Lancer les tests:

```bash
uv run --project ingest python -m pytest ingest/tests
```

Lancer un flow localement:

```bash
uv run --project ingest python -m ingest.flows.upload_deputes_bq
```

Lancer le flow dbt localement:

```bash
uv pip install dbt-bigquery
uv run --project ingest python -m ingest.flows.run_dbt_build
```

## Commandes make disponibles

- `make push_prefect_worker`
- `make push_prefect_server`
- `make push_backend`
- `make push_frontend`
- `make push_all_images`
- `make setup_prefect_variables`
- `make deploy_all_flows`
- `make setup_precommit` (installe pre-commit depuis le projet racine)
- `make run_precommit` (lance tous les hooks pre-commit)
- `make run_all_flows` (déclenche tous les flows d'ingestion hors `dbt_build` en parallèle)
- `make run_marts_api` (API FastAPI pour exposer les `mart_*` BigQuery)
- `make run_marts_ui` (interface Streamlit connectée à l'API)

## App marts BigQuery (FastAPI + Streamlit)

L'app est dans le dossier `app/` :

- backend FastAPI : `app/backend/main.py`
- frontend Streamlit : `app/frontend/App.py`

Lancement rapide :

```bash
make run_marts_api
```

Dans un second terminal :

```bash
make run_marts_ui
```
