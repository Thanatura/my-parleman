from dataclasses import dataclass
from datetime import date

from lib.bq_utils.models import BigQueryRow


@dataclass
class QuestionEcriteRow(BigQueryRow):
    uid: str

    numero: str | None
    regime: str | None
    legislature: str | None
    type: str | None

    rubrique: str | None
    tete_analyse: str | None
    analyse: str | None

    auteur_acteur_ref: str | None
    auteur_mandat_ref: str | None
    auteur_groupe_organe_ref: str | None
    auteur_groupe_abrege: str | None
    auteur_groupe_developpe: str | None

    min_int_organe_ref: str | None
    min_int_abrege: str | None
    min_int_developpe: str | None

    texte_question: str | None
    date_jo_question: date | None
    page_jo_question: str | None

    texte_reponse: str | None
    date_jo_reponse: date | None
    page_jo_reponse: str | None


@dataclass
class QuestionEcriteMinAttribRow(BigQueryRow):
    question_uid: str
    type_jo: str | None
    date_jo: date | None
    organe_ref: str | None
    abrege: str | None
    developpe: str | None


@dataclass
class QuestionEcriteRenouvellementRow(BigQueryRow):
    question_uid: str
    type_jo: str | None
    date_jo: date | None
    num_jo: str | None


@dataclass
class QuestionEcriteParseResult:
    questions: list[QuestionEcriteRow]
    min_attribs: list[QuestionEcriteMinAttribRow]
    renouvellements: list[QuestionEcriteRenouvellementRow]
