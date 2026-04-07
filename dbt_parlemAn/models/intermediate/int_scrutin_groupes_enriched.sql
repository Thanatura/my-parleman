{{ config(materialized='view') }}

with groupes as (select * from {{ ref('int_groupes') }}),
     scrutins_groupes as (select * from {{ ref('int_scrutin_groupes') }})
     select 
       g.groupe_uid,
       g.groupe_libelle,
       g.gp_position_politique,
       g.gp_couleur,
       g.groupe_legislature,
       g.groupe_date_debut,
       g.groupe_date_fin,
       s.scrutin_uid,
       s.position_majoritaire
     from groupes g
     left join scrutins_groupes s
       on g.groupe_uid = s.groupe_uid