{{ config(materialized='table') }}

with scrutins_groupes_enriched as (select * from {{ ref('int_scrutin_groupes_enriched') }})
     select 
        count(1) as nb_co_votes,
       s1.groupe_uid as groupe_uid_1, 
       s2.groupe_uid as groupe_uid_2
     from scrutins_groupes_enriched as s1
     join scrutins_groupes_enriched as s2
       on s1.groupe_uid < s2.groupe_uid
      and s1.scrutin_uid = s2.scrutin_uid
     where s1.position_majoritaire is not null
       and s1.position_majoritaire = s2.position_majoritaire
    group by
            groupe_uid_1,
            groupe_uid_2
    order by nb_co_votes desc