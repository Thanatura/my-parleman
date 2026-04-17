from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status

from .bigquery_service import BigQueryMartService
from .schemas import (
    GroupListResponse,
    GroupTable,
    MartListResponse,
    MartRowsResponse,
    MartTable,
)
from .settings import AppSettings


app = FastAPI(title="ParlemAN Mart API", version="0.1.0")


@lru_cache(maxsize=1)
def get_service() -> BigQueryMartService:
    settings = AppSettings.from_env()
    return BigQueryMartService(settings=settings)


def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    expected_key = get_service().settings.api_key
    if x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/marts", response_model=MartListResponse, dependencies=[Depends(verify_api_key)]
)
def list_marts() -> MartListResponse:
    service = get_service()
    marts = [MartTable(**row) for row in service.list_marts()]
    return MartListResponse(
        project=service.settings.gcp_project,
        dataset=service.settings.bq_dataset,
        marts=marts,
    )


@app.get(
    "/marts/{table_name}",
    response_model=MartRowsResponse,
    dependencies=[Depends(verify_api_key)],
)
def get_mart_rows(
    table_name: str,
    limit: int = Query(default=100, ge=1, le=1000),
) -> MartRowsResponse:
    service = get_service()
    try:
        rows = service.read_mart_rows(table_name=table_name, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return MartRowsResponse(
        project=service.settings.gcp_project,
        dataset=service.settings.bq_dataset,
        table_name=table_name,
        limit=limit,
        row_count=len(rows),
        rows=rows,
    )


@app.get(
    "/groups", response_model=GroupListResponse, dependencies=[Depends(verify_api_key)]
)
def list_groups() -> GroupListResponse:
    service = get_service()
    groups = [GroupTable(**row) for row in service.read_group_lookup()]
    return GroupListResponse(
        project=service.settings.gcp_project,
        dataset=service.settings.bq_dataset,
        groups=groups,
    )
