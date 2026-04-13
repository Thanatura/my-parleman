from collections.abc import Mapping
from typing import Sequence

from prefect import flow, get_run_logger, task
from prefect.artifacts import create_table_artifact
from prefect.tasks import task_input_hash

from lib.bq_utils import load_all_tables
from lib.bq_utils.models import BigQueryRow
from lib.config import ProjectConfig, get_config
from lib.extract import fetch_zip_file
from lib.scrutins.bq_schemas import SCRUTINS_SCHEMAS
from lib.scrutins.models import ScrutinParseResult
from lib.scrutins.parsing import parse_scrutins


@task(cache_key_fn=task_input_hash, cache_expiration=None)
def fetch_zip(url: str) -> bytes:
    logger = get_run_logger()
    logger.info(f"Downloading {url}")
    content = fetch_zip_file(url)
    logger.info(f"Downloaded {len(content):,} bytes")
    return content


@task
def parse_scrutins_table(zip_bytes: bytes) -> ScrutinParseResult:
    return parse_scrutins(zip_bytes)


@task
def load_to_bigquery(
    scrutins_result: ScrutinParseResult, config: ProjectConfig
) -> None:
    table_payloads: Mapping[str, Sequence[BigQueryRow]] = {
        "scrutins": scrutins_result.scrutins,
        "scrutin_groupes_votes": scrutins_result.groupes_votes,
        "scrutin_votes_individuels": scrutins_result.votes_individuels,
    }

    loaded_rows = load_all_tables(
        table_rows=table_payloads,
        schemas=SCRUTINS_SCHEMAS,
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
        description="scrutins load summary by table",
    )


@flow
def scrutin_flow() -> None:
    config = get_config()
    zip_bytes = fetch_zip(config.scrutins_url)
    scrutins_result = parse_scrutins_table(zip_bytes)
    load_to_bigquery(scrutins_result, config)


if __name__ == "__main__":
    scrutin_flow()
