{{ config(materialized='view') }}

select
  uid as compte_rendu_uid,
  seance_ref,
  session_ref,
  safe_cast(date_seance as date) as date_seance,
  date_seance_jour,
  num_seance_jour,
  num_seance,
  type_assemblee,
  legislature,
  session,
  etat,
  diffusion,
  version
from {{ source('raw_parleman', 'comptes_rendus') }}