"""Prefect orchestration for the AN deputes pipeline."""

from lib.constants import BQ_DATASET, DATA_URL, GCP_PROJECT
from lib.models import AdresseRow, ActeurRow, DeportRow, MandatRow, OrganeRow
from lib.parsing import (
    parse_acteurs,
    parse_adresses,
    parse_deports,
    parse_mandats,
    parse_organes,
)
from lib.pipeline_core import fetch_zip_data, load_all_tables
from prefect import flow, get_run_logger, task
from prefect.tasks import task_input_hash


# ---------------------------------------------------------------------------
# Parsing tasks
# ---------------------------------------------------------------------------


@task(cache_key_fn=task_input_hash, cache_expiration=None)
def fetch_zip(url: str) -> bytes:
    logger = get_run_logger()
    logger.info(f"Downloading {url}")
    content = fetch_zip_data(url)
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
) -> None:
    logger = get_run_logger()
    counts = load_all_tables(
        acteurs=acteurs,
        adresses=adresses,
        mandats=mandats,
        organes=organes,
        deports=deports,
        project=GCP_PROJECT,
        dataset=BQ_DATASET,
    )

    for table_name, loaded_count in counts.items():
        logger.info(
            f"Loaded {loaded_count:,} rows into {GCP_PROJECT}.{BQ_DATASET}.{table_name}"
        )

    logger.info("All tables loaded successfully.")


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------


@flow(name="an-deputes-pipeline", log_prints=True)
def an_deputes_pipeline(url: str = DATA_URL) -> None:
    """
    Flux idempotent : téléchargement → parsing → WRITE_TRUNCATE dans BigQuery.
    Relancer le flux à tout moment produit le même état final.
    """
    zip_bytes = fetch_zip(url)
    acteurs = parse_acteurs_table(zip_bytes)
    adresses = parse_adresses_table(zip_bytes)
    mandats = parse_mandats_table(zip_bytes)
    organes = parse_organes_table(zip_bytes)
    deports = parse_deports_table(zip_bytes)
    load_to_bigquery(acteurs, adresses, mandats, organes, deports)


if __name__ == "__main__":
    an_deputes_pipeline()
