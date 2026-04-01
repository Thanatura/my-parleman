from datetime import timedelta
import json
import os
from typing import Any

from prefect import flow, task

from prefect.artifacts import create_markdown_artifact
from prefect.cache_policies import INPUTS, NO_CACHE
from prefect.tasks import task_input_hash
from prefect_gcp import BigQueryWarehouse, GcpCredentials
from lib.debat import DebatParseResult, parse_debats_files
from lib.debat.sql_statements import build_sql_statements
from lib.extract import extract_file_contents, fetch_zip_file

DEBAT_URL = "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut/syseron.xml.zip"
GCP_PROJECT = "parleman-491810"
BQ_DATASET = "ParlemAN_tests"


def get_service_account_info() -> dict[str, Any]:
    parsed_obj: object = json.loads(os.environ["SERVICE_ACCOUNT_INFO"])
    if not isinstance(parsed_obj, dict):
        raise ValueError("SERVICE_ACCOUNT_INFO must decode to a JSON object")
    return {str(key): value for key, value in parsed_obj.items()}


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


@task(
    # persist_result=True,
    cache_policy=NO_CACHE,
    # cache_expiration=timedelta(days=1),
)
def build_sql_statements_task(parsed_debats: DebatParseResult) -> list[str]:
    return build_sql_statements(parsed_debats, GCP_PROJECT, BQ_DATASET)


@task(cache_policy=NO_CACHE)
def upload_to_bigquery(statements: list[str]) -> None:
    print(f"connecting to dataset {BQ_DATASET} in project {GCP_PROJECT}")
    create_markdown_artifact(
        key="statements",
        markdown="### SQL Statements Preview\n\n"
        + "\n---\n".join(f"- `{statement}`" for statement in statements),
    )
    credentials = GcpCredentials(service_account_info=get_service_account_info())
    with BigQueryWarehouse(gcp_credentials=credentials) as warehouse:
        for statement in statements:
            print(f"executing {statement[:80]}...", end="", flush=True)
            try:
                warehouse.execute(statement)
            except Exception as e:
                print(
                    'failed. writing failed statement to "failed_statement.sql" for debugging.'
                )
                open("failed_statement.sql", "w").write(statement)
                raise e
            print("done.")


@flow
def debat_flow() -> None:
    debat_archive = fetch_debat_data()
    debat_contents = extract_debat_data(debat_archive)
    parsed_debats = parse_debat_contents(debat_contents)
    statements = build_sql_statements_task(parsed_debats)
    upload_to_bigquery(statements)


if __name__ == "__main__":
    debat_flow()
