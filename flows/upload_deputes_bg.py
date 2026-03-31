"""
Pipeline Prefect — Assemblée Nationale (AMO10)
Télécharge, parse et charge dans BigQuery les députés actifs,
leurs mandats et les organes associés.

Tables BigQuery produites :
  - an.acteurs          (1 ligne par député)
  - an.adresses         (adresses postales & mails)
  - an.mandats          (tous les mandats actifs)
  - an.organes          (organes de tous types)
  - an.deports          (déports / conflits d'intérêts)
"""

import io
import json
import zipfile
from datetime import date, datetime
from typing import Any

import requests
from google.cloud import bigquery
from prefect import flow, get_run_logger, task
from prefect.tasks import task_input_hash

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_URL = (
    "https://data.assemblee-nationale.fr/static/openData/repository/17/amo/deputes_actifs_mandats_actifs_organes/AMO10_deputes_actifs_mandats_actifs_organes.json.zip"
)
GCP_PROJECT = "parleman-491810"
BQ_DATASET = "ParlemAN_tests"


SCHEMA: dict[str, list[bigquery.SchemaField]] = {
    "acteurs": [
        bigquery.SchemaField("uid", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("civilite", "STRING"),
        bigquery.SchemaField("prenom", "STRING"),
        bigquery.SchemaField("nom", "STRING"),
        bigquery.SchemaField("alpha", "STRING"),
        bigquery.SchemaField("trigramme", "STRING"),
        bigquery.SchemaField("date_naissance", "DATE"),
        bigquery.SchemaField("ville_naissance", "STRING"),
        bigquery.SchemaField("departement_naissance", "STRING"),
        bigquery.SchemaField("pays_naissance", "STRING"),
        bigquery.SchemaField("profession_libelle", "STRING"),
        bigquery.SchemaField("profession_categorie", "STRING"),
        bigquery.SchemaField("profession_famille", "STRING"),
        bigquery.SchemaField("uri_hatvp", "STRING"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED"),
    ],
    "adresses": [
        bigquery.SchemaField("uid", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("acteur_uid", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("type_code", "STRING"),
        bigquery.SchemaField("type_libelle", "STRING"),
        bigquery.SchemaField("xsi_type", "STRING"),
        bigquery.SchemaField("intitule", "STRING"),
        bigquery.SchemaField("numero_rue", "STRING"),
        bigquery.SchemaField("nom_rue", "STRING"),
        bigquery.SchemaField("complement", "STRING"),
        bigquery.SchemaField("code_postal", "STRING"),
        bigquery.SchemaField("ville", "STRING"),
        bigquery.SchemaField("val_elec", "STRING"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED"),
    ],
    "mandats": [
        bigquery.SchemaField("uid", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("acteur_ref", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("xsi_type", "STRING"),
        bigquery.SchemaField("legislature", "STRING"),
        bigquery.SchemaField("type_organe", "STRING"),
        bigquery.SchemaField("organe_ref", "STRING"),
        bigquery.SchemaField("date_debut", "DATE"),
        bigquery.SchemaField("date_fin", "DATE"),
        bigquery.SchemaField("date_publication", "DATE"),
        bigquery.SchemaField("preseance", "INTEGER"),
        bigquery.SchemaField("nomin_principale", "BOOLEAN"),
        bigquery.SchemaField("code_qualite", "STRING"),
        bigquery.SchemaField("lib_qualite", "STRING"),
        # Champs MandatParlementaire uniquement
        bigquery.SchemaField("election_departement", "STRING"),
        bigquery.SchemaField("election_num_departement", "STRING"),
        bigquery.SchemaField("election_num_circo", "STRING"),
        bigquery.SchemaField("election_cause_mandat", "STRING"),
        bigquery.SchemaField("mandature_date_prise_fonction", "DATE"),
        bigquery.SchemaField("mandature_cause_fin", "STRING"),
        bigquery.SchemaField("mandature_premiere_election", "BOOLEAN"),
        bigquery.SchemaField("mandature_place_hemicycle", "INTEGER"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED"),
    ],
    "organes": [
        bigquery.SchemaField("uid", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("xsi_type", "STRING"),
        bigquery.SchemaField("code_type", "STRING"),
        bigquery.SchemaField("libelle", "STRING"),
        bigquery.SchemaField("libelle_abrege", "STRING"),
        bigquery.SchemaField("libelle_abrev", "STRING"),
        bigquery.SchemaField("regime", "STRING"),
        bigquery.SchemaField("legislature", "STRING"),
        bigquery.SchemaField("date_debut", "DATE"),
        bigquery.SchemaField("date_fin", "DATE"),
        # CIRCONSCRIPTION
        bigquery.SchemaField("circo_numero", "STRING"),
        bigquery.SchemaField("circo_region_type", "STRING"),
        bigquery.SchemaField("circo_region_libelle", "STRING"),
        bigquery.SchemaField("circo_dep_code", "STRING"),
        bigquery.SchemaField("circo_dep_libelle", "STRING"),
        # GP
        bigquery.SchemaField("gp_couleur", "STRING"),
        bigquery.SchemaField("gp_preseance", "INTEGER"),
        bigquery.SchemaField("gp_position_politique", "STRING"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED"),
    ],
    "deports": [
        bigquery.SchemaField("uid", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("legislature", "STRING"),
        bigquery.SchemaField("acteur_ref", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("date_creation", "TIMESTAMP"),
        bigquery.SchemaField("date_publication", "TIMESTAMP"),
        bigquery.SchemaField("portee_code", "STRING"),
        bigquery.SchemaField("portee_libelle", "STRING"),
        bigquery.SchemaField("lecture_code", "STRING"),
        bigquery.SchemaField("instance_code", "STRING"),
        bigquery.SchemaField("cible_type_code", "STRING"),
        bigquery.SchemaField("cible_reference_textuelle", "STRING"),
        bigquery.SchemaField("ingested_at", "TIMESTAMP", mode="REQUIRED"),
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _str(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _date(val: Any) -> date | None:
    if not val:
        return None
    try:
        return date.fromisoformat(str(val)[:10])
    except ValueError:
        return None


def _ts(val: Any) -> datetime | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except ValueError:
        return None


def _int(val: Any) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _bool(val: Any) -> bool | None:
    if val is None:
        return None
    return str(val).strip() == "1"


def _organe_refs(organes: Any) -> list[str]:
    """Normalize organes.organeRef → list of strings."""
    if not organes:
        return []
    refs = organes.get("organeRef", [])
    if isinstance(refs, str):
        return [refs]
    return refs


# ---------------------------------------------------------------------------
# Parsing tasks
# ---------------------------------------------------------------------------


@task(cache_key_fn=task_input_hash, cache_expiration=None)
def fetch_zip(url: str) -> bytes:
    logger = get_run_logger()
    logger.info(f"Downloading {url}")
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    logger.info(f"Downloaded {len(r.content):,} bytes")
    return r.content


@task
def parse_acteurs(zip_bytes: bytes) -> tuple[list[dict], list[dict], list[dict]]:
    """Parse json/acteur/*.json → (acteurs, adresses, mandats)."""
    logger = get_run_logger()
    now = datetime.utcnow()
    acteurs, adresses, mandats = [], [], []

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        files = [n for n in zf.namelist() if n.startswith("json/acteur/") and n.endswith(".json")]
        logger.info(f"Parsing {len(files)} acteur files")
        for name in files:
            raw = json.loads(zf.read(name))
            a = raw["acteur"]
            uid = a["uid"]["#text"] if isinstance(a["uid"], dict) else a["uid"]

            # ── etatCivil ──────────────────────────────────────────────────
            ident = a.get("etatCivil", {}).get("ident", {}) or {}
            nais = a.get("etatCivil", {}).get("infoNaissance", {}) or {}
            prof = a.get("profession", {}) or {}
            soc = prof.get("socProcINSEE", {}) or {}

            acteurs.append({
                "uid": uid,
                "civilite": _str(ident.get("civ")),
                "prenom": _str(ident.get("prenom")),
                "nom": _str(ident.get("nom")),
                "alpha": _str(ident.get("alpha")),
                "trigramme": _str(ident.get("trigramme")),
                "date_naissance": _date(nais.get("dateNais")),
                "ville_naissance": _str(nais.get("villeNais")),
                "departement_naissance": _str(nais.get("depNais")),
                "pays_naissance": _str(nais.get("paysNais")),
                "profession_libelle": _str(prof.get("libelleCourant")),
                "profession_categorie": _str(soc.get("catSocPro")),
                "profession_famille": _str(soc.get("famSocPro")),
                "uri_hatvp": _str(a.get("uri_hatvp")),
                "ingested_at": now,
            })

            # ── adresses ───────────────────────────────────────────────────
            adr_raw = a.get("adresses", {}) or {}
            adr_list = adr_raw.get("adresse", [])
            if isinstance(adr_list, dict):
                adr_list = [adr_list]
            for adr in (adr_list or []):
                adresses.append({
                    "uid": _str(adr.get("uid")),
                    "acteur_uid": uid,
                    "type_code": _str(adr.get("type")),
                    "type_libelle": _str(adr.get("typeLibelle")),
                    "xsi_type": _str(adr.get("@xsi:type")),
                    "intitule": _str(adr.get("intitule")),
                    "numero_rue": _str(adr.get("numeroRue")),
                    "nom_rue": _str(adr.get("nomRue")),
                    "complement": _str(adr.get("complementAdresse")),
                    "code_postal": _str(adr.get("codePostal")),
                    "ville": _str(adr.get("ville")),
                    "val_elec": _str(adr.get("valElec")),
                    "ingested_at": now,
                })

            # ── mandats ────────────────────────────────────────────────────
            mdt_raw = a.get("mandats", {}) or {}
            mdt_list = mdt_raw.get("mandat", [])
            if isinstance(mdt_list, dict):
                mdt_list = [mdt_list]
            for m in (mdt_list or []):
                infos = m.get("infosQualite", {}) or {}
                # Un mandat peut référencer plusieurs organes (rare) → on explose
                refs = _organe_refs(m.get("organes"))
                if not refs:
                    refs = [None]
                for ref in refs:
                    row = {
                        "uid": _str(m.get("uid")),
                        "acteur_ref": uid,
                        "xsi_type": _str(m.get("@xsi:type")),
                        "legislature": _str(m.get("legislature")),
                        "type_organe": _str(m.get("typeOrgane")),
                        "organe_ref": ref,
                        "date_debut": _date(m.get("dateDebut")),
                        "date_fin": _date(m.get("dateFin")),
                        "date_publication": _date(m.get("datePublication")),
                        "preseance": _int(m.get("preseance")),
                        "nomin_principale": _bool(m.get("nominPrincipale")),
                        "code_qualite": _str(infos.get("codeQualite")),
                        "lib_qualite": _str(infos.get("libQualite")),
                        # MandatParlementaire extras
                        "election_departement": None,
                        "election_num_departement": None,
                        "election_num_circo": None,
                        "election_cause_mandat": None,
                        "mandature_date_prise_fonction": None,
                        "mandature_cause_fin": None,
                        "mandature_premiere_election": None,
                        "mandature_place_hemicycle": None,
                        "ingested_at": now,
                    }
                    if m.get("@xsi:type") == "MandatParlementaire_type":
                        elec = (m.get("election") or {}).get("lieu") or {}
                        mandt = m.get("mandature") or {}
                        row.update({
                            "election_departement": _str(elec.get("departement")),
                            "election_num_departement": _str(elec.get("numDepartement")),
                            "election_num_circo": _str(elec.get("numCirco")),
                            "election_cause_mandat": _str((m.get("election") or {}).get("causeMandat")),
                            "mandature_date_prise_fonction": _date(mandt.get("datePriseFonction")),
                            "mandature_cause_fin": _str(mandt.get("causeFin")),
                            "mandature_premiere_election": _bool(mandt.get("premiereElection")),
                            "mandature_place_hemicycle": _int(mandt.get("placeHemicycle")),
                        })
                    mandats.append(row)

    logger.info(f"Parsed {len(acteurs)} acteurs, {len(adresses)} adresses, {len(mandats)} mandats")
    return acteurs, adresses, mandats


@task
def parse_organes(zip_bytes: bytes) -> list[dict]:
    logger = get_run_logger()
    now = datetime.utcnow()
    organes = []

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        files = [n for n in zf.namelist() if n.startswith("json/organe/") and n.endswith(".json")]
        logger.info(f"Parsing {len(files)} organe files")
        for name in files:
            raw = json.loads(zf.read(name))
            o = raw["organe"]
            vimode = o.get("viMoDe") or {}
            lieu = o.get("lieu") or {}
            region = lieu.get("region") or {}
            dep = lieu.get("departement") or {}

            organes.append({
                "uid": _str(o.get("uid")),
                "xsi_type": _str(o.get("@xsi:type")),
                "code_type": _str(o.get("codeType")),
                "libelle": _str(o.get("libelle")),
                "libelle_abrege": _str(o.get("libelleAbrege")),
                "libelle_abrev": _str(o.get("libelleAbrev")),
                "regime": _str(o.get("regime")),
                "legislature": _str(o.get("legislature")),
                "date_debut": _date(vimode.get("dateDebut")),
                "date_fin": _date(vimode.get("dateFin")),
                # CIRCONSCRIPTION
                "circo_numero": _str(o.get("numero")),
                "circo_region_type": _str(region.get("type")),
                "circo_region_libelle": _str(region.get("libelle")),
                "circo_dep_code": _str(dep.get("code")),
                "circo_dep_libelle": _str(dep.get("libelle")),
                # GP
                "gp_couleur": _str(o.get("couleurAssociee")),
                "gp_preseance": _int(o.get("preseance")),
                "gp_position_politique": _str(o.get("positionPolitique")),
                "ingested_at": now,
            })

    logger.info(f"Parsed {len(organes)} organes")
    return organes


@task
def parse_deports(zip_bytes: bytes) -> list[dict]:
    logger = get_run_logger()
    now = datetime.utcnow()
    deports = []

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        files = [n for n in zf.namelist() if n.startswith("json/deport/") and n.endswith(".json")]
        logger.info(f"Parsing {len(files)} deport files")
        for name in files:
            raw = json.loads(zf.read(name))
            d = raw["deport"]
            portee = d.get("portee") or {}
            lecture = d.get("lecture") or {}
            instance = d.get("instance") or {}
            cible = d.get("cible") or {}
            cible_type = cible.get("type") or {}

            deports.append({
                "uid": _str(d.get("uid")),
                "legislature": _str(d.get("legislature")),
                "acteur_ref": _str(d.get("refActeur")),
                "date_creation": _ts(d.get("dateCreation")),
                "date_publication": _ts(d.get("datePublication")),
                "portee_code": _str(portee.get("code")),
                "portee_libelle": _str(portee.get("libelle")),
                "lecture_code": _str(lecture.get("code")),
                "instance_code": _str(instance.get("code")),
                "cible_type_code": _str(cible_type.get("code")),
                "cible_reference_textuelle": _str(cible.get("referenceTextuelle")),
                "ingested_at": now,
            })

    logger.info(f"Parsed {len(deports)} deports")
    return deports


# ---------------------------------------------------------------------------
# BigQuery tasks
# ---------------------------------------------------------------------------


def _ensure_dataset(client: bigquery.Client) -> None:
    ds_ref = bigquery.Dataset(f"{GCP_PROJECT}.{BQ_DATASET}")
    ds_ref.location = "EU"
    client.create_dataset(ds_ref, exists_ok=True)


def _serialize_for_json(obj: Any) -> Any:
    """Convert date/datetime objects to ISO format strings for JSON serialization."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj


def _load_rows(
    client: bigquery.Client,
    table_name: str,
    rows: list[dict],
) -> None:
    logger = get_run_logger()
    if not rows:
        logger.warning(f"No rows to load for {table_name}, skipping.")
        return

    table_id = f"{GCP_PROJECT}.{BQ_DATASET}.{table_name}"

    # Serialize dates to ISO strings for JSON compatibility
    rows_serialized = [
        {k: _serialize_for_json(v) for k, v in row.items()}
        for row in rows
    ]

    # Truncate + reload (idempotent)
    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA[table_name],
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )
    job = client.load_table_from_json(rows_serialized, table_id, job_config=job_config)
    job.result()  # Wait for completion
    logger.info(f"Loaded {len(rows):,} rows into {table_id}")


@task
def load_to_bigquery(
    acteurs: list[dict],
    adresses: list[dict],
    mandats: list[dict],
    organes: list[dict],
    deports: list[dict],
) -> None:
    logger = get_run_logger()
    client = bigquery.Client(project=GCP_PROJECT)
    _ensure_dataset(client)

    for table, rows in [
        ("acteurs", acteurs),
        ("adresses", adresses),
        ("mandats", mandats),
        ("organes", organes),
        ("deports", deports),
    ]:
        logger.info(f"Loading table: {table} ({len(rows):,} rows)")
        _load_rows(client, table, rows)

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
    acteurs, adresses, mandats = parse_acteurs(zip_bytes)
    organes = parse_organes(zip_bytes)
    deports = parse_deports(zip_bytes)
    load_to_bigquery(acteurs, adresses, mandats, organes, deports)


if __name__ == "__main__":
    an_deputes_pipeline()