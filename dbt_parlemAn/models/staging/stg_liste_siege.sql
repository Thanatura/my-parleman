{{ config(materialized='view') }}

with acteurs as (
    select
      uid as depute_uid
    from {{ source('raw_parleman', 'acteurs') }}
),
mandats as (
    select
      uid as mandat_uid,
      acteur_ref as depute_uid,
      type_organe,
      mandature_place_hemicycle
    from {{ source('raw_parleman', 'mandats') }}
)

SELECT DISTINCT 
    a.depute_uid, 
    m.mandature_place_hemicycle
FROM mandats m
LEFT JOIN acteurs a
    ON m.depute_uid = a.depute_uid
WHERE m.type_organe = 'ASSEMBLEE'
ORDER BY m.mandature_place_hemicycle