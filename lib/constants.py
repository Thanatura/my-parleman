"""Project-wide settings loaded from config/settings.yaml."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_DATA_URL = (
    "https://data.assemblee-nationale.fr/static/openData/repository/17/amo/"
    "deputes_actifs_mandats_actifs_organes/"
    "AMO10_deputes_actifs_mandats_actifs_organes.json.zip"
)
_DEFAULT_PROJECT = "parleman-491810"
_DEFAULT_DATASET = "ParlemAN_tests"


@dataclass(frozen=True, slots=True)
class Settings:
    data_url: str
    gcp_project: str
    bq_dataset: str


def _settings_file() -> Path:
    return Path(__file__).resolve().parents[1] / "config" / "settings.yaml"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    config_path = _settings_file()
    if not config_path.exists():
        return Settings(_DEFAULT_DATA_URL, _DEFAULT_PROJECT, _DEFAULT_DATASET)

    content = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    pipeline = content.get("pipeline", {}) if isinstance(content, dict) else {}
    gcp = content.get("gcp", {}) if isinstance(content, dict) else {}

    data_url = _as_str(pipeline.get("data_url"), _DEFAULT_DATA_URL)
    gcp_project = _as_str(gcp.get("project"), _DEFAULT_PROJECT)
    bq_dataset = _as_str(gcp.get("bq_dataset"), _DEFAULT_DATASET)

    return Settings(data_url=data_url, gcp_project=gcp_project, bq_dataset=bq_dataset)


def _as_str(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


_SETTINGS = get_settings()
DATA_URL = _SETTINGS.data_url
GCP_PROJECT = _SETTINGS.gcp_project
BQ_DATASET = _SETTINGS.bq_dataset
