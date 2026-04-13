FROM python:3.13-slim

# Install git (required for prefect git_clone)
RUN apt-get update && apt-get install -y --no-install-recommends git

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY ./README.md ./README.md
COPY ./pyproject.toml ./pyproject.toml
COPY ./uv.lock ./uv.lock
COPY ./flows ./flows
COPY ./lib ./lib
COPY ./dbt_parlemAn ./dbt_parlemAn

RUN uv sync --no-dev --no-cache --no-editable --frozen

# Install dbtf CLI
RUN curl -fsSL https://public.cdn.getdbt.com/fs/install/install.sh | sh -s -- --update
RUN exec $SHELL

# Ensure the virtual environment's bin directory is in the PATH
ENV PATH="/app/.venv/bin:$PATH" 