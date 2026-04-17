FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace:/workspace/app

COPY app/pyproject.toml /workspace/app/pyproject.toml
COPY app/__init__.py /workspace/app/__init__.py
COPY app/README.md /workspace/app/README.md
COPY app/uv.lock /workspace/app/uv.lock

RUN uv sync --project /workspace/app --no-dev --frozen

COPY app/backend /workspace/app/backend

EXPOSE 8000

CMD ["/workspace/app/.venv/bin/uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
