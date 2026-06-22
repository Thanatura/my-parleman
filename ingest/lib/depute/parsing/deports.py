from lib.depute.models import DeportRow
from lib.parsing_common import read_json_files_from_zip, to_str, to_ts, utc_now


def parse_deports(zip_bytes: bytes) -> list[DeportRow]:
    rows: list[DeportRow] = []
    now = utc_now()

    for payload in read_json_files_from_zip(zip_bytes, prefix="json/deport/"):
        deport = payload["deport"]
        portee = deport.get("portee") or {}
        lecture = deport.get("lecture") or {}
        instance = deport.get("instance") or {}
        cible = deport.get("cible") or {}
        cible_type = cible.get("type") or {}

        rows.append(
            DeportRow(
                uid=to_str(deport.get("uid")),
                legislature=to_str(deport.get("legislature")),
                acteur_ref=to_str(deport.get("refActeur")),
                date_creation=to_ts(deport.get("dateCreation")),
                date_publication=to_ts(deport.get("datePublication")),
                portee_code=to_str(portee.get("code")),
                portee_libelle=to_str(portee.get("libelle")),
                lecture_code=to_str(lecture.get("code")),
                instance_code=to_str(instance.get("code")),
                cible_type_code=to_str(cible_type.get("code")),
                cible_reference_textuelle=to_str(cible.get("referenceTextuelle")),
                ingested_at=now,
            )
        )

    return rows
