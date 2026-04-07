{{ config(materialized='view') }}

select
  compte_rendu_uid,
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
from {{ source('raw_parleman', 'points_seance') }}