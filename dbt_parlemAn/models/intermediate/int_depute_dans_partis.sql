{{ config(materialized='view') }}

with acteurs as (
    select *
    from {{ ref('stg_deputes') }}
),
organes as (
    select *
    from {{ ref('stg_organes') }}
),
mandats as (
    select *
    from {{ ref('stg_mandats') }}
)


SELECT DISTINCT 
    a.depute_uid, 
    o.libelle as gp_libelle, 
    o.gp_couleur
FROM mandats m
LEFT JOIN acteurs a
    ON m.depute_uid = a.depute_uid
LEFT JOIN organes o
    ON m.organe_uid = o.organe_uid
WHERE m.type_organe = 'GP'
ORDER BY o.libelle