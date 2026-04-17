from __future__ import annotations

import json
import re
from typing import Any

from google.cloud import bigquery
from google.oauth2 import service_account

from .settings import AppSettings

_VALID_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class BigQueryMartService:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.client = self._build_client()

    def _build_client(self) -> bigquery.Client:
        if self.settings.service_account_info:
            info_obj = json.loads(self.settings.service_account_info)
            credentials = service_account.Credentials.from_service_account_info(
                info_obj
            )
            return bigquery.Client(
                project=self.settings.gcp_project, credentials=credentials
            )

        return bigquery.Client(project=self.settings.gcp_project)

    def list_marts(self) -> list[dict[str, Any]]:
        query = f"""
        SELECT
          table_name,
          table_type,
          creation_time
        FROM `{self.settings.gcp_project}.{self.settings.bq_dataset}.INFORMATION_SCHEMA.TABLES`
        WHERE STARTS_WITH(table_name, 'mart_')
        ORDER BY table_name
        """
        result = self.client.query(query).result()
        return [
            {
                "table_name": row["table_name"],
                "table_type": row["table_type"],
                "creation_time": row.get("creation_time"),
            }
            for row in result
        ]

    def read_mart_rows(self, table_name: str, limit: int = 100) -> list[dict[str, Any]]:
        self._validate_table_name(table_name)
        safe_limit = max(1, min(limit, 1000))

        query = f"""
        SELECT *
        FROM `{self.settings.gcp_project}.{self.settings.bq_dataset}.{table_name}`
        LIMIT @limit
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limit", "INT64", safe_limit)
            ]
        )
        rows = self.client.query(query, job_config=job_config).result()
        return [dict(row.items()) for row in rows]

    def read_group_lookup(self) -> list[dict[str, Any]]:
        query = f"""
        SELECT
          CAST(groupe_uid AS STRING) AS groupe_uid,
          groupe_libelle,
          groupe_libelle_abrev,
          gp_couleur
        FROM `{self.settings.gcp_project}.{self.settings.bq_dataset}.int_groupes`
        ORDER BY groupe_libelle
        """
        rows = self.client.query(query).result()
        return [dict(row.items()) for row in rows]

    def _validate_table_name(self, table_name: str) -> None:
        if not _VALID_IDENTIFIER.match(table_name):
            raise ValueError("Invalid table name")
        if not table_name.startswith("mart_"):
            raise ValueError("Only mart_ tables are allowed")
