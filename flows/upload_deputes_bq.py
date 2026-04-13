from collections.abc import Mapping
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
from lib.bq_utils import load_all_tables
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


@task
def parse_acteurs_table(zip_bytes: bytes) -> list[ActeurRow]:
    logger = get_run_logger()
    rows = parse_acteurs(zip_bytes)
    logger.info(f"Parsed {len(rows)} acteurs")
    return rows


@task
def parse_adresses_table(zip_bytes: bytes) -> list[AdresseRow]:
    logger = get_run_logger()
    rows = parse_adresses(zip_bytes)
    logger.info(f"Parsed {len(rows)} adresses")
    return rows


@task
def parse_mandats_table(zip_bytes: bytes) -> list[MandatRow]:
    logger = get_run_logger()
    rows = parse_mandats(zip_bytes)
    logger.info(f"Parsed {len(rows)} mandats")
    return rows


@task
def parse_organes_table(zip_bytes: bytes) -> list[OrganeRow]:
    logger = get_run_logger()
    rows = parse_organes(zip_bytes)
    logger.info(f"Parsed {len(rows)} organes")
    return rows


@task
def parse_deports_table(zip_bytes: bytes) -> list[DeportRow]:
    logger = get_run_logger()
    rows = parse_deports(zip_bytes)
    logger.info(f"Parsed {len(rows)} deports")
    return rows


@task
def load_to_bigquery(
    acteurs: list[ActeurRow],
    adresses: list[AdresseRow],
    mandats: list[MandatRow],
    organes: list[OrganeRow],
    deports: list[DeportRow],
    config: ProjectConfig,
) -> None:
    table_rows: Mapping[str, Sequence[BigQueryRow]] = {
        "acteurs": acteurs,
        "adresses": adresses,
        "mandats": mandats,
        "organes": organes,
        "deports": deports,
    }
    loaded_rows = load_all_tables(
        table_rows=table_rows,
        schemas=DEPUTES_SCHEMAS,
        config=config,
    )

    create_table_artifact(
        key="bq-load-summary",
        table=[
            {
                "table": table_name,
                "loaded_rows": loaded_rows[table_name],
            }
            for table_name in table_rows
        ],
        description="depute load summary by table",
    )


@flow(name="an-deputes-pipeline", log_prints=True)
def an_deputes_flow() -> None:
    config = get_config()
    zip_bytes = fetch_zip(config.deputes_url)
    acteurs = parse_acteurs_table(zip_bytes)
    adresses = parse_adresses_table(zip_bytes)
    mandats = parse_mandats_table(zip_bytes)
    organes = parse_organes_table(zip_bytes)
    deports = parse_deports_table(zip_bytes)
    load_to_bigquery(acteurs, adresses, mandats, organes, deports, config)


if __name__ == "__main__":
    an_deputes_flow()
