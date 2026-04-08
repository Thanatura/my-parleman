from typing import Any

import json
from lib.parsing_common import (
    to_str,
    to_date,
)
from lib.extract import extract_zip_contents_with_dossier
from lib.amendements.models import (
    AmendementRow,
    AmendementSignataireRow,
    AmendementsCosignataireRow,
    AmendementParseResult,
)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def parse_amendements(zip_bytes: bytes) -> AmendementParseResult:
    """Parse amendments from zip archive"""
    amendements: list[AmendementRow] = []
    signataires: list[AmendementSignataireRow] = []
    cosignataires: list[AmendementsCosignataireRow] = []

    for dossier_id, file_content in extract_zip_contents_with_dossier(zip_bytes):
        try:
            payload = json.loads(file_content)
        except json.JSONDecodeError:
            continue
            
        amendement_wrapper = (payload or {}).get("amendement")
        if not isinstance(amendement_wrapper, dict):
            continue

        uid = to_str(amendement_wrapper.get("uid"))
        if not uid:
            continue

        # Extract identification
        identification = amendement_wrapper.get("identification") or {}

        # Extract pointeur fragment texte (text targeting)
        pointeur = amendement_wrapper.get("pointeurFragmentTexte") or {}
        division = pointeur.get("division") or {}

        # Extract corps (body)
        corps = amendement_wrapper.get("corps") or {}
        contenu_auteur = corps.get("contenuAuteur") or {}

        # Extract cycle de vie (lifecycle)
        cycle_vie = amendement_wrapper.get("cycleDeVie") or {}
        etat_elem = cycle_vie.get("etatDesTraitements", {})
        etat = etat_elem.get("etat") or {}
        sous_etat = etat_elem.get("sousEtat") or {}

        # Extract signataires (authors/signatories)
        sig_container = amendement_wrapper.get("signataires") or {}

        # Parse main author
        auteur_elem = sig_container.get("auteur")
        auteur_type = None
        auteur_acteur_ref = None
        auteur_groupe_ref = None

        if isinstance(auteur_elem, dict):
            auteur_type = to_str(auteur_elem.get("typeAuteur"))
            auteur_acteur_ref = to_str(auteur_elem.get("acteurRef"))
            auteur_groupe_ref = to_str(auteur_elem.get("groupePolitiqueRef"))

            # Add author to signataires table
            if auteur_acteur_ref:
                signataires.append(
                    AmendementSignataireRow(
                        amendement_uid=uid,
                        acteur_ref=auteur_acteur_ref,
                        type_auteur=auteur_type,
                        groupe_politique_ref=auteur_groupe_ref,
                        ordre_presentation=0,
                    )
                )

        # Parse co-signers
        cosig_container = sig_container.get("cosignataires")
        if isinstance(cosig_container, dict):
            cosig_refs = cosig_container.get("acteurRef", [])
            if not isinstance(cosig_refs, list):
                cosig_refs = [cosig_refs] if cosig_refs else []

            for idx, cosig_ref in enumerate(cosig_refs, start=1):
                cosig_ref_str = to_str(cosig_ref)
                if cosig_ref_str:
                    cosignataires.append(
                        AmendementsCosignataireRow(
                            amendement_uid=uid,
                            cosignataire_acteur_ref=cosig_ref_str,
                            ordre_presentation=idx,
                        )
                    )

        # Create amendment row
        amendements.append(
            AmendementRow(
                uid=uid,
                legislature=to_str(amendement_wrapper.get("legislature")),
                numero_long=to_str(identification.get("numeroLong")),
                numero_ordre_depot=to_str(identification.get("numeroOrdreDepot")),
                prefixe_organe_examen=to_str(identification.get("prefixeOrganeExamen")),
                examen_ref=to_str(amendement_wrapper.get("examenRef")),
                texte_legislatif_ref=to_str(
                    amendement_wrapper.get("texteLegislatifRef")
                ),
                dossier_legislatif_ref=to_str(dossier_id),
                division_titre=to_str(division.get("titre")),
                article_designation_courte=to_str(
                    division.get("articleDesignationCourte")
                ),
                division_type=to_str(division.get("type")),
                dispositif=to_str(contenu_auteur.get("dispositif")),
                expose_sommaire=to_str(contenu_auteur.get("exposeSommaire")),
                date_depot=to_date(cycle_vie.get("dateDepot")),
                date_publication=to_date(cycle_vie.get("datePublication")),
                etat_code=to_str(etat.get("code")),
                etat_libelle=to_str(etat.get("libelle")),
                sous_etat_code=to_str(sous_etat.get("code")),
                sous_etat_libelle=to_str(sous_etat.get("libelle")),
                sort=to_str(cycle_vie.get("sort")),
                auteur_type=auteur_type,
                auteur_acteur_ref=auteur_acteur_ref,
                auteur_groupe_politique_ref=auteur_groupe_ref,
            )
        )

    return AmendementParseResult(
        amendements=amendements,
        signataires=signataires,
        cosignataires=cosignataires,
    )
