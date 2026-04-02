from dataclasses import dataclass
from datetime import date, datetime

from lib.bq_utils.models import BigQueryRow


@dataclass
class ActeurRow(BigQueryRow):
    uid: str
    civilite: str | None
    prenom: str | None
    nom: str | None
    alpha: str | None
    trigramme: str | None
    date_naissance: date | None
    ville_naissance: str | None
    departement_naissance: str | None
    pays_naissance: str | None
    profession_libelle: str | None
    profession_categorie: str | None
    profession_famille: str | None
    uri_hatvp: str | None
    ingested_at: datetime


@dataclass
class AdresseRow(BigQueryRow):
    uid: str | None
    acteur_uid: str
    type_code: str | None
    type_libelle: str | None
    xsi_type: str | None
    intitule: str | None
    numero_rue: str | None
    nom_rue: str | None
    complement: str | None
    code_postal: str | None
    ville: str | None
    val_elec: str | None
    ingested_at: datetime


@dataclass(frozen=False)
class MandatRow(BigQueryRow):
    uid: str | None
    acteur_ref: str
    xsi_type: str | None
    legislature: str | None
    type_organe: str | None
    organe_ref: str | None
    date_debut: date | None
    date_fin: date | None
    date_publication: date | None
    preseance: int | None
    nomin_principale: bool | None
    code_qualite: str | None
    lib_qualite: str | None
    election_departement: str | None
    election_num_departement: str | None
    election_num_circo: str | None
    election_cause_mandat: str | None
    mandature_date_prise_fonction: date | None
    mandature_cause_fin: str | None
    mandature_premiere_election: bool | None
    mandature_place_hemicycle: int | None
    ingested_at: datetime


@dataclass
class OrganeRow(BigQueryRow):
    uid: str | None
    xsi_type: str | None
    code_type: str | None
    libelle: str | None
    libelle_abrege: str | None
    libelle_abrev: str | None
    regime: str | None
    legislature: str | None
    date_debut: date | None
    date_fin: date | None
    circo_numero: str | None
    circo_region_type: str | None
    circo_region_libelle: str | None
    circo_dep_code: str | None
    circo_dep_libelle: str | None
    gp_couleur: str | None
    gp_preseance: int | None
    gp_position_politique: str | None
    ingested_at: datetime


@dataclass
class DeportRow(BigQueryRow):
    uid: str | None
    legislature: str | None
    acteur_ref: str | None
    date_creation: datetime | None
    date_publication: datetime | None
    portee_code: str | None
    portee_libelle: str | None
    lecture_code: str | None
    instance_code: str | None
    cible_type_code: str | None
    cible_reference_textuelle: str | None
    ingested_at: datetime
