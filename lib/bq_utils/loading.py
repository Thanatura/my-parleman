from collections.abc import Iterable, Mapping
from uuid import uuid4

from google.cloud import bigquery
from prefect import get_run_logger

from lib.bq_utils.client import create_bq_client
from lib.bq_utils.chunking import iter_chunked_rows
from lib.bq_utils.models import BigQueryRow
from lib.bq_utils.staging import (
    build_staging_table_id,
    build_target_table_id,
    cleanup_staging_tables,
    prepare_staging_tables,
    publish_staging_to_target,
)
from lib.bq_utils.validation import ensure_dataset, validate_rows_for_table
from lib.config import ProjectConfig


def _load_rows_to_table_id(
    bq_client: bigquery.Client,
    table_id: str,
    rows: Iterable[BigQueryRow],
    schema: list[bigquery.SchemaField],
    write_disposition: str,
) -> int:
    if not rows:
        return 0

    json_rows = [row.to_bq_dict() for row in rows]

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=write_disposition,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    job = bq_client.load_table_from_json(json_rows, table_id, job_config=job_config)
    job.result()
    return len(json_rows)


def load_all_tables_by_batches(
    *,
    table_rows: Mapping[str, Iterable[BigQueryRow]],
    schemas: Mapping[str, list[bigquery.SchemaField]],
    config: ProjectConfig,
    run_id: str | None = None,
) -> Mapping[str, int]:
    logger = get_run_logger()
    logger.info("connecting to big query...")
    bq_client = create_bq_client(config)
    logger.info("Finished connecting to big query")

    logger.info("Creating dataset if not exists...")
    ensure_dataset(bq_client, config=config)
    logger.info("Finished ensuring dataset exists")

    table_names = list(schemas.keys())
    staging_suffix = (run_id or str(uuid4())).replace("-", "_")
    staging_table_ids = {
        table_name: build_staging_table_id(config, table_name, staging_suffix)
        for table_name in table_names
    }
    loaded_rows: dict[str, int] = {table_name: 0 for table_name in table_names}

    logger.info("Preparing %d staging tables", len(table_names))
    prepare_staging_tables(
        bq_client=bq_client,
        table_names=table_names,
        schemas=schemas,
        staging_table_ids=staging_table_ids,
    )
    logger.info("Staging tables prepared")

    try:
        chunk_size = 40_000
        for table_name in table_names:
            table_iter = table_rows.get(table_name)
            if table_iter is None:
                raise ValueError(f"Missing table iterable for '{table_name}'")

            table_batch_count = 0
            for table_batch_count, batch_rows in enumerate(
                iter_chunked_rows(table_iter, chunk_size=chunk_size),
                start=1,
            ):
                validate_rows_for_table(table_name, schemas, batch_rows)
                loaded_rows[table_name] += _load_rows_to_table_id(
                    bq_client=bq_client,
                    table_id=staging_table_ids[table_name],
                    rows=batch_rows,
                    schema=schemas[table_name],
                    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                )

                logger.info(
                    "Loaded staging batch %d for table %s",
                    table_batch_count,
                    table_name,
                )

        logger.info("Publishing staging tables to target tables")
        for table_name in table_names:
            publish_staging_to_target(
                bq_client=bq_client,
                target_table_id=build_target_table_id(config, table_name),
                staging_table_id=staging_table_ids[table_name],
            )

        logger.info("Published %d tables to target", len(table_names))
    finally:
        logger.info("Cleaning up staging tables")
        cleanup_staging_tables(
            bq_client=bq_client,
            staging_table_ids=staging_table_ids,
        )

    return loaded_rows
