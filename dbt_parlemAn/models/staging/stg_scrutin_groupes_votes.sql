{{ config(materialized='view') }}

select
  scrutin_uid,
  organe_ref_assemblee,
  groupe_organe_ref,
  nombre_membres_groupe,
  position_majoritaire,
  non_votants,
  pour,
  contre,
  abstentions,
  non_votants_volontaires
from {{ source('raw_parleman', 'scrutin_groupes_votes') }}