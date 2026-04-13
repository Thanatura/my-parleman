from dataclasses import dataclass
from datetime import date
from collections.abc import Iterator

from lib.bq_utils.models import BigQueryRow


@dataclass
class AmendementRow(BigQueryRow):
    """Represents a parliamentary amendment"""

    uid: str
    legislature: str | None
    numero_long: str | None
    numero_ordre_depot: str | None
    prefixe_organe_examen: str | None
    examen_ref: str | None
    texte_legislatif_ref: str | None
    dossier_legislatif_ref: str | None

    # Targeting text location
    division_titre: str | None
    article_designation_courte: str | None
    division_type: str | None

    # Amendment body
    dispositif: str | None
    expose_sommaire: str | None

    # Amendment lifecycle
    date_depot: date | None
    date_publication: date | None
    etat_code: str | None
    etat_libelle: str | None
    sous_etat_code: str | None
    sous_etat_libelle: str | None
    sort: str | None

    # Signatories
    auteur_type: str | None
    auteur_acteur_ref: str | None
    auteur_groupe_politique_ref: str | None


@dataclass
class AmendementSignataireRow(BigQueryRow):
    """Represents amendment author/signatory"""

    amendement_uid: str
    acteur_ref: str
    type_auteur: str | None
    groupe_politique_ref: str | None
    ordre_presentation: int


@dataclass
class AmendementsCosignataireRow(BigQueryRow):
    """Represents co-signers of an amendment"""

    amendement_uid: str
    cosignataire_acteur_ref: str
    ordre_presentation: int


@dataclass
class AmendementParseResult:
    amendements: Iterator[AmendementRow]
    signataires: Iterator[AmendementSignataireRow]
    cosignataires: Iterator[AmendementsCosignataireRow]
