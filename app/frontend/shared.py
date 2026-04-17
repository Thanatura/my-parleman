from __future__ import annotations

import os
from typing import TypeAlias

import pandas as pd
import requests


DEFAULT_API_URL = os.getenv("PARLEMAN_API_URL", "http://127.0.0.1:8000")
JsonObject: TypeAlias = dict[str, object]


def fetch_json(api_base_url: str, path: str) -> JsonObject:
    response = requests.get(f"{api_base_url.rstrip('/')}{path}", timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("API response is not a JSON object")

    result: JsonObject = {}
    for key, value in payload.items():
        result[str(key)] = value
    return result


def load_marts(api_base_url: str) -> list[JsonObject]:
    payload = fetch_json(api_base_url, "/marts")
    raw_marts = payload.get("marts", [])
    if not isinstance(raw_marts, list):
        return []

    marts: list[JsonObject] = []
    for mart in raw_marts:
        if isinstance(mart, dict):
            normalized: JsonObject = {}
            for key, value in mart.items():
                normalized[str(key)] = value
            marts.append(normalized)
    return marts


def load_mart_frame(
    api_base_url: str, table_name: str, limit: int
) -> tuple[JsonObject, pd.DataFrame]:
    payload = fetch_json(api_base_url, f"/marts/{table_name}?limit={limit}")
    raw_rows = payload.get("rows", [])
    if isinstance(raw_rows, list):
        frame = pd.DataFrame(raw_rows)
    else:
        frame = pd.DataFrame()
    return payload, frame


def load_group_lookup(api_base_url: str) -> pd.DataFrame:
    payload = fetch_json(api_base_url, "/groups")
    raw_groups = payload.get("groups", [])
    if isinstance(raw_groups, list):
        return pd.DataFrame(raw_groups)
    return pd.DataFrame()


def summarize_columns(frame: pd.DataFrame) -> tuple[list[str], list[str]]:
    numeric_columns = frame.select_dtypes(include="number").columns.tolist()
    categorical_columns = [
        column
        for column in frame.columns
        if column not in numeric_columns and frame[column].nunique(dropna=True) <= 50
    ]
    return numeric_columns, categorical_columns
