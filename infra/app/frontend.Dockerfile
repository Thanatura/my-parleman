FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace:/workspace/app \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

COPY app/pyproject.toml /workspace/app/pyproject.toml
COPY app/__init__.py /workspace/app/__init__.py
COPY app/README.md /workspace/app/README.md
COPY app/uv.lock /workspace/app/uv.lock

RUN uv sync --project /workspace/app --no-dev --frozen

COPY app/frontend /workspace/app/frontend

EXPOSE 8501

CMD ["/workspace/app/.venv/bin/streamlit", "run", "app/frontend/App.py"]
