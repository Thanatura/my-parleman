from dataclasses import dataclass
from datetime import date

from lib.bq_utils.models import BigQueryRow


@dataclass
class ScrutinRow(BigQueryRow):
    uid: str

    numero: str | None
    legislature: str | None
    organe_ref: str | None
    session_ref: str | None
    seance_ref: str | None
    date_scrutin: date | None
    quantieme_jour_seance: int | None

    type_vote_code: str | None
    type_vote_libelle: str | None
    type_majorite: str | None

    sort_code: str | None
    sort_libelle: str | None

    titre: str | None
    demandeur_texte: str | None
    demandeur_reference_legislative: str | None
    objet_libelle: str | None
    objet_dossier_legislatif: str | None
    objet_reference_legislative: str | None

    mode_publication_votes: str | None
    lieu_vote: str | None

    synthese_nombre_votants: int | None
    synthese_suffrages_exprimes: int | None
    synthese_nbr_suffrages_requis: int | None
    synthese_annonce: str | None
    synthese_non_votants: int | None
    synthese_pour: int | None
    synthese_contre: int | None
    synthese_abstentions: int | None
    synthese_non_votants_volontaires: int | None


@dataclass
class ScrutinGroupeVoteRow(BigQueryRow):
    scrutin_uid: str
    organe_ref_assemblee: str | None
    groupe_organe_ref: str | None
    nombre_membres_groupe: int | None
    position_majoritaire: str | None

    non_votants: int | None
    pour: int | None
    contre: int | None
    abstentions: int | None
    non_votants_volontaires: int | None


@dataclass
class ScrutinVoteIndividuelRow(BigQueryRow):
    scrutin_uid: str
    groupe_organe_ref: str | None
    position_vote: str  # Literal["pour", "contre", "abstention", "nonVotant", "nonVotantVolontaire"]

    acteur_ref: str | None
    mandat_ref: str | None
    par_delegation: bool | None
    num_place: str | None
    cause_position_vote: str | None

    source: str  # Literal["mise au point", "ventilation"]


@dataclass
class ScrutinParseResult:
    scrutins: list[ScrutinRow]
    groupes_votes: list[ScrutinGroupeVoteRow]
    votes_individuels: list[ScrutinVoteIndividuelRow]
