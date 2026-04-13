{{ config(materialized='view') }}

with scrutins as (
    select
        scrutin_uid,
        sort_code,
        synthese_nombre_votants,
        synthese_pour,
        synthese_contre,
        synthese_abstentions
    from {{ ref('stg_scrutins') }}
),

actes as (
    select
        dossier_uid,
        vote_ref
    from {{ ref('stg_dossier_actes_legislatifs') }}
    where vote_ref is not null
)

select
    a.dossier_uid,
    count(distinct s.scrutin_uid) as nombre_scrutins_total,
    sum(case when lower(s.sort_code) = 'adopté' then 1 else 0 end) as nombre_scrutins_adoptes,
    sum(case when lower(s.sort_code) = 'rejeté' then 1 else 0 end) as nombre_scrutins_rejetes,
    
    sum(s.synthese_nombre_votants) as volume_votants_total,
    sum(s.synthese_pour) as volume_votes_pour,
    sum(s.synthese_contre) as volume_votes_contre,
    sum(s.synthese_abstentions) as volume_votes_abstentions
from scrutins s
inner join actes a on s.scrutin_uid = a.vote_ref
where a.dossier_uid is not null
group by 1
