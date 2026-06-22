FROM python:3.13-slim

# Install git (required for prefect git_clone)
RUN apt-get update && apt-get install -y --no-install-recommends git

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY ./ingest/pyproject.toml ./ingest/pyproject.toml
COPY ./ingest/uv.lock ./ingest/uv.lock
COPY ./ingest/flows ./ingest/flows
COPY ./ingest/lib ./ingest/lib
COPY ./dbt_parlemAn ./dbt_parlemAn
COPY ./infra/prefect/scripts ./infra/prefect/scripts

RUN uv sync --project /app/ingest --no-dev --no-cache --no-editable --frozen

# Install dbt in the project virtualenv so Prefect tasks can resolve `dbt`
RUN uv pip install --python /app/ingest/.venv/bin/python --no-cache dbt-bigquery

# Ensure the virtual environment's bin directory is in the PATH
ENV PATH="/app/ingest/.venv/bin:$PATH"

# 10/10
# 5 niv 1 (bénédiction, soin, blessure, eclair traçant, mot de guérison)
# 4 niv 2 (prière de guérison, apaisement des émotions, aide, immobilisation de personne)
# 1 niv 3 (esprits gardiens)