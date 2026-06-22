from collections.abc import Mapping
import os

from prefect import flow, get_run_logger, task
from prefect.artifacts import create_table_artifact

from lib.amendements.parsing import parse_amendements
from lib.bq_utils import load_all_tables
from lib.config import ProjectConfig, get_config
from lib.amendements import (
    AMENDEMENTS_SCHEMAS,
)
from lib.extract import fetch_zip_file_to_temp


@task
def fetch_zip_to_file(url: str) -> str:
    logger = get_run_logger()
    logger.info(f"Downloading {url}")
    file_path = fetch_zip_file_to_temp(url)
    logger.info(f"Downloaded archive to {file_path}")
    return file_path


@task
def publish_load_summary_artifact(
    total_loaded_rows: Mapping[str, int],
    batch_count: int,
) -> None:
    create_table_artifact(
        key="bq-load-summary",
        table=[
            {
                "table": table_name,
                "loaded_rows": total_loaded_rows[table_name],
            }
            for table_name in sorted(total_loaded_rows)
        ],
        description=(f"amendements load summary by table (after batch {batch_count})"),
    )


@task
def cleanup_temp_file(zip_file_path: str) -> None:
    logger = get_run_logger()
    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)
        logger.info("Deleted temporary file %s", zip_file_path)


@flow
def parse_and_load_amendements(
    zip_file_path: str,
    config: ProjectConfig,
) -> None:
    logger = get_run_logger()

    table_names = {
        "amendements",
        "amendement_signataires",
        "amendement_cosignataires",
    }
    total_loaded_rows = {table_name: 0 for table_name in table_names}
    batch_count = 0

    try:
        amendements = parse_amendements(zip_file_path)
        table_rows = {
            "amendements": amendements.amendements,
            "amendement_signataires": amendements.signataires,
            "amendement_cosignataires": amendements.cosignataires,
        }
        load_all_tables(
            table_rows=table_rows,
            schemas=AMENDEMENTS_SCHEMAS,
            config=config,
        )
        publish_load_summary_artifact(total_loaded_rows, batch_count)
    finally:
        cleanup_temp_file(zip_file_path)

    logger.info("Finished loading amendements in %d batch(es)", batch_count)


@flow
def amendements_flow() -> None:
    config = get_config()
    zip_file_path = fetch_zip_to_file(config.amendements_url)
    parse_and_load_amendements(zip_file_path, config)


if __name__ == "__main__":
    amendements_flow()
