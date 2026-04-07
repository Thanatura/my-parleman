from typing import Sequence
from google.cloud import bigquery
from google.oauth2 import service_account
from prefect import get_run_logger
from prefect.artifacts import create_progress_artifact, update_progress_artifact
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
    logger = get_run_logger()

    logger.info("connecting to big query...")
    credentials = service_account.Credentials.from_service_account_info(
        config.service_account_info
    )

    bq_client = bigquery.Client(
        project=config.gcp_project,
        credentials=credentials,
    )

    logger.info("Finished connecting to big query")

    loaded_rows: dict[str, int] = {}

    logger.info("Creating dataset if not exists...")
    ensure_dataset(bq_client, config=config)
    logger.info("Finished ensuring dataset exists")

    progress_artifact_id = create_progress_artifact(
        progress=0.0,
        description="Loading tables to BigQuery",
    )

    nb_loaded_tables = 0
    total_tables = len(table_rows)
    for table_name, rows in table_rows.items():
        logger.info("Validating rows for table %s...", table_name)
        validate_rows_for_table(table_name, schemas, rows)
        logger.info("Finished validating rows for table %s...", table_name)

        logger.info("Loading table %s...", table_name)
        loaded_rows[table_name] = load_table_rows(
            bq_client,
            table_name,
            rows,
            config=config,
            schema=schemas[table_name],
        )
        logger.info(
            "Finished loading table %s. Loaded %d rows.",
            table_name,
            loaded_rows[table_name],
        )
        nb_loaded_tables += 1
        update_progress_artifact(
            artifact_id=progress_artifact_id,
            progress=(nb_loaded_tables / total_tables) * 100,
        )

    return loaded_rows
