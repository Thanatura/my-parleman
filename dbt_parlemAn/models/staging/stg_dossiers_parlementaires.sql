{{ config(materialized='view') }}

select
  uid as dossier_uid,
  legislature,
  titre_dossier,
  titre_chemin,
  procedure_parlementaire_code,
  procedure_parlementaire_libelle,
  initiateur_acteur_ref,
  initiateur_mandat_ref,
  initiateur_organe_ref,
  nombre_actes_legislatifs
from {{ source('raw_parleman', 'dossiers_parlementaires') }}