{{ config(materialized='view') }}

select
  dossier_uid,
  acte_uid,
  acte_code,
  acte_libelle_canonique,
  acte_libelle_court,
  organe_ref,
  date_acte,
  type_acte,
  texte_associe,
  vote_ref
from {{ source('raw_parleman', 'dossier_actes_legislatifs') }}