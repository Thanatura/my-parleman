from collections.abc import Mapping, Sequence

from google.api_core.exceptions import NotFound
from google.cloud import bigquery

from lib.config import ProjectConfig


def schema_signature(
    schema: Sequence[bigquery.SchemaField],
) -> list[dict[str, object]]:
    return [field.to_api_repr() for field in schema]


def build_target_table_id(config: ProjectConfig, table_name: str) -> str:
    return f"{config.gcp_project}.{config.bq_dataset}.{table_name}"


def build_staging_table_id(
    config: ProjectConfig,
    table_name: str,
    staging_suffix: str,
) -> str:
    return (
        f"{config.gcp_project}.{config.bq_dataset}."
        f"_staging_{table_name}_{staging_suffix}"
    )


def create_or_replace_empty_table(
    bq_client: bigquery.Client,
    table_id: str,
    schema: list[bigquery.SchemaField],
) -> None:
    recreate_table = False
    try:
        existing_table = bq_client.get_table(table_id)
        recreate_table = schema_signature(existing_table.schema) != schema_signature(
            schema
        )
    except NotFound:
        recreate_table = True

    if recreate_table:
        bq_client.delete_table(table_id, not_found_ok=True)
        bq_client.create_table(bigquery.Table(table_id, schema=schema), exists_ok=True)

    bq_client.query(f"TRUNCATE TABLE `{table_id}`").result()


def publish_staging_to_target(
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


def delete_table_if_exists(bq_client: bigquery.Client, table_id: str) -> None:
    bq_client.delete_table(table_id, not_found_ok=True)


def prepare_staging_tables(
    bq_client: bigquery.Client,
    table_names: Sequence[str],
    schemas: Mapping[str, list[bigquery.SchemaField]],
    staging_table_ids: Mapping[str, str],
) -> None:
    for table_name in table_names:
        create_or_replace_empty_table(
            bq_client=bq_client,
            table_id=staging_table_ids[table_name],
            schema=schemas[table_name],
        )


def cleanup_staging_tables(
    bq_client: bigquery.Client,
    staging_table_ids: Mapping[str, str],
) -> None:
    for table_id in staging_table_ids.values():
        delete_table_if_exists(bq_client=bq_client, table_id=table_id)
