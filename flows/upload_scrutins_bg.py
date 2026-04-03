from typing import Sequence

from prefect.artifacts import create_table_artifact

from lib.bq_utils.models import BigQueryRow
from lib.config import ProjectConfig, get_config
from lib.depute.bq_schemas import DEPUTES_SCHEMAS
from lib.depute.models import AdresseRow, ActeurRow, DeportRow, MandatRow, OrganeRow
from lib.depute.parsing import (
    parse_acteurs,
    parse_adresses,
    parse_deports,
    parse_mandats,
    parse_organes,
)
from lib.bq_utils.bq_utils import load_all_tables
from prefect import flow, get_run_logger, task
from prefect.tasks import task_input_hash

from lib.extract import fetch_zip_file


@task(cache_key_fn=task_input_hash, cache_expiration=None)
def fetch_zip(url: str) -> bytes:
    logger = get_run_logger()
    logger.info(f"Downloading {url}")
    content = fetch_zip_file(url)
    logger.info(f"Downloaded {len(content):,} bytes")
    return content

@flow
def scrutin_pipeline():
    config = get_config()
    zip_bytes = fetch_zip(config.scrutins_url)

    


if __name__ == "__main__":
    scrutin_pipeline()
