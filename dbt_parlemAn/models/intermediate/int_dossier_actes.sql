{{ config(materialized='view') }}

with actes as (
    select
        dossier_uid,
        acte_uid,
        date_acte,
        type_acte,
        acte_code
    from {{ ref('stg_dossier_actes_legislatifs') }}
)

select
    dossier_uid,
    min(date_acte) as date_premier_acte,
    max(date_acte) as date_dernier_acte,
    count(distinct acte_uid) as nombre_actes_total,
    countif(acte_code like 'PROM%') > 0 as est_adopte
from actes
where dossier_uid is not null
group by 1
