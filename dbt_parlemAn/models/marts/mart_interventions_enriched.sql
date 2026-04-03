{{ config(materialized='table') }}

select
  intervention_id,
  compte_rendu_uid,
  point_id,
  point_valeur_ptsodj,
  date_seance,
  legislature,
  session,
  num_seance,
  roledebat,
  depute_uid,
  orateur_nom,
  trigramme,
  profession_categorie,
  profession_famille,
  texte
from {{ ref('int_interventions_enriched') }}
