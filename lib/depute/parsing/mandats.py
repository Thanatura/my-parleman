from lib.depute.models import MandatRow
from lib.depute.parsing.acteurs import _acteur_node, _acteur_uid
from lib.parsing_common import (
    organe_refs,
    read_json_files_from_zip,
    to_bool,
    to_date,
    to_int,
    to_str,
    utc_now,
)


def parse_mandats(zip_bytes: bytes) -> list[MandatRow]:
    rows: list[MandatRow] = []
    now = utc_now()

    for payload in read_json_files_from_zip(zip_bytes, prefix="json/acteur/"):
        acteur = _acteur_node(payload)
        acteur_uid = _acteur_uid(acteur)

        mandats = (acteur.get("mandats", {}) or {}).get("mandat", [])
        if isinstance(mandats, dict):
            mandats = [mandats]

        for mandat in mandats or []:
            infos = mandat.get("infosQualite", {}) or {}
            refs = organe_refs(mandat.get("organes")) or [None]

            for ref in refs:
                row = MandatRow(
                    uid=to_str(mandat.get("uid")),
                    acteur_ref=acteur_uid,
                    xsi_type=to_str(mandat.get("@xsi:type")),
                    legislature=to_str(mandat.get("legislature")),
                    type_organe=to_str(mandat.get("typeOrgane")),
                    organe_ref=ref,
                    date_debut=to_date(mandat.get("dateDebut")),
                    date_fin=to_date(mandat.get("dateFin")),
                    date_publication=to_date(mandat.get("datePublication")),
                    preseance=to_int(mandat.get("preseance")),
                    nomin_principale=to_bool(mandat.get("nominPrincipale")),
                    code_qualite=to_str(infos.get("codeQualite")),
                    lib_qualite=to_str(infos.get("libQualite")),
                    election_departement=None,
                    election_num_departement=None,
                    election_num_circo=None,
                    election_cause_mandat=None,
                    mandature_date_prise_fonction=None,
                    mandature_cause_fin=None,
                    mandature_premiere_election=None,
                    mandature_place_hemicycle=None,
                    ingested_at=now,
                )

                if mandat.get("@xsi:type") == "MandatParlementaire_type":
                    election = (mandat.get("election") or {}).get("lieu") or {}
                    mandature = mandat.get("mandature") or {}
                    row.election_departement = to_str(election.get("departement"))
                    row.election_num_departement = to_str(
                        election.get("numDepartement")
                    )
                    row.election_num_circo = to_str(election.get("numCirco"))
                    row.election_cause_mandat = to_str(
                        (mandat.get("election") or {}).get("causeMandat")
                    )
                    row.mandature_date_prise_fonction = to_date(
                        mandature.get("datePriseFonction")
                    )
                    row.mandature_cause_fin = to_str(mandature.get("causeFin"))
                    row.mandature_premiere_election = to_bool(
                        mandature.get("premiereElection")
                    )
                    row.mandature_place_hemicycle = to_int(
                        mandature.get("placeHemicycle")
                    )

                rows.append(row)

    return rows
