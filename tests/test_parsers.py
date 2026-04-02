import io
import json
import zipfile

from lib.depute.models import AdresseRow, ActeurRow, DeportRow, MandatRow, OrganeRow
from lib.depute.parsing import (
    parse_acteurs,
    parse_adresses,
    parse_deports,
    parse_mandats,
    parse_organes,
)


def _sample_zip() -> bytes:
    """Builds a minimal ZIP in memory for testing each parser."""
    acteur_payload = {
        "acteur": {
            "uid": "PA0001",
            "etatCivil": {
                "ident": {
                    "civ": "M.",
                    "prenom": "Jean",
                    "nom": "Dupont",
                    "alpha": "Dupont",
                    "trigramme": "JDU",
                },
                "infoNaissance": {
                    "dateNais": "1980-01-02",
                    "villeNais": "Paris",
                    "depNais": "75",
                    "paysNais": "France",
                },
            },
            "profession": {
                "libelleCourant": "Ingenieur",
                "socProcINSEE": {"catSocPro": "3", "famSocPro": "31"},
            },
            "uri_hatvp": "https://example.org/hatvp/PA0001",
            "adresses": {
                "adresse": {
                    "uid": "ADR0001",
                    "type": "2",
                    "typeLibelle": "Electronique",
                    "@xsi:type": "AdresseType",
                    "intitule": "Mail",
                    "numeroRue": "10",
                    "nomRue": "Rue de Test",
                    "complementAdresse": "Bat A",
                    "codePostal": "75001",
                    "ville": "Paris",
                    "valElec": "jean.dupont@example.org",
                }
            },
            "mandats": {
                "mandat": {
                    "uid": "M0001",
                    "@xsi:type": "MandatParlementaire_type",
                    "legislature": "17",
                    "typeOrgane": "ASSEMBLEE",
                    "organes": {"organeRef": "PO0001"},
                    "dateDebut": "2024-07-01",
                    "dateFin": None,
                    "datePublication": "2024-07-02",
                    "preseance": "1",
                    "nominPrincipale": "1",
                    "infosQualite": {"codeQualite": "M", "libQualite": "Membre"},
                    "election": {
                        "lieu": {
                            "departement": "Paris",
                            "numDepartement": "75",
                            "numCirco": "1",
                        },
                        "causeMandat": "Election",
                    },
                    "mandature": {
                        "datePriseFonction": "2024-07-08",
                        "causeFin": None,
                        "premiereElection": "1",
                        "placeHemicycle": "42",
                    },
                }
            },
        }
    }

    organe_payload = {
        "organe": {
            "uid": "PO0001",
            "@xsi:type": "OrganeParlementaire_Type",
            "codeType": "ASSEMBLEE",
            "libelle": "Assemblee nationale",
            "libelleAbrege": "AN",
            "libelleAbrev": "AN",
            "regime": "V",
            "legislature": "17",
            "viMoDe": {"dateDebut": "2024-07-01", "dateFin": None},
            "lieu": {
                "region": {"type": "REG", "libelle": "Ile-de-France"},
                "departement": {"code": "75", "libelle": "Paris"},
            },
            "numero": "1",
            "couleurAssociee": "#00AAFF",
            "preseance": "1",
            "positionPolitique": "CENTRE",
        }
    }

    deport_payload = {
        "deport": {
            "uid": "D0001",
            "legislature": "17",
            "refActeur": "PA0001",
            "dateCreation": "2024-07-10T10:00:00Z",
            "datePublication": "2024-07-11T10:00:00Z",
            "portee": {"code": "T", "libelle": "Totale"},
            "lecture": {"code": "L1"},
            "instance": {"code": "AN"},
            "cible": {
                "type": {"code": "TEXT"},
                "referenceTextuelle": "Texte de test",
            },
        }
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("json/acteur/PA0001.json", json.dumps(acteur_payload))
        archive.writestr("json/organe/PO0001.json", json.dumps(organe_payload))
        archive.writestr("json/deport/D0001.json", json.dumps(deport_payload))

    return buffer.getvalue()


def test_parse_acteurs_returns_typed_rows() -> None:
    """Verifies that the acteurs parser returns a typed and complete row."""
    rows = parse_acteurs(_sample_zip())
    assert len(rows) == 1
    assert isinstance(rows[0], ActeurRow)
    assert rows[0].uid == "PA0001"


def test_parse_adresses_returns_typed_rows() -> None:
    """Verifies that the adresses parser returns the link to the acteur."""
    rows = parse_adresses(_sample_zip())
    assert len(rows) == 1
    assert isinstance(rows[0], AdresseRow)
    assert rows[0].acteur_uid == "PA0001"


def test_parse_mandats_returns_typed_rows() -> None:
    """Verifies that the mandats parser preserves the organ reference."""
    rows = parse_mandats(_sample_zip())
    assert len(rows) == 1
    assert isinstance(rows[0], MandatRow)
    assert rows[0].organe_ref == "PO0001"


def test_parse_organes_returns_typed_rows() -> None:
    """Verifies that the organes parser returns a typed organ row."""
    rows = parse_organes(_sample_zip())
    assert len(rows) == 1
    assert isinstance(rows[0], OrganeRow)
    assert rows[0].uid == "PO0001"


def test_parse_deports_returns_typed_rows() -> None:
    """Verifies that the deports parser returns the expected acteur reference."""
    rows = parse_deports(_sample_zip())
    assert len(rows) == 1
    assert isinstance(rows[0], DeportRow)
    assert rows[0].acteur_ref == "PA0001"
