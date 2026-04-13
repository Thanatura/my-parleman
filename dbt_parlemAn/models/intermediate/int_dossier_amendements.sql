{{ config(materialized='view') }}

with amendements as (
    select
        dossier_legislatif_ref as dossier_uid,
        amendement_uid,
        sort
    from {{ ref('stg_amendements') }}
)

select
    dossier_uid,
    count(distinct amendement_uid) as nombre_amendements_total,
    sum(case when sort = 'Adopté' then 1 else 0 end) as nombre_amendements_adoptes,
    sum(case when sort = 'Rejeté' or sort = 'Tombé' then 1 else 0 end) as nombre_amendements_rejetes
from amendements
where dossier_uid is not null
group by 1
