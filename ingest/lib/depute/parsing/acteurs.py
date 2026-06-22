from typing import Any

from lib.depute.models import ActeurRow
from lib.parsing_common import read_json_files_from_zip, to_date, to_str, utc_now


def _acteur_node(raw_payload: dict[str, Any]) -> dict[str, Any]:
    acteur = raw_payload["acteur"]
    if not isinstance(acteur, dict):
        raise ValueError(f"Expected 'acteur' to be a dict, got {type(acteur)}")
    return acteur


def _acteur_uid(acteur: dict[str, Any]) -> str:
    uid = acteur["uid"]
    if isinstance(uid, dict):
        extracted_uid = uid["#text"]
        if not isinstance(extracted_uid, str):
            raise ValueError(
                f"Expected 'uid.#text' to be a str, got {type(extracted_uid)}"
            )
        return extracted_uid
    elif isinstance(uid, str):
        return uid
    raise ValueError(f"Expected 'uid' to be a str or dict, got {type(uid)}")


def parse_acteurs(zip_bytes: bytes) -> list[ActeurRow]:
    rows: list[ActeurRow] = []
    now = utc_now()

    for payload in read_json_files_from_zip(zip_bytes, prefix="json/acteur/"):
        acteur = _acteur_node(payload)
        ident = acteur.get("etatCivil", {}).get("ident", {}) or {}
        naissance = acteur.get("etatCivil", {}).get("infoNaissance", {}) or {}
        profession = acteur.get("profession", {}) or {}
        soc = profession.get("socProcINSEE", {}) or {}

        rows.append(
            ActeurRow(
                uid=_acteur_uid(acteur),
                civilite=to_str(ident.get("civ")),
                prenom=to_str(ident.get("prenom")),
                nom=to_str(ident.get("nom")),
                alpha=to_str(ident.get("alpha")),
                trigramme=to_str(ident.get("trigramme")),
                date_naissance=to_date(naissance.get("dateNais")),
                ville_naissance=to_str(naissance.get("villeNais")),
                departement_naissance=to_str(naissance.get("depNais")),
                pays_naissance=to_str(naissance.get("paysNais")),
                profession_libelle=to_str(profession.get("libelleCourant")),
                profession_categorie=to_str(soc.get("catSocPro")),
                profession_famille=to_str(soc.get("famSocPro")),
                uri_hatvp=to_str(acteur.get("uri_hatvp")),
                ingested_at=now,
            )
        )

    return rows
