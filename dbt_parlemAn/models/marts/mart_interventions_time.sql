{{ config(materialized='table') }}

with interventions as (
    select *
    from {{ ref('int_interventions_enriched') }}
)

select
  date_seance,
  legislature,
  count(distinct intervention_id) as nb_interventions,
  count(distinct depute_uid) as nb_orateurs,
  count(distinct compte_rendu_uid) as nb_comptes_rendus
from interventions
where date_seance is not null
group by date_seance, legislature
