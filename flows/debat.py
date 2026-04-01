import json
import os
from typing import Any

from prefect import flow, task
from prefect.cache_policies import INPUTS, NO_CACHE
from prefect.tasks import task_input_hash
from prefect_gcp import BigQueryWarehouse, GcpCredentials
from lib.debat import CompteRendu, DebatParseResult, parse_debats_files
from lib.extract import extract_file_contents, fetch_zip_file

DEBAT_URL = "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut/syseron.xml.zip"
GCP_PROJECT = "parleman-491810"
BQ_DATASET = "ParlemAN_tests"


def get_service_account_info() -> dict[str, Any]:
    parsed_obj: object = json.loads(os.environ["SERVICE_ACCOUNT_INFO"])
    if not isinstance(parsed_obj, dict):
        raise ValueError("SERVICE_ACCOUNT_INFO must decode to a JSON object")
    return {str(key): value for key, value in parsed_obj.items()}


@task(cache_key_fn=task_input_hash, persist_result=True)
def fetch_debat_data() -> bytes:
    debat_archive = fetch_zip_file(DEBAT_URL)
    return debat_archive


@task(cache_key_fn=task_input_hash, persist_result=True)
def extract_debat_data(debat_archive: bytes) -> list[str]:
    debat_contents = extract_file_contents(debat_archive)
    return debat_contents


@task(persist_result=True, cache_policy=INPUTS)
def parse_debat_contents(debat_contents: list[str]) -> DebatParseResult:
    return parse_debats_files(debat_contents)


@task(cache_policy=NO_CACHE)
def upload_to_bigquery(parsed_debats: DebatParseResult) -> None:
    credentials = GcpCredentials(service_account_info=get_service_account_info())
    with BigQueryWarehouse(gcp_credentials=credentials) as warehouse:
        print(f"connected to dataset {BQ_DATASET} in project {GCP_PROJECT}")
        warehouse.execute(
            CompteRendu.create_table_sql_text(
                project_id=GCP_PROJECT, dataset_id=BQ_DATASET
            )
        )
        warehouse.execute(
            CompteRendu.truncate_table_sql_text(
                project_id=GCP_PROJECT, dataset_id=BQ_DATASET
            )
        )
        print("created and truncated table comptes_rendus")
        print(
            "will execute : ",
            len(parsed_debats.comptes_rendus),
            "comptes_rendus inserts",
        )
        smt = f"""
            INSERT INTO {GCP_PROJECT}.{BQ_DATASET}.comptes_rendus
            VALUES {",".join(compte_rendu.insert_sql_text_values() for compte_rendu in parsed_debats.comptes_rendus)};
            """
        print(smt)
        # warehouse.execute(

        # )
        print("will execute : ", len(parsed_debats.points), "points inserts")
        print(
            "will execute : ", len(parsed_debats.interventions), "interventions inserts"
        )
        # insert in batches of 1000 to avoid hitting BigQuery limits
        # batch_size = 1000
        # for i in range(0, len(parsed_debats.comptes_rendus), batch_size):
        #     batch = parsed_debats.comptes_rendus[i : i + batch_size]

        print("finished inserting data into BigQuery")


@flow
def debat_flow() -> None:
    debat_archive = fetch_debat_data()
    debat_contents = extract_debat_data(debat_archive)
    parsed_debats = parse_debat_contents(debat_contents)
    upload_to_bigquery(parsed_debats)


if __name__ == "__main__":
    debat_flow()
