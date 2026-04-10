from collections.abc import Iterable, Iterator
from typing import Sequence, cast
from uuid import UUID, uuid4
from google.cloud import bigquery
from google.oauth2 import service_account
from prefect import get_run_logger
from prefect.artifacts import create_progress_artifact, update_progress_artifact
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
    rows: Sequence[BigQueryRow],
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
    return len(rows)


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
    bq_client.create_table(bigquery.Table(table_id, schema=schema), exists_ok=True)
    bq_client.query(f"TRUNCATE TABLE `{table_id}`").result()


def _publish_staging_to_target(
    bq_client: bigquery.Client,
    target_table_id: str,
    staging_table_id: str,
) -> None:
    query = f"""
        CREATE OR REPLACE TABLE `{target_table_id}`
        AS SELECT * FROM `{staging_table_id}`
    """
    bq_client.query(query).result()


def _delete_table_if_exists(bq_client: bigquery.Client, table_id: str) -> None:
    bq_client.delete_table(table_id, not_found_ok=True)


def _prepare_staging_tables(
    bq_client: bigquery.Client,
    table_names: Sequence[str],
    schemas: dict[str, list[bigquery.SchemaField]],
    staging_table_ids: dict[str, str],
) -> None:
    for table_name in table_names:
        _create_or_replace_empty_table(
            bq_client=bq_client,
            table_id=staging_table_ids[table_name],
            schema=schemas[table_name],
        )


def _load_batch_to_staging(
    bq_client: bigquery.Client,
    table_rows: dict[str, Sequence[BigQueryRow]],
    table_names: Sequence[str],
    schemas: dict[str, list[bigquery.SchemaField]],
    staging_table_ids: dict[str, str],
    loaded_rows: dict[str, int],
) -> None:
    for table_name in table_names:
        rows = table_rows.get(table_name, [])
        validate_rows_for_table(table_name, schemas, rows)

        loaded_rows[table_name] += _load_rows_to_table_id(
            bq_client=bq_client,
            table_id=staging_table_ids[table_name],
            rows=rows,
            schema=schemas[table_name],
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )


def _publish_staging_tables(
    bq_client: bigquery.Client,
    config: ProjectConfig,
    table_names: Sequence[str],
    staging_table_ids: dict[str, str],
) -> None:
    for table_name in table_names:
        _publish_staging_to_target(
            bq_client=bq_client,
            target_table_id=_build_target_table_id(config, table_name),
            staging_table_id=staging_table_ids[table_name],
        )


def _cleanup_staging_tables(
    bq_client: bigquery.Client,
    staging_table_ids: dict[str, str],
) -> None:
    for table_id in staging_table_ids.values():
        _delete_table_if_exists(bq_client=bq_client, table_id=table_id)


def _update_global_progress(
    progress_artifact_id: UUID | None,
    completed_steps: int,
    total_steps: int,
) -> None:
    if progress_artifact_id is None or total_steps is None or total_steps <= 0:
        return
    update_progress_artifact(
        artifact_id=progress_artifact_id,
        progress=(completed_steps / total_steps) * 100,
    )


def _iter_table_rows_batches(
    table_rows: dict[str, Sequence[BigQueryRow]],
    batch_size: int,
) -> Iterator[dict[str, Sequence[BigQueryRow]]]:
    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")

    max_length = max((len(rows) for rows in table_rows.values()), default=0)
    for start in range(0, max_length, batch_size):
        yield {
            table_name: rows[start : start + batch_size]
            for table_name, rows in table_rows.items()
        }


def load_all_tables_by_batches(
    *,
    table_batches: Iterable[dict[str, Sequence[BigQueryRow]]],
    schemas: dict[str, list[bigquery.SchemaField]],
    config: ProjectConfig,
    run_id: str | None = None,
    nb_batches: int,
) -> dict[str, int]:
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
    nb_steps = nb_batches + len(schemas) + 1

    progress_artifact_id = cast(
        UUID,
        create_progress_artifact(
            progress=0.0,
            description="Idempotent staged loading to BigQuery",
        ),
    )

    logger.info("Preparing %d staging tables", len(table_names))

    _prepare_staging_tables(
        bq_client=bq_client,
        table_names=table_names,
        schemas=schemas,
        staging_table_ids=staging_table_ids,
    )
    logger.info("Staging tables prepared")

    try:
        completed_steps = 0
        batch_count = 0
        for table_rows in table_batches:
            batch_count += 1
            _load_batch_to_staging(
                bq_client=bq_client,
                table_rows=table_rows,
                table_names=table_names,
                schemas=schemas,
                staging_table_ids=staging_table_ids,
                loaded_rows=loaded_rows,
            )
            completed_steps += 1
            _update_global_progress(
                progress_artifact_id=progress_artifact_id,
                completed_steps=completed_steps,
                total_steps=nb_steps,
            )

            logger.info(
                "Loaded staging batch %d%s",
                batch_count,
                f"/{nb_batches}" if nb_batches else "",
            )

        logger.info("Publishing staging tables to target tables")
        _publish_staging_tables(
            bq_client=bq_client,
            config=config,
            table_names=table_names,
            staging_table_ids=staging_table_ids,
        )
        completed_steps += 1
        _update_global_progress(
            progress_artifact_id=progress_artifact_id,
            completed_steps=completed_steps,
            total_steps=nb_steps,
        )
        logger.info("Published %d tables to target", len(table_names))
    finally:
        logger.info("Cleaning up staging tables")
        _cleanup_staging_tables(
            bq_client=bq_client,
            staging_table_ids=staging_table_ids,
        )
        completed_steps += 1
        _update_global_progress(
            progress_artifact_id=progress_artifact_id,
            completed_steps=completed_steps,
            total_steps=nb_steps,
        )

    return loaded_rows


def load_all_tables(
    *,
    table_rows: dict[str, Sequence[BigQueryRow]],
    schemas: dict[str, list[bigquery.SchemaField]],
    config: ProjectConfig,
    batch_size: int = 40_000,
) -> dict[str, int]:
    table_batches = _iter_table_rows_batches(table_rows, batch_size=batch_size)
    nb_batches = sum(len(rows) for rows in table_rows.values()) // batch_size + 1
    return load_all_tables_by_batches(
        table_batches=table_batches,
        schemas=schemas,
        config=config,
        nb_batches=nb_batches,
    )
