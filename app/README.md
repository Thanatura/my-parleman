# App marts BigQuery (FastAPI + Streamlit)

Cette application expose les marts dbt depuis BigQuery via une API FastAPI, puis les visualise avec Streamlit.

## Structure

- API: `app/backend/main.py`
- UI Streamlit: `app/frontend/App.py`
- Pages Streamlit:
	- `app/frontend/pages/0_Exploration.py`
	- `app/frontend/pages/1_Visualisations.py`

## Variables d'environnement requises

- `GCP_PROJECT`
- `BQ_DATASET`
- optionnel: `SERVICE_ACCOUNT_INFO` (contenu JSON d'un compte de service)

Si `SERVICE_ACCOUNT_INFO` n'est pas fourni, l'application utilise les Application Default Credentials.

## Installation (pyproject dédié)

Depuis la racine du repo:

```bash
uv sync --project app --dev
```

## Lancement recommandé (Makefile)

Depuis la racine du repo:

```bash
make run_marts_api
```

Dans un second terminal:

```bash
make run_marts_ui
```

Le Makefile configure automatiquement le contexte d'import Python pour supporter les imports `from app...` et `from frontend...`.

## Lancement manuel (sans Makefile)

Depuis la racine du repo:

```bash
set -a; source .env; set +a
PYTHONPATH="$(pwd):$(pwd)/app" uv run uvicorn app.backend.main:app --reload --host 0.0.0.0 --port 8000
```

Dans un second terminal:

```bash
set -a; source .env; set +a
PYTHONPATH="$(pwd):$(pwd)/app" PARLEMAN_API_URL="${PARLEMAN_API_URL:-http://127.0.0.1:8000}" uv run streamlit run app/frontend/App.py
```

## Endpoints API

- `GET /health`
- `GET /marts`
- `GET /marts/{table_name}?limit=100` (limite max: 1000)

## Dépannage rapide

Si vous voyez une erreur de type `ModuleNotFoundError` sur `app` ou `frontend`:

1. Lancez les services via `make run_marts_api` et `make run_marts_ui`.
2. Vérifiez que vous exécutez depuis la racine du repo.
3. Vérifiez que `.env` existe et est chargé.
