from typing import Any

from lib.parsing_common import read_json_files_from_zip, to_date, to_str
from lib.questions_ecrites.models import (
    QuestionEcriteMinAttribRow,
    QuestionEcriteParseResult,
    QuestionEcriteRenouvellementRow,
    QuestionEcriteRow,
)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _first_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                return item
    return {}


def parse_questions_ecrites(zip_bytes: bytes) -> QuestionEcriteParseResult:
    questions: list[QuestionEcriteRow] = []
    min_attribs: list[QuestionEcriteMinAttribRow] = []
    renouvellements: list[QuestionEcriteRenouvellementRow] = []

    for payload in read_json_files_from_zip(zip_bytes, prefix="json/"):
        question = _first_dict((payload or {}).get("question"))
        if not question:
            continue

        uid = to_str(question.get("uid"))
        if not uid:
            continue

        identifiant = _first_dict(question.get("identifiant"))
        indexation = _first_dict(question.get("indexationAN"))
        analyses = _first_dict(indexation.get("analyses"))

        auteur = _first_dict(question.get("auteur"))
        identite = _first_dict(auteur.get("identite"))
        groupe = _first_dict(auteur.get("groupe"))

        min_int = _first_dict(question.get("minInt"))

        # Textes
        textes_question = _first_dict(question.get("textesQuestion"))
        texte_question_wrapper = _first_dict(textes_question.get("texteQuestion"))
        t_question_info_jo = _first_dict(texte_question_wrapper.get("infoJO"))

        textes_reponse = _first_dict(question.get("textesReponse"))
        texte_reponse_wrapper = _first_dict(textes_reponse.get("texteReponse"))
        t_reponse_info_jo = _first_dict(texte_reponse_wrapper.get("infoJO"))

        questions.append(
            QuestionEcriteRow(
                uid=uid,
                numero=to_str(identifiant.get("numero")),
                regime=to_str(identifiant.get("regime")),
                legislature=to_str(identifiant.get("legislature")),
                type=to_str(question.get("type")),
                rubrique=to_str(indexation.get("rubrique")),
                tete_analyse=to_str(indexation.get("teteAnalyse")),
                analyse=to_str(analyses.get("analyse")),
                auteur_acteur_ref=to_str(identite.get("acteurRef")),
                auteur_mandat_ref=to_str(identite.get("mandatRef")),
                auteur_groupe_organe_ref=to_str(groupe.get("organeRef")),
                auteur_groupe_abrege=to_str(groupe.get("abrege")),
                auteur_groupe_developpe=to_str(groupe.get("developpe")),
                min_int_organe_ref=to_str(min_int.get("organeRef")),
                min_int_abrege=to_str(min_int.get("abrege")),
                min_int_developpe=to_str(min_int.get("developpe")),
                texte_question=to_str(texte_question_wrapper.get("texte")),
                date_jo_question=to_date(t_question_info_jo.get("dateJO")),
                page_jo_question=to_str(t_question_info_jo.get("pageJO")),
                texte_reponse=to_str(texte_reponse_wrapper.get("texte")),
                date_jo_reponse=to_date(t_reponse_info_jo.get("dateJO")),
                page_jo_reponse=to_str(t_reponse_info_jo.get("pageJO")),
            )
        )

        min_attribs_wrapper = _first_dict(question.get("minAttribs"))
        min_attribs_data = _as_list(min_attribs_wrapper.get("minAttrib"))
        for min_attrib in min_attribs_data:
            if not isinstance(min_attrib, dict):
                continue
            info_jo = _first_dict(min_attrib.get("infoJO"))
            denom = _first_dict(min_attrib.get("denomination"))
            min_attribs.append(
                QuestionEcriteMinAttribRow(
                    question_uid=uid,
                    type_jo=to_str(info_jo.get("typeJO")),
                    date_jo=to_date(info_jo.get("dateJO")),
                    organe_ref=to_str(denom.get("organeRef")),
                    abrege=to_str(denom.get("abrege")),
                    developpe=to_str(denom.get("developpe")),
                )
            )

        renouv_wrapper = _first_dict(question.get("renouvellements"))
        renouv_data = _as_list(renouv_wrapper.get("renouvellement"))
        for renouv in renouv_data:
            if not isinstance(renouv, dict):
                continue
            info_jo = _first_dict(renouv.get("infoJO"))
            renouvellements.append(
                QuestionEcriteRenouvellementRow(
                    question_uid=uid,
                    type_jo=to_str(info_jo.get("typeJO")),
                    date_jo=to_date(info_jo.get("dateJO")),
                    num_jo=to_str(info_jo.get("numJO")),
                )
            )

    return QuestionEcriteParseResult(
        questions=questions,
        min_attribs=min_attribs,
        renouvellements=renouvellements,
    )
