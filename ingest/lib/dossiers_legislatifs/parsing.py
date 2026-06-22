from typing import Any

from lib.parsing_common import (
    read_json_files_from_zip,
    to_str,
    to_int,
    to_ts,
)
from lib.dossiers_legislatifs.models import (
    DocumentRow,
    DossierParlementaireRow,
    DossierActeLegislatifRow,
    DossiersParseResult,
)


def _extract_documents(zip_bytes: bytes) -> list[DocumentRow]:
    """Extract documents from the zip archive (document folder)"""
    documents: list[DocumentRow] = []

    for payload in read_json_files_from_zip(zip_bytes, prefix="json/document/"):
        document_wrapper = (payload or {}).get("document") or {}
        if not isinstance(document_wrapper, dict):
            continue

        uid = to_str(document_wrapper.get("uid"))
        if not uid:
            continue

        # Extract classification
        classification = document_wrapper.get("classification") or {}
        famille = classification.get("famille") or {}
        type_elem = classification.get("type") or {}
        sous_type = classification.get("sousType") or {}

        # Extract cycle de vie dates
        cycle_de_vie = document_wrapper.get("cycleDeVie") or {}
        chrono = cycle_de_vie.get("chrono") or {}

        # Extract notice
        notice = document_wrapper.get("notice") or {}

        # Extract auteurs
        auteur_ref = None
        auteur_qualite = None
        auteurs = document_wrapper.get("auteurs") or {}
        auteur_elem = auteurs.get("auteur")
        if isinstance(auteur_elem, dict):
            acteur = auteur_elem.get("acteur")
            if isinstance(acteur, dict):
                auteur_ref = to_str(acteur.get("acteurRef"))
                auteur_qualite = to_str(acteur.get("qualite"))

        # Extract imprimerie
        imprimerie = document_wrapper.get("imprimerie") or {}

        # Extract adoption_conforme
        adoption_conforme = notice.get("adoptionConforme")
        if adoption_conforme is not None:
            adoption_conforme = str(adoption_conforme).lower() == "true"

        documents.append(
            DocumentRow(
                uid=uid,
                legislature=to_str(document_wrapper.get("legislature")),
                type_code=to_str(type_elem.get("code")),
                type_libelle=to_str(type_elem.get("libelle")),
                denomination_structurelle=to_str(
                    document_wrapper.get("denominationStructurelle")
                ),
                provenance=to_str(document_wrapper.get("provenance")),
                titre_principal=to_str(
                    document_wrapper.get("titres", {}).get("titrePrincipal")
                ),
                titre_principal_court=to_str(
                    document_wrapper.get("titres", {}).get("titrePrincipalCourt")
                ),
                dossier_ref=to_str(document_wrapper.get("dossierRef")),
                date_creation=to_ts(chrono.get("dateCreation")),
                date_depot=to_ts(chrono.get("dateDepot")),
                date_publication=to_ts(chrono.get("datePublication")),
                date_publication_web=to_ts(chrono.get("datePublicationWeb")),
                famille_depot_code=to_str(famille.get("depot", {}).get("code")),
                famille_depot_libelle=to_str(famille.get("depot", {}).get("libelle")),
                famille_classe_code=to_str(famille.get("classe", {}).get("code")),
                famille_classe_libelle=to_str(famille.get("classe", {}).get("libelle")),
                famille_espece_code=to_str(famille.get("espece", {}).get("code")),
                famille_espece_libelle=to_str(famille.get("espece", {}).get("libelle")),
                type_sous_type_code=to_str(sous_type.get("code")),
                type_sous_type_libelle=to_str(sous_type.get("libelle")),
                num_notice=to_str(notice.get("numNotice")),
                formule=to_str(notice.get("formule")),
                adoption_conforme=adoption_conforme,
                auteur_ref=auteur_ref,
                auteur_qualite=auteur_qualite,
                isbn=to_str(imprimerie.get("ISBN")),
                issn=to_str(imprimerie.get("ISSN")),
                dian=to_str(imprimerie.get("DIAN")),
                nb_page=to_int(imprimerie.get("nbPage")),
            )
        )

    return documents


def _flatten_actes_legislatifs(
    acte: dict[str, Any],
    dossier_uid: str,
    parent_uid: str | None = None,
) -> list[DossierActeLegislatifRow]:
    """
    Recursively flatten nested legislative acts (actes_legislatifs).
    Each acte can contain nested actes_legislatifs.
    """
    rows: list[DossierActeLegislatifRow] = []

    if not isinstance(acte, dict):
        return rows

    # Get the ID for this acte
    acte_uid = to_str(acte.get("uid")) or parent_uid or ""
    if not acte_uid:
        return rows

    # Extract LibelleActe
    libelle_acte = acte.get("libelleActe") or {}

    # Extract vote ref
    vote_ref = (acte.get("voteRefs") or {}).get("voteRef") or ""

    rows.append(
        DossierActeLegislatifRow(
            dossier_uid=dossier_uid,
            acte_uid=acte_uid,
            acte_code=to_str(acte.get("codeActe")),
            acte_libelle_canonique=to_str(libelle_acte.get("nomCanonique")),
            acte_libelle_court=to_str(libelle_acte.get("libelleCourt")),
            organe_ref=to_str(acte.get("organeRef")),
            date_acte=to_ts(acte.get("dateActe")),
            type_acte=to_str(acte.get("@xsi:type")),
            texte_associe=to_str(acte.get("texteAssocie")),
            vote_ref=to_str(vote_ref),
        )
    )

    # Recursively process nested actes_legislatifs
    nested_actes_container = acte.get("actesLegislatifs") or {}
    nested_actes = nested_actes_container.get("acteLegislatif")
    if nested_actes:
        if not isinstance(nested_actes, list):
            nested_actes = [nested_actes]
        for nested_acte in nested_actes:
            rows.extend(_flatten_actes_legislatifs(nested_acte, dossier_uid, acte_uid))

    return rows


def _extract_dossiers_and_actes(
    zip_bytes: bytes,
) -> tuple[list[DossierParlementaireRow], list[DossierActeLegislatifRow]]:
    """Extract parliamentary dossiers and their legislative acts"""
    dossiers: list[DossierParlementaireRow] = []
    actes: list[DossierActeLegislatifRow] = []

    for payload in read_json_files_from_zip(
        zip_bytes, prefix="json/dossierParlementaire/"
    ):
        dossier_wrapper = (payload or {}).get("dossierParlementaire") or {}
        if not isinstance(dossier_wrapper, dict):
            continue

        uid = to_str(dossier_wrapper.get("uid"))
        if not uid:
            continue

        # Extract titre dossier
        titre_dossier_elem = dossier_wrapper.get("titreDossier") or {}

        # Extract procedure
        procedure = dossier_wrapper.get("procedureParlementaire") or {}

        # Extract initiator
        initiateur = dossier_wrapper.get("initiateur") or {}
        initiateur_acteurs = initiateur.get("acteurs")
        initiateur_acteur_ref = None
        initiateur_mandat_ref = None
        if isinstance(initiateur_acteurs, dict):
            initiateur_acteur = initiateur_acteurs.get("acteur")
            if isinstance(initiateur_acteur, dict):
                initiateur_acteur_ref = to_str(initiateur_acteur.get("acteurRef"))
                initiateur_mandat_ref = to_str(initiateur_acteur.get("mandatRef"))

        # Extract initiator organe
        initiateur_organes = initiateur.get("organes")
        initiateur_organe_ref = None
        if isinstance(initiateur_organes, dict):
            initiateur_organe = initiateur_organes.get("organe")
            if isinstance(initiateur_organe, dict):
                organe_ref_elem = initiateur_organe.get("organeRef")
                if isinstance(organe_ref_elem, dict):
                    initiateur_organe_ref = to_str(organe_ref_elem.get("uid"))
                else:
                    initiateur_organe_ref = to_str(organe_ref_elem)

        # Count actes legislatifs
        actes_legislatifs_container = dossier_wrapper.get("actesLegislatifs") or {}
        actes_legislatifs = actes_legislatifs_container.get("acteLegislatif") or []
        if not isinstance(actes_legislatifs, list):
            actes_legislatifs = [actes_legislatifs]
        nombre_actes = len(actes_legislatifs) if actes_legislatifs else 0

        dossiers.append(
            DossierParlementaireRow(
                uid=uid,
                legislature=to_str(dossier_wrapper.get("legislature")),
                titre_dossier=to_str(titre_dossier_elem.get("titre")),
                titre_chemin=to_str(titre_dossier_elem.get("titreChemin")),
                procedure_parlementaire_code=to_str(procedure.get("code")),
                procedure_parlementaire_libelle=to_str(procedure.get("libelle")),
                initiateur_acteur_ref=initiateur_acteur_ref,
                initiateur_mandat_ref=initiateur_mandat_ref,
                initiateur_organe_ref=initiateur_organe_ref,
                nombre_actes_legislatifs=nombre_actes,
            )
        )

        # Flatten and extract all legislative acts
        for acte in actes_legislatifs:
            if isinstance(acte, dict):
                actes.extend(_flatten_actes_legislatifs(acte, uid))

    return dossiers, actes


def parse_dossiers_legislatifs(zip_bytes: bytes) -> DossiersParseResult:
    """Parse legislative dossiers from zip archive"""
    documents = _extract_documents(zip_bytes)
    dossiers, actes = _extract_dossiers_and_actes(zip_bytes)

    return DossiersParseResult(
        documents=documents,
        dossiers_parlementaires=dossiers,
        dossier_actes_legislatifs=actes,
    )
