from dataclasses import dataclass
from datetime import datetime

from lib.bq_utils.models import BigQueryRow


@dataclass
class DocumentRow(BigQueryRow):
    """Represents a legislative document (accord international, amendment, etc.)"""

    uid: str
    legislature: str | None
    type_code: str | None
    type_libelle: str | None
    denomination_structurelle: str | None
    provenance: str | None
    titre_principal: str | None
    titre_principal_court: str | None
    dossier_ref: str | None

    # Cycle de vie dates
    date_creation: datetime | None
    date_depot: datetime | None
    date_publication: datetime | None
    date_publication_web: datetime | None

    # Classification
    famille_depot_code: str | None
    famille_depot_libelle: str | None
    famille_classe_code: str | None
    famille_classe_libelle: str | None
    famille_espece_code: str | None
    famille_espece_libelle: str | None
    type_sous_type_code: str | None
    type_sous_type_libelle: str | None

    # Notice
    num_notice: str | None
    formule: str | None
    adoption_conforme: bool | None

    # Auteurs
    auteur_ref: str | None
    auteur_qualite: str | None

    # Imprimerie
    isbn: str | None
    issn: str | None
    dian: str | None
    nb_page: int | None


@dataclass
class DossierParlementaireRow(BigQueryRow):
    """Represents a parliamentary legislative dossier"""

    uid: str
    legislature: str | None
    titre_dossier: str | None
    titre_chemin: str | None
    procedure_parlementaire_code: str | None
    procedure_parlementaire_libelle: str | None

    # Initiator information
    initiateur_acteur_ref: str | None
    initiateur_mandat_ref: str | None
    initiateur_organe_ref: str | None

    # References to associated acts/documents
    nombre_actes_legislatifs: int | None


@dataclass
class DossierActeLegislatifRow(BigQueryRow):
    """Represents a legislative act within a dossier"""

    dossier_uid: str
    acte_uid: str
    acte_code: str | None
    acte_libelle_canonique: str | None
    acte_libelle_court: str | None
    organe_ref: str | None
    date_acte: datetime | None
    type_acte: str | None  # Etape_Type, DepotInitiative_Type, etc.
    texte_associe: str | None
    vote_ref: str | None


@dataclass
class DossiersParseResult:
    documents: list[DocumentRow]
    dossiers_parlementaires: list[DossierParlementaireRow]
    dossier_actes_legislatifs: list[DossierActeLegislatifRow]
