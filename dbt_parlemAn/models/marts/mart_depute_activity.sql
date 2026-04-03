{{ config(materialized='table') }}

with interventions as (
    select *
    from {{ ref('int_interventions_enriched') }}
),
depute_mandats as (
    select *
    from {{ ref('int_depute_mandats') }}
)

select
  dm.depute_uid,
  max(dm.nom_complet) as nom_complet,
  max(dm.trigramme) as trigramme,
  count(distinct dm.mandat_uid) as nb_mandats,
  count(distinct i.intervention_id) as nb_interventions,
  min(i.date_seance) as premiere_intervention,
  max(i.date_seance) as derniere_intervention
from depute_mandats dm
left join interventions i
  on dm.depute_uid = i.depute_uid
group by dm.depute_uid
