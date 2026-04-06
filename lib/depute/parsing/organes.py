from lib.depute.models import OrganeRow
from lib.parsing_common import (
    read_json_files_from_zip,
    to_date,
    to_int,
    to_str,
    utc_now,
)


def parse_organes(zip_bytes: bytes) -> list[OrganeRow]:
    rows: list[OrganeRow] = []
    now = utc_now()

    for payload in read_json_files_from_zip(zip_bytes, prefix="json/organe/"):
        organe = payload["organe"]
        vimode = organe.get("viMoDe") or {}
        lieu = organe.get("lieu") or {}
        region = lieu.get("region") or {}
        departement = lieu.get("departement") or {}

        rows.append(
            OrganeRow(
                uid=to_str(organe.get("uid")),
                xsi_type=to_str(organe.get("@xsi:type")),
                code_type=to_str(organe.get("codeType")),
                libelle=to_str(organe.get("libelle")),
                libelle_abrege=to_str(organe.get("libelleAbrege")),
                libelle_abrev=to_str(organe.get("libelleAbrev")),
                regime=to_str(organe.get("regime")),
                legislature=to_str(organe.get("legislature")),
                date_debut=to_date(vimode.get("dateDebut")),
                date_fin=to_date(vimode.get("dateFin")),
                circo_numero=to_str(organe.get("numero")),
                circo_region_type=to_str(region.get("type")),
                circo_region_libelle=to_str(region.get("libelle")),
                circo_dep_code=to_str(departement.get("code")),
                circo_dep_libelle=to_str(departement.get("libelle")),
                gp_couleur=to_str(organe.get("couleurAssociee")),
                gp_preseance=to_int(organe.get("preseance")),
                gp_position_politique=to_str(organe.get("positionPolitique")),
                ingested_at=now,
            )
        )

    return rows
