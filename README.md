# ParlemAN

# Setup du projet

1. Installer [uv](https://docs.astral.sh/uv/getting-started/installation/)

# Configurer le Service Account GCP

Le flow Prefect et Metabase utilisent BigQuery. Il faut donc un service account avec une cle JSON.

1. Definir les variables de base:

```bash
export GCP_PROJECT_ID="parleman-491810"
export SA_NAME="parleman-bq-runner"
```

2. Creer le service account si ce nest pas encore fait:

```bash
gcloud iam service-accounts create "$SA_NAME" \
	--project "$GCP_PROJECT_ID" \
	--display-name "ParlemAN BigQuery Runner"
```

3. Donner les roles minimaux (projet):

```bash
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
	--member "serviceAccount:${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
	--role "roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
	--member "serviceAccount:${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
	--role "roles/bigquery.dataEditor"
```

4. Generer la cle JSON locale:

```bash
mkdir -p .secrets
gcloud iam service-accounts keys create .secrets/parleman-sa.json \
	--iam-account "${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
	--project "$GCP_PROJECT_ID"
```

5. Exporter la variable d'environnement pour le flow:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/.secrets/parleman-sa.json"
```

6. Lancer le flow:

```bash
uv run python -m flows.upload_deputes_bg
```

7. Dans Metabase (BigQuery), importer ce meme fichier JSON de service account.

Note securite:
- Ne jamais commiter `.secrets/parleman-sa.json`.
- Faire une rotation periodique des cles.

# Installer Metabase

Prerequis:
- Docker + Docker Compose installes

1. Creer le fichier d'environnement Metabase:

```bash
cp config/metabase.env.example config/metabase.env
```

2. Editer `config/metabase.env` et remplacer `MB_ENCRYPTION_SECRET_KEY` par une valeur forte.

3. Demarrer Metabase et sa base interne PostgreSQL:

```bash
cd infra
docker compose up -d
```

4. Ouvrir Metabase:

http://localhost:3000

Adminer (inspection de la base PostgreSQL interne de Metabase):

http://localhost:8080

Parametres de connexion Adminer:
- System: PostgreSQL
- Server: metabase-db
- Username: metabase
- Password: metabase
- Database: metabase

5. Configurer la connexion BigQuery dans Metabase:
- Admin settings > Databases > Add database
- Type: BigQuery
- Project ID: `parleman-491810`
- Dataset: `ParlemAN_tests`
- Authentication: Service account JSON

6. Arreter Metabase:

```bash
cd infra
docker compose down
```

# Structure du projet


│
├── infra/                      # Terraform (infrastructure)
│   ├── main.tf
│   └── variables.tf
│  
├── flows/                      # Prefect flows
│   ├── api_to_gcs_flow.py
│   └── tasks/
│       ├── fetch_api.py
│       └── upload_gcs.py
│
├── config/
│   ├── settings.yaml
│   └── secrets.env
│
├── scripts/                    # scripts utilitaires
│   └── run_flow.py
│
├── lib/                    # librairies utilitaires
│   └── parse_xml.py
│
├── requirements.txt
├── .env
├── .gitignore
└── README.md
