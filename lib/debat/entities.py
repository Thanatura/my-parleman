from __future__ import annotations

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

    @classmethod
    def create_table_sql_text(cls, project_id: str, dataset_id: str) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS {project_id}.{dataset_id}.comptes_rendus (
            uid STRING,
            seance_ref STRING,
            session_ref STRING,
            date_seance STRING,
            date_seance_jour STRING,
            num_seance_jour STRING,
            num_seance STRING,
            type_assemblee STRING,
            legislature STRING,
            session STRING,
            etat STRING,
            diffusion STRING,
            version STRING
        );
        """.strip()

    @classmethod
    def truncate_table_sql_text(cls, project_id: str, dataset_id: str) -> str:
        return f"""
        TRUNCATE TABLE {project_id}.{dataset_id}.comptes_rendus;
        """.strip()

    @classmethod
    def columns(cls) -> str:
        return "(uid, seance_ref, session_ref, date_seance, date_seance_jour, num_seance_jour, num_seance, type_assemblee, legislature, session, etat, diffusion, version)"

    def __repr__(self) -> str:
        value_tuple = (
            self.uid,
            self.seance_ref,
            self.session_ref,
            self.date_seance,
            self.date_seance_jour,
            self.num_seance_jour,
            self.num_seance,
            self.type_assemblee,
            self.legislature,
            self.session,
            self.etat,
            self.diffusion,
            self.version,
        )
        return f"""
        ({",".join([f'"{v}"' for v in value_tuple])})
        """.strip()


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

    @classmethod
    def create_table_sql_text(cls, project_id: str, dataset_id: str) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS {project_id}.{dataset_id}.points_seance (
            compte_rendu_uid STRING,
            point_id STRING,
            point_type STRING,
            valeur_ptsodj STRING,
            nivpoint STRING,
            ordinal_prise STRING,
            ordre_absolu_seance STRING,
            code_grammaire STRING,
            code_style STRING,
            sommaire STRING,
            titre STRING
        );
        """.strip()

    @classmethod
    def truncate_table_sql_text(cls, project_id: str, dataset_id: str) -> str:
        return f"""
        TRUNCATE TABLE {project_id}.{dataset_id}.points_seance;
        """.strip()

    @classmethod
    def columns(cls) -> str:
        return "(compte_rendu_uid, point_id, point_type, valeur_ptsodj, nivpoint, ordinal_prise, ordre_absolu_seance, code_grammaire, code_style, sommaire, titre)"

    def __repr__(self) -> str:
        value_tuple = (
            self.compte_rendu_uid,
            self.point_id,
            self.point_type,
            self.valeur_ptsodj,
            self.nivpoint,
            self.ordinal_prise,
            self.ordre_absolu_seance,
            self.code_grammaire,
            self.code_style,
            self.sommaire,
            self.titre,
        )
        return f"""
        ({",".join([f'"{v}"' for v in value_tuple])})
        """.strip()


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

    @classmethod
    def create_table_sql_text(cls, project_id: str, dataset_id: str) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS {project_id}.{dataset_id}.interventions (
            compte_rendu_uid STRING,
            point_id STRING,
            point_valeur_ptsodj STRING,
            intervention_id STRING,
            ordre_absolu_seance STRING,
            ordinal_prise STRING,
            code_grammaire STRING,
            code_style STRING,
            code_parole STRING,
            roledebat STRING,
            speaker_name STRING,
            speaker_id STRING,
            speaker_qualite STRING,
            texte STRING
        );
        """.strip()

    @classmethod
    def truncate_table_sql_text(cls, project_id: str, dataset_id: str) -> str:
        return f"""
        TRUNCATE TABLE {project_id}.{dataset_id}.interventions;
        """.strip()

    @classmethod
    def columns(cls) -> str:
        return "(compte_rendu_uid, point_id, point_valeur_ptsodj, intervention_id, ordre_absolu_seance, ordinal_prise, code_grammaire, code_style, code_parole, roledebat, speaker_name, speaker_id, speaker_qualite, texte)"

    def __repr__(self) -> str:
        value_tuple = (
            self.compte_rendu_uid,
            self.point_id,
            self.point_valeur_ptsodj,
            self.intervention_id,
            self.ordre_absolu_seance,
            self.ordinal_prise,
            self.code_grammaire,
            self.code_style,
            self.code_parole,
            self.roledebat,
            self.speaker_name,
            self.speaker_id,
            self.speaker_qualite,
            self.texte,
        )
        return f"""
        ({",".join([f'"{v}"' for v in value_tuple])})
        """.strip()


@dataclass(frozen=True)
class DebatParseResult:
    comptes_rendus: list[CompteRendu]
    points: list[PointSeance]
    interventions: list[Intervention]
