from typing import Any

from lib.parsing_common import read_json_files_from_zip, to_date, to_int, to_str
from lib.scrutins.models import (
    ScrutinGroupeVoteRow,
    ScrutinParseResult,
    ScrutinRow,
    ScrutinVoteIndividuelRow,
)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _to_bool(value: Any) -> bool | None:
    text = to_str(value)
    if text is None:
        return None
    lowered = text.lower()
    if lowered in {"true", "1"}:
        return True
    if lowered in {"false", "0"}:
        return False
    return None


def _extract_votants(container: Any) -> list[dict[str, Any]]:
    if not container:
        return []
    if isinstance(container, dict) and "votant" in container:
        candidates = _as_list(container.get("votant"))
    else:
        candidates = _as_list(container)
    return [candidate for candidate in candidates if isinstance(candidate, dict)]


def _build_individual_votes(
    *,
    scrutin_uid: str,
    groupe_organe_ref: str | None,
    position_vote: str,
    container: Any,
    source: str,
) -> list[ScrutinVoteIndividuelRow]:
    rows: list[ScrutinVoteIndividuelRow] = []
    for votant in _extract_votants(container):
        rows.append(
            ScrutinVoteIndividuelRow(
                scrutin_uid=scrutin_uid,
                groupe_organe_ref=groupe_organe_ref,
                position_vote=position_vote,
                acteur_ref=to_str(votant.get("acteurRef")) or "",
                mandat_ref=to_str(votant.get("mandatRef")),
                par_delegation=_to_bool(votant.get("parDelegation")),
                num_place=to_str(votant.get("numPlace")),
                cause_position_vote=to_str(votant.get("causePositionVote")),
                source=source,
            )
        )
    return rows


def parse_scrutins(zip_bytes: bytes) -> ScrutinParseResult:
    scrutins: list[ScrutinRow] = []
    groupes_votes: list[ScrutinGroupeVoteRow] = []
    votes_individuels: list[ScrutinVoteIndividuelRow] = []

    for payload in read_json_files_from_zip(zip_bytes, prefix="json/"):
        scrutin = (payload or {}).get("scrutin") or {}
        if not isinstance(scrutin, dict):
            continue

        uid = to_str(scrutin.get("uid"))
        if not uid:
            continue

        type_vote = scrutin.get("typeVote") or {}
        sort = scrutin.get("sort") or {}
        demandeur = scrutin.get("demandeur") or {}
        objet = scrutin.get("objet") or {}
        synthese_vote = scrutin.get("syntheseVote") or {}
        synthese_decompte = synthese_vote.get("decompte") or {}

        scrutins.append(
            ScrutinRow(
                uid=uid,
                numero=to_str(scrutin.get("numero")),
                legislature=to_str(scrutin.get("legislature")),
                organe_ref=to_str(scrutin.get("organeRef")),
                session_ref=to_str(scrutin.get("sessionRef")),
                seance_ref=to_str(scrutin.get("seanceRef")),
                date_scrutin=to_date(scrutin.get("dateScrutin")),
                quantieme_jour_seance=to_int(scrutin.get("quantiemeJourSeance")),
                type_vote_code=to_str(type_vote.get("codeTypeVote")),
                type_vote_libelle=to_str(type_vote.get("libelleTypeVote")),
                type_majorite=to_str(type_vote.get("typeMajorite")),
                sort_code=to_str(sort.get("code")),
                sort_libelle=to_str(sort.get("libelle")),
                titre=to_str(scrutin.get("titre")),
                demandeur_texte=to_str(demandeur.get("texte")),
                demandeur_reference_legislative=to_str(
                    demandeur.get("referenceLegislative")
                ),
                objet_libelle=to_str(objet.get("libelle")),
                objet_dossier_legislatif=to_str(objet.get("dossierLegislatif")),
                objet_reference_legislative=to_str(objet.get("referenceLegislative")),
                mode_publication_votes=to_str(scrutin.get("modePublicationDesVotes")),
                lieu_vote=to_str(scrutin.get("lieuVote")),
                synthese_nombre_votants=to_int(synthese_vote.get("nombreVotants")),
                synthese_suffrages_exprimes=to_int(
                    synthese_vote.get("suffragesExprimes")
                ),
                synthese_nbr_suffrages_requis=to_int(
                    synthese_vote.get("nbrSuffragesRequis")
                ),
                synthese_annonce=to_str(synthese_vote.get("annonce")),
                synthese_non_votants=to_int(synthese_decompte.get("nonVotants")),
                synthese_pour=to_int(synthese_decompte.get("pour")),
                synthese_contre=to_int(synthese_decompte.get("contre")),
                synthese_abstentions=to_int(synthese_decompte.get("abstentions")),
                synthese_non_votants_volontaires=to_int(
                    synthese_decompte.get("nonVotantsVolontaires")
                ),
            )
        )

        ventilation_organe = (scrutin.get("ventilationVotes") or {}).get("organe") or {}
        organe_ref_assemblee = to_str(ventilation_organe.get("organeRef"))
        groupes = _as_list(((ventilation_organe.get("groupes") or {}).get("groupe")))

        for groupe in groupes:
            if not isinstance(groupe, dict):
                continue

            groupe_organe_ref = to_str(groupe.get("organeRef"))
            vote = groupe.get("vote") or {}
            decompte_voix = vote.get("decompteVoix") or {}

            groupes_votes.append(
                ScrutinGroupeVoteRow(
                    scrutin_uid=uid,
                    organe_ref_assemblee=organe_ref_assemblee,
                    groupe_organe_ref=groupe_organe_ref,
                    nombre_membres_groupe=to_int(groupe.get("nombreMembresGroupe")),
                    position_majoritaire=to_str(vote.get("positionMajoritaire")),
                    non_votants=to_int(decompte_voix.get("nonVotants")),
                    pour=to_int(decompte_voix.get("pour")),
                    contre=to_int(decompte_voix.get("contre")),
                    abstentions=to_int(decompte_voix.get("abstentions")),
                    non_votants_volontaires=to_int(
                        decompte_voix.get("nonVotantsVolontaires")
                    ),
                )
            )

            decompte_nominatif = vote.get("decompteNominatif") or {}
            votes_individuels.extend(
                _build_individual_votes(
                    scrutin_uid=uid,
                    groupe_organe_ref=groupe_organe_ref,
                    position_vote="pour",
                    container=decompte_nominatif.get("pours"),
                    source="ventilation",
                )
            )
            votes_individuels.extend(
                _build_individual_votes(
                    scrutin_uid=uid,
                    groupe_organe_ref=groupe_organe_ref,
                    position_vote="contre",
                    container=decompte_nominatif.get("contres"),
                    source="ventilation",
                )
            )
            votes_individuels.extend(
                _build_individual_votes(
                    scrutin_uid=uid,
                    groupe_organe_ref=groupe_organe_ref,
                    position_vote="abstention",
                    container=decompte_nominatif.get("abstentions"),
                    source="ventilation",
                )
            )
            votes_individuels.extend(
                _build_individual_votes(
                    scrutin_uid=uid,
                    groupe_organe_ref=groupe_organe_ref,
                    position_vote="non_votant",
                    container=decompte_nominatif.get("nonVotants"),
                    source="ventilation",
                )
            )

        mise_au_point = scrutin.get("miseAuPoint") or {}
        votes_individuels.extend(
            _build_individual_votes(
                scrutin_uid=uid,
                groupe_organe_ref=None,
                position_vote="pour",
                container=mise_au_point.get("pours"),
                source="mise_au_point",
            )
        )
        votes_individuels.extend(
            _build_individual_votes(
                scrutin_uid=uid,
                groupe_organe_ref=None,
                position_vote="contre",
                container=mise_au_point.get("contres"),
                source="mise_au_point",
            )
        )
        votes_individuels.extend(
            _build_individual_votes(
                scrutin_uid=uid,
                groupe_organe_ref=None,
                position_vote="abstention",
                container=mise_au_point.get("abstentions"),
                source="mise_au_point",
            )
        )
        votes_individuels.extend(
            _build_individual_votes(
                scrutin_uid=uid,
                groupe_organe_ref=None,
                position_vote="non_votant",
                container=mise_au_point.get("nonVotants"),
                source="mise_au_point",
            )
        )

    return ScrutinParseResult(
        scrutins=scrutins,
        groupes_votes=groupes_votes,
        votes_individuels=votes_individuels,
    )
