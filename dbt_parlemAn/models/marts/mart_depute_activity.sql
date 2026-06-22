with interventions as (
  select intervention_id,
    date_seance,
    depute_uid
  from {{ ref('stg_interventions_enriched') }}
),
depute_mandats as (
  select depute_uid,
    nom_complet,
    trigramme,
    mandat_uid
  from {{ ref('stg_depute_mandats') }}
)
select dm.depute_uid,
  max(dm.nom_complet) as nom_complet,
  max(dm.trigramme) as trigramme,
  count(distinct dm.mandat_uid) as nb_mandats,
  count(distinct i.intervention_id) as nb_interventions,
  min(i.date_seance) as premiere_intervention,
  max(i.date_seance) as derniere_intervention
from depute_mandats dm
  left join interventions i on dm.depute_uid = i.depute_uid
group by dm.depute_uid