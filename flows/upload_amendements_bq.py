from typing import Sequence

from prefect import flow, get_run_logger, task
from prefect.artifacts import create_table_artifact
from prefect.tasks import task_input_hash

from lib.bq_utils.bq_utils import load_all_tables
from lib.bq_utils.models import BigQueryRow
from lib.config import ProjectConfig, get_config
from lib.amendements import (
    AMENDEMENTS_SCHEMAS,
    AmendementParseResult,
    parse_amendements,
)
from lib.extract import fetch_zip_file


@task(cache_key_fn=task_input_hash, cache_expiration=None)
def fetch_zip(url: str) -> bytes:
    logger = get_run_logger()
    logger.info(f"Downloading {url}")
    content = fetch_zip_file(url)
    logger.info(f"Downloaded {len(content):,} bytes")
    return content


@task
def parse_amendements_table(zip_bytes: bytes) -> AmendementParseResult:
    logger = get_run_logger()
    result = parse_amendements(zip_bytes)
    logger.info(f"Parsed {len(result.amendements)} amendements")
    logger.info(f"Parsed {len(result.signataires)} signataires")
    logger.info(f"Parsed {len(result.cosignataires)} cosignataires")
    return result


@task
def load_to_bigquery(
    amendements_result: AmendementParseResult, config: ProjectConfig
) -> None:
    table_payloads: dict[str, Sequence[BigQueryRow]] = {
        "amendements": amendements_result.amendements,
        "amendement_signataires": amendements_result.signataires,
        "amendement_cosignataires": amendements_result.cosignataires,
    }

    loaded_rows = load_all_tables(
        table_rows=table_payloads,
        schemas=AMENDEMENTS_SCHEMAS,
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
        description="amendements load summary by table",
    )


@flow
def amendements_pipeline() -> None:
    config = get_config()
    zip_bytes = fetch_zip(config.amendements_url)
    amendements_result = parse_amendements_table(zip_bytes)
    load_to_bigquery(amendements_result, config)


if __name__ == "__main__":
    amendements_pipeline()
