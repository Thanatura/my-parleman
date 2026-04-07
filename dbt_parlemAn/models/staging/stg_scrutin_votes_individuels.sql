{{ config(materialized='view') }}

select
  scrutin_uid,
  groupe_organe_ref,
  position_vote,
  acteur_ref as depute_uid,
  mandat_ref,
  par_delegation,
  num_place,
  cause_position_vote,
  source
from {{ source('raw_parleman', 'scrutin_votes_individuels') }}