from dataclasses import asdict
from datetime import timedelta
from typing import Any

from prefect import flow, task

from prefect.cache_policies import INPUTS, NO_CACHE
from prefect.tasks import task_input_hash
from prefect_gcp import GcpCredentials
from lib.bq_utils import load_table_from_uri, upload_jsonl_to_gcs
from lib.config import ProjectConfig, get_config
from lib.debat import DebatParseResult, parse_debats_files
from lib.debat.bq_schemas import TABLE_SCHEMAS
from lib.extract import extract_file_contents, fetch_zip_file


@task(
    cache_key_fn=task_input_hash,
    persist_result=True,
    cache_expiration=timedelta(days=1),
)
def fetch_debat_data(debat_url: str) -> bytes:
    return fetch_zip_file(debat_url)


@task(
    cache_key_fn=task_input_hash,
    persist_result=True,
    cache_expiration=timedelta(days=1),
)
def extract_debat_data(debat_archive: bytes) -> list[str]:
    return extract_file_contents(debat_archive)


@task(
    persist_result=True,
    cache_policy=INPUTS,
    cache_expiration=timedelta(days=1),
)
def parse_debat_contents(debat_contents: list[str]) -> DebatParseResult:
    return parse_debats_files(debat_contents)


@task(cache_policy=NO_CACHE)
def upload_to_bigquery(parsed_debats: DebatParseResult, config: ProjectConfig) -> None:
    credentials = GcpCredentials(service_account_info=config.service_account_info)
    storage_client = credentials.get_cloud_storage_client(project=config.gcp_project)
    bq_client = credentials.get_bigquery_client(project=config.gcp_project)

    run_prefix = f"parleman-load/{config.bq_dataset}"
    table_payloads: dict[str, list[dict[str, Any]]] = {
        "comptes_rendus": [asdict(item) for item in parsed_debats.comptes_rendus],
        "points_seance": [asdict(item) for item in parsed_debats.points],
        "interventions": [asdict(item) for item in parsed_debats.interventions],
    }

    loaded_rows: dict[str, int] = {}
    uris: dict[str, str] = {}
    for table_name, records in table_payloads.items():
        blob_path = f"{run_prefix}/{table_name}.jsonl"
        source_uri = upload_jsonl_to_gcs(
            storage_client=storage_client,
            bucket_name=config.gcs_load_bucket,
            blob_path=blob_path,
            records=records,
        )
        uris[table_name] = source_uri
        loaded_rows[table_name] = load_table_from_uri(
            bq_client=bq_client,
            table_name=table_name,
            source_uri=source_uri,
            schema=TABLE_SCHEMAS[table_name],
            gcp_project=config.gcp_project,
            bq_dataset=config.bq_dataset,
        )


@flow
def debat_flow() -> None:
    config = get_config()
    debat_archive = fetch_debat_data(debat_url=config.debat_url)
    debat_contents = extract_debat_data(debat_archive)
    parsed_debats = parse_debat_contents(debat_contents)
    upload_to_bigquery(parsed_debats, config)


if __name__ == "__main__":
    debat_flow()
