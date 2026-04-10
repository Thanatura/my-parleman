from collections.abc import Mapping
from typing import Sequence

from prefect import flow, get_run_logger, task
from prefect.artifacts import create_table_artifact
from prefect.tasks import task_input_hash

from lib.bq_utils import load_all_tables
from lib.bq_utils.models import BigQueryRow
from lib.config import ProjectConfig, get_config
from lib.extract import fetch_zip_file
from lib.questions_ecrites.bq_schemas import QUESTIONS_ECRITES_SCHEMAS
from lib.questions_ecrites.models import QuestionEcriteParseResult
from lib.questions_ecrites.parsing import parse_questions_ecrites


@task(cache_key_fn=task_input_hash, cache_expiration=None)
def fetch_zip(url: str) -> bytes:
    logger = get_run_logger()
    logger.info(f"Downloading {url}")
    content = fetch_zip_file(url)
    logger.info(f"Downloaded {len(content):,} bytes")
    return content


@task
def parse_questions_ecrites_table(zip_bytes: bytes) -> QuestionEcriteParseResult:
    return parse_questions_ecrites(zip_bytes)


@task
def load_to_bigquery(
    questions_ecrites_result: QuestionEcriteParseResult, config: ProjectConfig
) -> None:
    table_payloads: Mapping[str, Sequence[BigQueryRow]] = {
        "questions_ecrites": questions_ecrites_result.questions,
        "questions_ecrites_min_attribs": questions_ecrites_result.min_attribs,
        "questions_ecrites_renouvellements": questions_ecrites_result.renouvellements,
    }

    loaded_rows = load_all_tables(
        table_rows=table_payloads,
        schemas=QUESTIONS_ECRITES_SCHEMAS,
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
        description="questions ecrites load summary by table",
    )


@flow
def questions_ecrites_flow() -> None:
    config = get_config()
    zip_bytes = fetch_zip(config.questions_ecrites_url)
    questions_ecrites_result = parse_questions_ecrites_table(zip_bytes)
    load_to_bigquery(questions_ecrites_result, config)


if __name__ == "__main__":
    questions_ecrites_flow()
