{{ config(materialized='view') }}

select
  uid as depute_uid,
  civilite,
  prenom,
  nom,
  concat(coalesce(prenom, ''), ' ', coalesce(nom, '')) as nom_complet,
  alpha,
  trigramme,
  date_naissance,
  ville_naissance,
  departement_naissance,
  pays_naissance,
  profession_libelle,
  profession_categorie,
  profession_famille,
  uri_hatvp,
  ingested_at
from {{ source('raw_parleman', 'acteurs') }}
