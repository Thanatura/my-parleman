from collections.abc import Mapping
from datetime import timedelta
from typing import Sequence

from prefect import flow, task
from prefect.artifacts import create_table_artifact

from prefect.cache_policies import INPUTS, NO_CACHE
from prefect.tasks import task_input_hash
from lib.bq_utils import load_all_tables
from lib.bq_utils.models import BigQueryRow
from lib.config import ProjectConfig, get_config
from lib.debat import DebatParseResult, parse_debats_files
from lib.debat.bq_schemas import DEBATS_SCHEMAS
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
    table_payloads: Mapping[str, Sequence[BigQueryRow]] = {
        "comptes_rendus": parsed_debats.comptes_rendus,
        "points_seance": parsed_debats.points,
        "interventions": parsed_debats.interventions,
    }

    loaded_rows = load_all_tables(
        table_rows=table_payloads,
        schemas=DEBATS_SCHEMAS,
        config=config,
    )

    create_table_artifact(
        key="bq-load-summary",
        table=[
            {
                "table": table_name,
                "loaded_rows": loaded_rows[table_name],
            }
            for table_name in table_payloads
        ],
        description="debats load summary by table",
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
