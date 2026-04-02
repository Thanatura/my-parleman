from collections.abc import Sequence

import requests
from google.cloud import bigquery
from google.oauth2 import service_account
from lib.config import ProjectConfig
from lib.depute.bq_schemas import DEPUTES_SCHEMAS
from lib.depute.models import BigQueryRow
from lib.depute.validation import validate_all_tables


def fetch_zip_data(url: str, timeout: int = 120) -> bytes:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content


def ensure_dataset(client: bigquery.Client, config: ProjectConfig) -> None:
    dataset_ref = bigquery.Dataset(f"{config.gcp_project}.{config.bq_dataset}")
    dataset_ref.location = "EU"
    client.create_dataset(dataset_ref, exists_ok=True)


def load_table_rows(
    bq_client: bigquery.Client,
    table_name: str,
    rows: Sequence[BigQueryRow],
    config: ProjectConfig,
) -> int:
    if not rows:
        return 0

    table_id = f"{config.gcp_project}.{config.bq_dataset}.{table_name}"
    json_rows = [row.to_bq_dict() for row in rows]

    job_config = bigquery.LoadJobConfig(
        schema=DEPUTES_SCHEMAS[table_name],
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    job = bq_client.load_table_from_json(json_rows, table_id, job_config=job_config)
    job.result()
    return len(rows)


def load_all_tables(
    *,
    acteurs: Sequence[BigQueryRow],
    adresses: Sequence[BigQueryRow],
    mandats: Sequence[BigQueryRow],
    organes: Sequence[BigQueryRow],
    deports: Sequence[BigQueryRow],
    config: ProjectConfig,
) -> dict[str, int]:
    credentials = service_account.Credentials.from_service_account_info(
        config.service_account_info
    )

    bq_client = bigquery.Client(
        project=config.gcp_project,
        credentials=credentials,
    )
    validate_all_tables(
        acteurs=acteurs,
        adresses=adresses,
        mandats=mandats,
        organes=organes,
        deports=deports,
    )

    ensure_dataset(bq_client, config=config)

    return {
        "acteurs": load_table_rows(bq_client, "acteurs", acteurs, config=config),
        "adresses": load_table_rows(bq_client, "adresses", adresses, config=config),
        "mandats": load_table_rows(bq_client, "mandats", mandats, config=config),
        "organes": load_table_rows(bq_client, "organes", organes, config=config),
        "deports": load_table_rows(bq_client, "deports", deports, config=config),
    }
