from collections.abc import Iterable, Iterator, Mapping
from typing import Sequence
from uuid import uuid4
from google.api_core.exceptions import NotFound
from google.cloud import bigquery
from google.oauth2 import service_account
from prefect import get_run_logger
from lib.bq_utils.models import BigQueryRow
from lib.bq_utils.validation import ensure_dataset, validate_rows_for_table
from lib.config import ProjectConfig


def _create_bq_client(config: ProjectConfig) -> bigquery.Client:
    credentials = service_account.Credentials.from_service_account_info(
        config.service_account_info
    )
    return bigquery.Client(
        project=config.gcp_project,
        credentials=credentials,
    )


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


def _schema_signature(
    schema: Sequence[bigquery.SchemaField],
) -> list[dict[str, object]]:
    return [field.to_api_repr() for field in schema]


def _build_target_table_id(config: ProjectConfig, table_name: str) -> str:
    return f"{config.gcp_project}.{config.bq_dataset}.{table_name}"


def _build_staging_table_id(
    config: ProjectConfig,
    table_name: str,
    staging_suffix: str,
) -> str:
    return (
        f"{config.gcp_project}.{config.bq_dataset}."
        f"_staging_{table_name}_{staging_suffix}"
    )


def _create_or_replace_empty_table(
    bq_client: bigquery.Client,
    table_id: str,
    schema: list[bigquery.SchemaField],
) -> None:
    recreate_table = False
    try:
        existing_table = bq_client.get_table(table_id)
        recreate_table = _schema_signature(existing_table.schema) != _schema_signature(
            schema
        )
    except NotFound:
        recreate_table = True

    if recreate_table:
        bq_client.delete_table(table_id, not_found_ok=True)
        bq_client.create_table(bigquery.Table(table_id, schema=schema), exists_ok=True)

    bq_client.query(f"TRUNCATE TABLE `{table_id}`").result()


def _publish_staging_to_target(
    bq_client: bigquery.Client,
    target_table_id: str,
    staging_table_id: str,
) -> None:
    copy_job_config = bigquery.CopyJobConfig(
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    source_table = bigquery.TableReference.from_string(staging_table_id)
    destination_table = bigquery.TableReference.from_string(target_table_id)
    job = bq_client.copy_table(
        sources=source_table,
        destination=destination_table,
        job_config=copy_job_config,
    )
    job.result()


def _delete_table_if_exists(bq_client: bigquery.Client, table_id: str) -> None:
    bq_client.delete_table(table_id, not_found_ok=True)


def _prepare_staging_tables(
    bq_client: bigquery.Client,
    table_names: Sequence[str],
    schemas: Mapping[str, list[bigquery.SchemaField]],
    staging_table_ids: Mapping[str, str],
) -> None:
    for table_name in table_names:
        _create_or_replace_empty_table(
            bq_client=bq_client,
            table_id=staging_table_ids[table_name],
            schema=schemas[table_name],
        )


def _cleanup_staging_tables(
    bq_client: bigquery.Client,
    staging_table_ids: Mapping[str, str],
) -> None:
    for table_id in staging_table_ids.values():
        _delete_table_if_exists(bq_client=bq_client, table_id=table_id)


def _iter_chunked_rows(
    rows_iter: Iterable[BigQueryRow],
    chunk_size: int,
) -> Iterator[list[BigQueryRow]]:
    chunk: list[BigQueryRow] = []
    for row in rows_iter:
        chunk.append(row)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def load_all_tables_by_batches(
    *,
    table_batches: Mapping[str, Iterable[BigQueryRow]],
    schemas: Mapping[str, list[bigquery.SchemaField]],
    config: ProjectConfig,
    run_id: str | None = None,
) -> Mapping[str, int]:
    logger = get_run_logger()
    logger.info("connecting to big query...")
    bq_client = _create_bq_client(config)
    logger.info("Finished connecting to big query")

    logger.info("Creating dataset if not exists...")
    ensure_dataset(bq_client, config=config)
    logger.info("Finished ensuring dataset exists")

    table_names = list(schemas.keys())
    staging_suffix = (run_id or str(uuid4())).replace("-", "_")
    staging_table_ids = {
        table_name: _build_staging_table_id(config, table_name, staging_suffix)
        for table_name in table_names
    }
    loaded_rows: dict[str, int] = {table_name: 0 for table_name in table_names}

    logger.info("Preparing %d staging tables", len(table_names))
    _prepare_staging_tables(
        bq_client=bq_client,
        table_names=table_names,
        schemas=schemas,
        staging_table_ids=staging_table_ids,
    )
    logger.info("Staging tables prepared")

    try:
        chunk_size = 40_000
        for table_name in table_names:
            table_iter = table_batches.get(table_name)
            if table_iter is None:
                raise ValueError(f"Missing table iterable for '{table_name}'")

            table_batch_count = 0
            for table_batch_count, batch_rows in enumerate(
                _iter_chunked_rows(table_iter, chunk_size=chunk_size),
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
            _publish_staging_to_target(
                bq_client=bq_client,
                target_table_id=_build_target_table_id(config, table_name),
                staging_table_id=staging_table_ids[table_name],
            )

        logger.info("Published %d tables to target", len(table_names))
    finally:
        logger.info("Cleaning up staging tables")
        _cleanup_staging_tables(
            bq_client=bq_client,
            staging_table_ids=staging_table_ids,
        )

    return loaded_rows


def load_all_tables(
    *,
    table_rows: Mapping[str, Iterable[BigQueryRow]],
    schemas: Mapping[str, list[bigquery.SchemaField]],
    config: ProjectConfig,
) -> Mapping[str, int]:
    return load_all_tables_by_batches(
        table_batches=table_rows,
        schemas=schemas,
        config=config,
    )
