"""Core service layer for data ingestion and BigQuery loading."""

from collections.abc import Sequence

import requests
from google.cloud import bigquery

from lib.bq_schemas import SCHEMA
from lib.constants import BQ_DATASET, GCP_PROJECT
from lib.models import BigQueryRow
from lib.validation import validate_all_tables


def fetch_zip_data(url: str, timeout: int = 120) -> bytes:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content


def ensure_dataset(
    client: bigquery.Client, project: str = GCP_PROJECT, dataset: str = BQ_DATASET
) -> None:
    dataset_ref = bigquery.Dataset(f"{project}.{dataset}")
    dataset_ref.location = "EU"
    client.create_dataset(dataset_ref, exists_ok=True)


def load_table_rows(
    client: bigquery.Client,
    table_name: str,
    rows: Sequence[BigQueryRow],
    project: str = GCP_PROJECT,
    dataset: str = BQ_DATASET,
) -> int:
    if not rows:
        return 0

    table_id = f"{project}.{dataset}.{table_name}"
    json_rows = [row.to_bq_dict() for row in rows]

    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA[table_name],
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    job = client.load_table_from_json(json_rows, table_id, job_config=job_config)
    job.result()
    return len(rows)


def load_all_tables(
    *,
    acteurs: Sequence[BigQueryRow],
    adresses: Sequence[BigQueryRow],
    mandats: Sequence[BigQueryRow],
    organes: Sequence[BigQueryRow],
    deports: Sequence[BigQueryRow],
    project: str = GCP_PROJECT,
    dataset: str = BQ_DATASET,
) -> dict[str, int]:
    validate_all_tables(
        acteurs=acteurs,
        adresses=adresses,
        mandats=mandats,
        organes=organes,
        deports=deports,
    )

    client = bigquery.Client(project=project)
    ensure_dataset(client, project=project, dataset=dataset)

    return {
        "acteurs": load_table_rows(
            client, "acteurs", acteurs, project=project, dataset=dataset
        ),
        "adresses": load_table_rows(
            client, "adresses", adresses, project=project, dataset=dataset
        ),
        "mandats": load_table_rows(
            client, "mandats", mandats, project=project, dataset=dataset
        ),
        "organes": load_table_rows(
            client, "organes", organes, project=project, dataset=dataset
        ),
        "deports": load_table_rows(
            client, "deports", deports, project=project, dataset=dataset
        ),
    }
