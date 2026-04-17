from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MartTable(BaseModel):
    table_name: str
    table_type: str
    creation_time: datetime | None


class MartListResponse(BaseModel):
    project: str
    dataset: str
    marts: list[MartTable]


class MartRowsResponse(BaseModel):
    project: str
    dataset: str
    table_name: str
    limit: int
    row_count: int
    rows: list[dict[str, object]]


class GroupTable(BaseModel):
    groupe_uid: str
    groupe_libelle: str | None = None
    groupe_libelle_abrev: str | None = None
    gp_couleur: str | None = None


class GroupListResponse(BaseModel):
    project: str
    dataset: str
    groups: list[GroupTable]
