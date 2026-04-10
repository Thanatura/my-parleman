import json
import zipfile
from tempfile import NamedTemporaryFile
from pathlib import Path

from lib.amendements.parsing import _parse_single_amendement, parse_amendements


def _sample_amendement_payload() -> str:
    return json.dumps(
        {
            "amendement": {
                "uid": "AMDT0001",
                "legislature": "17",
                "identification": {
                    "numeroLong": "1234",
                    "numeroOrdreDepot": "1",
                    "prefixeOrganeExamen": "AN",
                },
                "examenRef": "EXAM-1",
                "texteLegislatifRef": "TEXTE-1",
                "pointeurFragmentTexte": {
                    "division": {
                        "titre": "Titre",
                        "articleDesignationCourte": "Art. 1",
                        "type": "article",
                    }
                },
                "corps": {
                    "contenuAuteur": {
                        "dispositif": "Modifier",
                        "exposeSommaire": "Résumé",
                    }
                },
                "cycleDeVie": {
                    "dateDepot": "2024-07-01",
                    "datePublication": "2024-07-02",
                    "sort": "adopté",
                    "etatDesTraitements": {
                        "etat": {"code": "DEP", "libelle": "Déposé"},
                        "sousEtat": {"code": "PUB", "libelle": "Publié"},
                    },
                },
                "signataires": {
                    "auteur": {
                        "typeAuteur": "DEPUTE",
                        "acteurRef": "PA0001",
                        "groupePolitiqueRef": "GP0001",
                    },
                    "cosignataires": {"acteurRef": ["PA0002", None, "PA0003"]},
                },
            }
        }
    )


def test_parse_single_amendement_extracts_rows() -> None:
    amendement, signataires, cosignataires = _parse_single_amendement(
        dossier_id="DOSSIER-1",
        file_content=_sample_amendement_payload(),
    )

    assert amendement is not None
    assert amendement.uid == "AMDT0001"
    assert amendement.dossier_legislatif_ref == "DOSSIER-1"
    assert amendement.division_titre == "Titre"
    assert amendement.auteur_acteur_ref == "PA0001"

    assert [row.acteur_ref for row in signataires] == ["PA0001"]
    assert [row.ordre_presentation for row in cosignataires] == [1, 3]
    assert [row.cosignataire_acteur_ref for row in cosignataires] == [
        "PA0002",
        "PA0003",
    ]


def test_parse_amendements_reads_zip() -> None:
    with NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
        archive_path = Path(temp_file.name)

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "json/amendement/DOSSIER-1.json",
                _sample_amendement_payload(),
            )

        result = parse_amendements(str(archive_path))

        amendements = list(result.amendements)
        signataires = list(result.signataires)
        cosignataires = list(result.cosignataires)

        assert len(amendements) == 1
        assert amendements[0].uid == "AMDT0001"
        assert len(signataires) == 1
        assert len(cosignataires) == 2
