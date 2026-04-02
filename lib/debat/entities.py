from dataclasses import dataclass


@dataclass(frozen=True)
class CompteRendu:
    uid: str | None
    seance_ref: str | None
    session_ref: str | None
    date_seance: str | None
    date_seance_jour: str | None
    num_seance_jour: str | None
    num_seance: str | None
    type_assemblee: str | None
    legislature: str | None
    session: str | None
    etat: str | None
    diffusion: str | None
    version: str | None


@dataclass(frozen=True)
class PointSeance:
    compte_rendu_uid: str | None
    point_id: str | None
    point_type: str
    valeur_ptsodj: str | None
    nivpoint: str | None
    ordinal_prise: str | None
    ordre_absolu_seance: str | None
    code_grammaire: str | None
    code_style: str | None
    sommaire: str | None
    titre: str


@dataclass(frozen=True)
class Intervention:
    compte_rendu_uid: str | None
    point_id: str | None
    point_valeur_ptsodj: str | None
    intervention_id: str | None
    ordre_absolu_seance: str | None
    ordinal_prise: str | None
    code_grammaire: str | None
    code_style: str | None
    code_parole: str | None
    roledebat: str | None
    speaker_name: str | None
    speaker_id: str | None
    speaker_qualite: str | None
    texte: str


@dataclass(frozen=True)
class DebatParseResult:
    comptes_rendus: list[CompteRendu]
    points: list[PointSeance]
    interventions: list[Intervention]
