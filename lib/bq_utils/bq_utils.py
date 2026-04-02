from typing import Sequence
from google.cloud import bigquery
from google.oauth2 import service_account
from lib.bq_utils.models import BigQueryRow
from lib.bq_utils.validation import ensure_dataset, validate_rows_for_table
from lib.config import ProjectConfig


def load_table_rows(
    bq_client: bigquery.Client,
    table_name: str,
    rows: Sequence[BigQueryRow],
    config: ProjectConfig,
    schema: list[bigquery.SchemaField],
) -> int:
    if not rows:
        return 0

    table_id = f"{config.gcp_project}.{config.bq_dataset}.{table_name}"
    json_rows = [row.to_bq_dict() for row in rows]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    job = bq_client.load_table_from_json(json_rows, table_id, job_config=job_config)
    job.result()
    return len(rows)


def load_all_tables(
    *,
    table_rows: dict[str, Sequence[BigQueryRow]],
    schemas: dict[str, list[bigquery.SchemaField]],
    config: ProjectConfig,
) -> dict[str, int]:
    credentials = service_account.Credentials.from_service_account_info(
        config.service_account_info
    )

    bq_client = bigquery.Client(
        project=config.gcp_project,
        credentials=credentials,
    )
    for table_name, rows in table_rows.items():
        validate_rows_for_table(table_name, schemas, rows)

    ensure_dataset(bq_client, config=config)

    loaded_rows: dict[str, int] = {}
    for table_name, records in table_rows.items():
        loaded_rows[table_name] = load_table_rows(
            bq_client,
            table_name,
            records,
            config=config,
            schema=schemas[table_name],
        )
    return loaded_rows
