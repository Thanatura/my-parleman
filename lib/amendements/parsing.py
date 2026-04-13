from collections.abc import Iterable, Iterator
from itertools import chain, tee
from typing import Any

import json
from lib.parsing_common import (
    to_str,
    to_date,
)
from lib.extract import extract_zip_file_contents_with_folder
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


def _get_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _load_amendement_wrapper(file_content: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(file_content)
    except json.JSONDecodeError:
        return None

    amendement_wrapper = (payload or {}).get("amendement")
    if not isinstance(amendement_wrapper, dict):
        return None

    uid = to_str(amendement_wrapper.get("uid"))
    if not uid:
        return None

    return amendement_wrapper


def _parse_auteur(
    uid: str,
    sig_container: dict[str, Any],
) -> tuple[
    str | None,
    str | None,
    str | None,
    list[AmendementSignataireRow],
]:
    auteur_elem = sig_container.get("auteur")
    auteur_type = None
    auteur_acteur_ref = None
    auteur_groupe_ref = None
    signataires: list[AmendementSignataireRow] = []

    if isinstance(auteur_elem, dict):
        auteur_type = to_str(auteur_elem.get("typeAuteur"))
        auteur_acteur_ref = to_str(auteur_elem.get("acteurRef"))
        auteur_groupe_ref = to_str(auteur_elem.get("groupePolitiqueRef"))

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

    return auteur_type, auteur_acteur_ref, auteur_groupe_ref, signataires


def _parse_cosignataires(
    uid: str,
    sig_container: dict[str, Any],
) -> list[AmendementsCosignataireRow]:
    cosignataires: list[AmendementsCosignataireRow] = []
    cosig_container = sig_container.get("cosignataires")

    if isinstance(cosig_container, dict):
        cosig_refs = _as_list(cosig_container.get("acteurRef"))

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

    return cosignataires


def _build_amendement_row(
    uid: str,
    dossier_id: str,
    amendement_wrapper: dict[str, Any],
    identification: dict[str, Any],
    division: dict[str, Any],
    contenu_auteur: dict[str, Any],
    cycle_vie: dict[str, Any],
    auteur_type: str | None,
    auteur_acteur_ref: str | None,
    auteur_groupe_ref: str | None,
) -> AmendementRow:
    etat_elem = _get_dict(cycle_vie.get("etatDesTraitements"))
    etat = _get_dict(etat_elem.get("etat"))
    sous_etat = _get_dict(etat_elem.get("sousEtat"))

    return AmendementRow(
        uid=uid,
        legislature=to_str(amendement_wrapper.get("legislature")),
        numero_long=to_str(identification.get("numeroLong")),
        numero_ordre_depot=to_str(identification.get("numeroOrdreDepot")),
        prefixe_organe_examen=to_str(identification.get("prefixeOrganeExamen")),
        examen_ref=to_str(amendement_wrapper.get("examenRef")),
        texte_legislatif_ref=to_str(amendement_wrapper.get("texteLegislatifRef")),
        dossier_legislatif_ref=to_str(dossier_id),
        division_titre=to_str(division.get("titre")),
        article_designation_courte=to_str(division.get("articleDesignationCourte")),
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


def _parse_single_amendement(
    dossier_id: str,
    file_content: str,
) -> tuple[
    AmendementRow | None,
    list[AmendementSignataireRow],
    list[AmendementsCosignataireRow],
]:
    amendement_wrapper = _load_amendement_wrapper(file_content)
    if amendement_wrapper is None:
        return None, [], []

    uid = to_str(amendement_wrapper.get("uid")) or ""
    identification = _get_dict(amendement_wrapper.get("identification"))
    pointeur = _get_dict(amendement_wrapper.get("pointeurFragmentTexte"))
    division = _get_dict(pointeur.get("division"))
    corps = _get_dict(amendement_wrapper.get("corps"))
    contenu_auteur = _get_dict(corps.get("contenuAuteur"))
    cycle_vie = _get_dict(amendement_wrapper.get("cycleDeVie"))
    sig_container = _get_dict(amendement_wrapper.get("signataires"))

    auteur_type, auteur_acteur_ref, auteur_groupe_ref, signataires = _parse_auteur(
        uid=uid,
        sig_container=sig_container,
    )
    cosignataires = _parse_cosignataires(uid=uid, sig_container=sig_container)

    amendement = _build_amendement_row(
        uid=uid,
        dossier_id=dossier_id,
        amendement_wrapper=amendement_wrapper,
        identification=identification,
        division=division,
        contenu_auteur=contenu_auteur,
        cycle_vie=cycle_vie,
        auteur_type=auteur_type,
        auteur_acteur_ref=auteur_acteur_ref,
        auteur_groupe_ref=auteur_groupe_ref,
    )

    return amendement, signataires, cosignataires


def _parse_batches_from_entries(
    entries: Iterable[tuple[str, str]],
    batch_size: int,
) -> Iterator[AmendementParseResult]:
    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")

    amendements: list[AmendementRow] = []
    signataires: list[AmendementSignataireRow] = []
    cosignataires: list[AmendementsCosignataireRow] = []

    for dossier_id, file_content in entries:
        amendement, parsed_signataires, parsed_cosignataires = _parse_single_amendement(
            dossier_id,
            file_content,
        )
        if amendement is None:
            continue

        amendements.append(amendement)
        signataires.extend(parsed_signataires)
        cosignataires.extend(parsed_cosignataires)

        if len(amendements) >= batch_size:
            yield AmendementParseResult(
                amendements=iter(amendements),
                signataires=iter(signataires),
                cosignataires=iter(cosignataires),
            )
            amendements = []
            signataires = []
            cosignataires = []

    if amendements or signataires or cosignataires:
        yield AmendementParseResult(
            amendements=iter(amendements),
            signataires=iter(signataires),
            cosignataires=iter(cosignataires),
        )


def _parse_amendements_batches_from_file(
    zip_file_path: str,
    batch_size: int = 10_000,
) -> Iterator[AmendementParseResult]:
    return _parse_batches_from_entries(
        entries=extract_zip_file_contents_with_folder(zip_file_path),
        batch_size=batch_size,
    )


def parse_amendements(zip_file_path: str) -> AmendementParseResult:
    """Parse amendments from zip archive"""
    batches = _parse_amendements_batches_from_file(zip_file_path, batch_size=10_000)
    batches_for_amendements, batches_for_signataires, batches_for_cosignataires = tee(
        batches,
        3,
    )

    return AmendementParseResult(
        amendements=chain.from_iterable(
            batch.amendements for batch in batches_for_amendements
        ),
        signataires=chain.from_iterable(
            batch.signataires for batch in batches_for_signataires
        ),
        cosignataires=chain.from_iterable(
            batch.cosignataires for batch in batches_for_cosignataires
        ),
    )
