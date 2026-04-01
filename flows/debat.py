from dataclasses import asdict
from datetime import timedelta
import json
import os
from typing import Any

from google.cloud import bigquery
from google.cloud.storage import Client
from prefect import flow, task

from prefect.artifacts import create_markdown_artifact
from prefect.cache_policies import INPUTS, NO_CACHE
from prefect.tasks import task_input_hash
from prefect_gcp import GcpCredentials
from lib.debat import DebatParseResult, parse_debats_files
from lib.debat.bq_schemas import TABLE_SCHEMAS
from lib.extract import extract_file_contents, fetch_zip_file

DEBAT_URL = "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut/syseron.xml.zip"
GCP_PROJECT = "parleman-491810"
BQ_DATASET = "ParlemAN_tests"


def get_service_account_info() -> dict[str, Any]:
    parsed_obj: object = json.loads(os.environ["SERVICE_ACCOUNT_INFO"])
    if not isinstance(parsed_obj, dict):
        raise ValueError("SERVICE_ACCOUNT_INFO must decode to a JSON object")
    return {str(key): value for key, value in parsed_obj.items()}


def get_gcs_load_bucket() -> str:
    bucket = os.environ.get("GCS_LOAD_BUCKET")
    if not bucket:
        raise ValueError("GCS_LOAD_BUCKET environment variable must be set")
    return bucket


@task(
    cache_key_fn=task_input_hash,
    persist_result=True,
    cache_expiration=timedelta(days=1),
)
def fetch_debat_data() -> bytes:
    debat_archive = fetch_zip_file(DEBAT_URL)
    return debat_archive


@task(
    cache_key_fn=task_input_hash,
    persist_result=True,
    cache_expiration=timedelta(days=1),
)
def extract_debat_data(debat_archive: bytes) -> list[str]:
    debat_contents = extract_file_contents(debat_archive)
    return debat_contents


@task(
    persist_result=True,
    cache_policy=INPUTS,
    cache_expiration=timedelta(days=1),
)
def parse_debat_contents(debat_contents: list[str]) -> DebatParseResult:
    return parse_debats_files(debat_contents)


def _upload_jsonl_to_gcs(
    *,
    storage_client: Client,
    bucket_name: str,
    blob_path: str,
    records: list[dict[str, Any]],
) -> str:
    payload = "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_string(payload, content_type="application/json")
    return f"gs://{bucket_name}/{blob_path}"


def _load_table_from_uri(
    *,
    bq_client: bigquery.Client,
    table_name: str,
    source_uri: str,
    schema: list[bigquery.SchemaField],
) -> int:
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
        schema=schema,
    )
    table_ref = f"{GCP_PROJECT}.{BQ_DATASET}.{table_name}"
    job = bq_client.load_table_from_uri(source_uri, table_ref, job_config=job_config)
    job.result()
    return int(getattr(job, "output_rows", 0) or 0)


@task(cache_policy=NO_CACHE)
def upload_to_bigquery(parsed_debats: DebatParseResult) -> None:
    GCS_LOAD_BUCKET = get_gcs_load_bucket()

    print(f"loading dataset {BQ_DATASET} in project {GCP_PROJECT} via load jobs")
    credentials = GcpCredentials(service_account_info=get_service_account_info())
    storage_client = credentials.get_cloud_storage_client(project=GCP_PROJECT)
    bq_client = credentials.get_bigquery_client(project=GCP_PROJECT)

    run_prefix = f"parleman-load/{BQ_DATASET}"
    table_payloads: dict[str, list[dict[str, Any]]] = {
        "comptes_rendus": [asdict(item) for item in parsed_debats.comptes_rendus],
        "points_seance": [asdict(item) for item in parsed_debats.points],
        "interventions": [asdict(item) for item in parsed_debats.interventions],
    }

    loaded_rows: dict[str, int] = {}
    uris: dict[str, str] = {}
    for table_name, records in table_payloads.items():
        blob_path = f"{run_prefix}/{table_name}.jsonl"
        source_uri = _upload_jsonl_to_gcs(
            storage_client=storage_client,
            bucket_name=GCS_LOAD_BUCKET,
            blob_path=blob_path,
            records=records,
        )
        uris[table_name] = source_uri
        loaded_rows[table_name] = _load_table_from_uri(
            bq_client=bq_client,
            table_name=table_name,
            source_uri=source_uri,
            schema=TABLE_SCHEMAS[table_name],
        )

    create_markdown_artifact(
        key="bq-load-jobs",
        markdown=(
            "### BigQuery Load Summary\n\n"
            f"- comptes_rendus: {loaded_rows['comptes_rendus']} rows ({uris['comptes_rendus']})\n"
            f"- points_seance: {loaded_rows['points_seance']} rows ({uris['points_seance']})\n"
            f"- interventions: {loaded_rows['interventions']} rows ({uris['interventions']})"
        ),
    )


@flow
def debat_flow() -> None:
    debat_archive = fetch_debat_data()
    debat_contents = extract_debat_data(debat_archive)
    parsed_debats = parse_debat_contents(debat_contents)
    upload_to_bigquery(parsed_debats)


if __name__ == "__main__":
    debat_flow()
