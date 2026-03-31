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
            date_seance DATE,
            date_seance_jour DATE,
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

    def insert_sql_text(self, project_id: str, dataset_id: str) -> str:
        return f"""
        INSERT INTO {project_id}.{dataset_id}.comptes_rendus (
            uid,
            seance_ref,
            session_ref,
            date_seance,
            date_seance_jour,
            num_seance_jour,
            num_seance,
            type_assemblee,
            legislature,
            session,
            etat,
            diffusion,
            version
        ) VALUES (
            {self.uid!r},
            {self.seance_ref!r},
            {self.session_ref!r},
            {self.date_seance!r},
            {self.date_seance_jour!r},
            {self.num_seance_jour!r},
            {self.num_seance!r},
            {self.type_assemblee!r},
            {self.legislature!r},
            {self.session!r},
            {self.etat!r},
            {self.diffusion!r},
            {self.version!r}
        );
        """.strip()


@dataclass(frozen=True)
class PointSeance:
    uid: str | None
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

    def to_sql_insert(self, project_id: str, dataset_id: str) -> str:
        return f"""
        INSERT INTO {project_id}.{dataset_id}.points_seance (
            uid,
            point_id,
            point_type,
            valeur_ptsodj,
            nivpoint,
            ordinal_prise,
            ordre_absolu_seance,
            code_grammaire,
            code_style,
            sommaire,
            titre
        ) VALUES (
            {self.uid!r},
            {self.point_id!r},
            {self.point_type!r},
            {self.valeur_ptsodj!r},
            {self.nivpoint!r},
            {self.ordinal_prise!r},
            {self.ordre_absolu_seance!r},
            {self.code_grammaire!r},
            {self.code_style!r},
            {self.sommaire!r},
            {self.titre!r}
        );
        """.strip()


@dataclass(frozen=True)
class Intervention:
    uid: str | None
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

    def to_sql_insert(self) -> str:
        return f"""
        INSERT INTO interventions (
            uid,
            point_id,
            point_valeur_ptsodj,
            intervention_id,
            ordre_absolu_seance,
            ordinal_prise,
            code_grammaire,
            code_style,
            code_parole,
            roledebat,
            speaker_name,
            speaker_id,
            speaker_qualite,
            texte
        ) VALUES (
            {self.uid!r},
            {self.point_id!r},
            {self.point_valeur_ptsodj!r},
            {self.intervention_id!r},
            {self.ordre_absolu_seance!r},
            {self.ordinal_prise!r},
            {self.code_grammaire!r},
            {self.code_style!r},
            {self.code_parole!r},
            {self.roledebat!r},
            {self.speaker_name!r},
            {self.speaker_id!r},
            {self.speaker_qualite!r},
            {self.texte!r}
        );
        """.strip()


@dataclass(frozen=True)
class DebatParseResult:
    comptes_rendus: list[CompteRendu]
    points: list[PointSeance]
    interventions: list[Intervention]
