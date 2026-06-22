from lib.depute.models import AdresseRow
from lib.depute.parsing.acteurs import _acteur_node, _acteur_uid
from lib.parsing_common import read_json_files_from_zip, to_str, utc_now


def parse_adresses(zip_bytes: bytes) -> list[AdresseRow]:
    rows: list[AdresseRow] = []
    now = utc_now()

    for payload in read_json_files_from_zip(zip_bytes, prefix="json/acteur/"):
        acteur = _acteur_node(payload)
        uid = _acteur_uid(acteur)

        adresses = (acteur.get("adresses", {}) or {}).get("adresse", [])
        if isinstance(adresses, dict):
            adresses = [adresses]

        for adresse in adresses or []:
            rows.append(
                AdresseRow(
                    uid=to_str(adresse.get("uid")),
                    acteur_uid=uid,
                    type_code=to_str(adresse.get("type")),
                    type_libelle=to_str(adresse.get("typeLibelle")),
                    xsi_type=to_str(adresse.get("@xsi:type")),
                    intitule=to_str(adresse.get("intitule")),
                    numero_rue=to_str(adresse.get("numeroRue")),
                    nom_rue=to_str(adresse.get("nomRue")),
                    complement=to_str(adresse.get("complementAdresse")),
                    code_postal=to_str(adresse.get("codePostal")),
                    ville=to_str(adresse.get("ville")),
                    val_elec=to_str(adresse.get("valElec")),
                    ingested_at=now,
                )
            )

    return rows
