{{ config(materialized='table') }}

with deputes_dans_partis as (
    select *
    from {{ ref('int_depute_dans_partis') }}
),liste_sieges as (
    select *
    from {{ ref('int_liste_siege') }}
),
acteurs as (
    select *
    from {{ ref('stg_deputes') }}
)

SELECT DISTINCT 
    dp.depute_uid, 
    a.nom, 
    a.prenom, 
    ls.mandature_place_hemicycle, 
    dp.gp_libelle, 
    dp.gp_couleur 
FROM deputes_dans_partis dp
LEFT JOIN liste_sieges ls
    ON dp.depute_uid = ls.depute_uid
LEFT JOIN acteurs a
    ON dp.depute_uid = a.depute_uid
ORDER BY ls.mandature_place_hemicycle