from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    gcp_project: str
    bq_dataset: str
    service_account_info: str | None

    @classmethod
    def from_env(cls) -> "AppSettings":
        gcp_project = os.environ.get("GCP_PROJECT", "").strip()
        bq_dataset = os.environ.get("BQ_DATASET", "").strip()
        service_account_info = (
            os.environ.get("SERVICE_ACCOUNT_INFO", "").strip() or None
        )

        if not gcp_project:
            raise ValueError("GCP_PROJECT environment variable must be set")
        if not bq_dataset:
            raise ValueError("BQ_DATASET environment variable must be set")

        return cls(
            gcp_project=gcp_project,
            bq_dataset=bq_dataset,
            service_account_info=service_account_info,
        )
