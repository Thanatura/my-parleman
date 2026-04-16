# ParlemAN

Pipeline de données pour les jeux open data de l'Assemblée nationale :
- extraction et parsing,
- chargement dans BigQuery,
- transformations dbt,
- orchestration avec Prefect.

Ce README est orienté examinateur : il décrit le chemin minimal pour lancer le projet sur votre propre projet GCP.

## Prérequis

- Python 3.13
- uv
- Docker
- gcloud CLI
- Terraform >= 1.8
- Prefect CLI (installé via les dépendances Python du projet)

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
- `SERVICE_ACCOUNT_INFO` est nécessaire pour des runs locaux de flows, mais pas pour le chemin Cloud Run + Prefect (le secret Prefect est alimenté via Terraform output et `make setup_prefect_secret_blocks`).

Exemple `.env` minimal pour la partie sécurité Prefect :

```bash
PREFECT_DB_PASSWORD="<mot_de_passe_fort>"
PREFECT_API_AUTH_STRING="admin:${PREFECT_DB_PASSWORD}"
TF_VAR_prefect_db_password="${PREFECT_DB_PASSWORD}"
TF_VAR_prefect_server_api_auth_string="${PREFECT_API_AUTH_STRING}"
```

## Structure du repo

```text
config/                  # Config templates (Metabase, settings)
dbt_parlemAn/            # Projet dbt
flows/                   # Flows Prefect (ingestion + dbt)
infra/                   # Docker compose local + Terraform
lib/                     # Parsing + chargement BigQuery
tests/                   # Tests unitaires
.env.example             # Variables d'environnement
prefect.yaml             # Deployments Prefect
```

## Déploiement complet sur un projet gcp

### 1) Bootstrap Terraform (state bucket + Artifact Registry)

```bash
terraform -chdir=infra/terraform/bootstrap init
terraform -chdir=infra/terraform/bootstrap apply
```

### 2) Build et push des images runtime

Depuis la racine :

```bash
make push_prefect_worker
make push_prefect_server
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

#### changements de sécurité récents

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

#### Accès à prefect server (privé)

Le serveur étant public mais protégé, l'accès recommandé se fait directement ou via proxy authentifié :

```bash
gcloud run services proxy prefect-server --region europe-west1 --port 8088
```

Puis ouvrir :

```text
http://127.0.0.1:8088/dashboard
```

Vérifier l'API proxifiée :

```bash
curl -sS http://127.0.0.1:8088/api/health
```

Mettre à jour PREFECT_API_URL :

```bash
export PREFECT_API_URL="http://127.0.0.1:8088/api"
echo "PREFECT_API_URL=${PREFECT_API_URL}" >> .env
```

Si le serveur est en mode public + clé, exporter aussi :

```bash
export PREFECT_API_AUTH_STRING="<username>:<password>"
echo "PREFECT_API_AUTH_STRING=${PREFECT_API_AUTH_STRING}" >> .env
```

### 4) Initialisation des variables et secrets Prefect

Depuis la racine:

```bash
make setup_prefect_variables
make setup_prefect_secret_blocks
```

Important:
- `make setup_prefect_secret_blocks` doit être rejoué après recréation/migration du serveur Prefect.
- Si ce step est omis, `prefect deploy --all` peut échouer avec `Block document not found` sur `prefect.blocks.secret.gcp-service-account-info`.

### 5) Déployer les flows

```bash
prefect deploy --all
```


## Pour vérifier que tout fonctionne

1. Dans Prefect UI, les deployments sont visibles (deputes, debats, scrutins, dossiers_legislatifs, amendements, questions_ecrites, dbt_build).
2. Un run manuel d'au moins un flow d'ingestion se termine en succès.
3. Le run `dbt_build` se termine en succès.
4. Les tables cibles existent dans le dataset BigQuery configuré.

## Exécution locale

Installer les dépendances :

```bash
uv sync
```

Lancer les tests:

```bash
uv run pytest
```

Lancer un flow localement:

```bash
uv run python -m flows.upload_deputes_bq
```

Lancer le flow dbt localement:

```bash
uv pip install dbt-bigquery
uv run python -m flows.run_dbt_build
```

## commandes make disponibles

- `make push_prefect_worker`
- `make push_prefect_server`
- `make setup_prefect_variables`
- `make setup_prefect_secret_blocks`
- `make run_all_flows` (déclenche tous les flows d'ingestion hors `dbt_build` en parallèle)
- `make run_all_flows_serial` (idem, en séquentiel)
- `make push_metabase`

## metabase local (optionnel)

```bash
cp config/metabase.env.example config/metabase.env
cd infra
docker compose up -d
```

Accès :
- Metabase: http://localhost:3000
- Adminer: http://localhost:8080

Arrêt :

```bash
cd infra
docker compose down
```

## sécurité

- Ne pas committer de `.env` réel.
- Ne pas committer de clés de service account.
- Limiter les permissions IAM au strict nécessaire.
- Si `prefect_server` est exposé publiquement, exiger `PREFECT_SERVER_API_AUTH_STRING` côté serveur et `PREFECT_API_AUTH_STRING` côté clients/workers.
