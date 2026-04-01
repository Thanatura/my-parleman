from dataclasses import dataclass
import json
import os
from typing import Any


@dataclass(frozen=True)
class ProjectConfig:
    debat_url: str
    gcp_project: str
    bq_dataset: str
    gcs_load_bucket: str
    service_account_info: dict[str, Any]


def _get_service_account_info() -> dict[str, Any]:
    parsed_obj: object = json.loads(os.environ["SERVICE_ACCOUNT_INFO"])
    if not isinstance(parsed_obj, dict):
        raise ValueError("SERVICE_ACCOUNT_INFO must decode to a JSON object")
    return {str(key): value for key, value in parsed_obj.items()}


def get_config() -> ProjectConfig:
    try:
        config = ProjectConfig(
            debat_url=os.environ["DEBAT_URL"],
            gcp_project=os.environ["GCP_PROJECT"],
            bq_dataset=os.environ["BQ_DATASET"],
            gcs_load_bucket=os.environ["GCS_LOAD_BUCKET"],
            service_account_info=_get_service_account_info(),
        )
    except KeyError as e:
        missing_key = e.args[0]
        raise ValueError(f"{missing_key} environment variable must be set") from e
    return config
