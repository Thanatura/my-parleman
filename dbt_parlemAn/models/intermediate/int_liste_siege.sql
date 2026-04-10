{{ config(materialized='view') }}

with acteurs as (
    select *
    from {{ ref('stg_deputes') }}
),
mandats as (
    select *
    from {{ ref('stg_mandats') }}
)

SELECT DISTINCT 
    a.depute_uid, 
    m.mandature_place_hemicycle
FROM mandats m
LEFT JOIN acteurs a
    ON m.depute_uid = a.depute_uid
WHERE m.type_organe = 'ASSEMBLEE'
ORDER BY m.mandature_place_hemicycle