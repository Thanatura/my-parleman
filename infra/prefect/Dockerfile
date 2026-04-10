FROM python:3.13-slim

# Install git (required for prefect git_clone)
RUN apt-get update && apt-get install -y --no-install-recommends git

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY ./README.md ./README.md
COPY ./pyproject.toml ./pyproject.toml
COPY ./flows ./flows
COPY ./lib ./lib

RUN uv sync --no-dev --no-cache --no-editable

# Ensure the virtual environment's bin directory is in the PATH
ENV PATH="/app/.venv/bin:$PATH" 