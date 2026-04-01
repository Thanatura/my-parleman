import json
from typing import Any

from google.cloud import bigquery
from google.cloud.storage import Client


def upload_jsonl_to_gcs(
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


def load_table_from_uri(
    *,
    bq_client: bigquery.Client,
    table_name: str,
    source_uri: str,
    schema: list[bigquery.SchemaField],
    gcp_project: str,
    bq_dataset: str,
) -> int:
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
        schema=schema,
    )
    table_ref = f"{gcp_project}.{bq_dataset}.{table_name}"
    job = bq_client.load_table_from_uri(source_uri, table_ref, job_config=job_config)
    job.result()
    return int(getattr(job, "output_rows", 0) or 0)
