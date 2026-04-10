from dataclasses import dataclass
import json
import os
from typing import Any


@dataclass(frozen=True)
class ProjectConfig:
    debat_url: str
    deputes_url: str
    scrutins_url: str
    questions_ecrites_url: str
    dossiers_legislatifs_url: str
    amendements_url: str
    gcp_project: str
    bq_dataset: str
    service_account_info: dict[str, Any]


def _get_service_account_info() -> dict[str, Any]:
    raw_value = os.environ["SERVICE_ACCOUNT_INFO"]
    try:
        parsed_obj: object = json.loads(raw_value)
    except json.JSONDecodeError as e:
        raise ValueError(
            "SERVICE_ACCOUNT_INFO must be valid JSON that decodes to a JSON object"
        ) from e
    if not isinstance(parsed_obj, dict):
        raise ValueError("SERVICE_ACCOUNT_INFO must decode to a JSON object")
    return {str(key): value for key, value in parsed_obj.items()}


def get_config() -> ProjectConfig:
    try:
        config = ProjectConfig(
            debat_url=os.environ["DEBAT_URL"],
            gcp_project=os.environ["GCP_PROJECT"],
            bq_dataset=os.environ["BQ_DATASET"],
            deputes_url=os.environ["DEPUTES_URL"],
            scrutins_url=os.environ["SCRUTINS_URL"],
            questions_ecrites_url=os.environ["QUESTIONS_ECRITES_URL"],
            dossiers_legislatifs_url=os.environ["DOSSIERS_LEGISLATIFS_URL"],
            amendements_url=os.environ["AMENDEMENTS_URL"],
            service_account_info=_get_service_account_info(),
        )
    except KeyError as e:
        missing_key = e.args[0]
        raise ValueError(f"{missing_key} environment variable must be set") from e
    return config
