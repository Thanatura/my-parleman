{{ config(materialized='table') }}

with depute_mandats as (
    select *
    from {{ ref('int_depute_mandats') }}
),
organes as (
    select *
    from {{ ref('stg_organes') }}
),
interventions as (
    select *
    from {{ ref('int_interventions_enriched') }}
),
groupes as (
    select
      organe_uid as groupe_uid,
      libelle as groupe_libelle,
      gp_position_politique,
      gp_couleur,
      legislature as groupe_legislature,
      date_debut as groupe_date_debut,
      date_fin as groupe_date_fin
    from organes
    where lower(coalesce(code_type, '')) in ('gp', 'groupepolitique')
       or lower(coalesce(libelle, '')) like '%groupe%'
),
groupe_members as (
    select
      g.groupe_uid,
      g.groupe_libelle,
      g.gp_position_politique,
      g.gp_couleur,
      g.groupe_legislature,
      count(distinct dm.depute_uid) as nb_deputes,
      count(distinct dm.mandat_uid) as nb_mandats
    from groupes g
    left join depute_mandats dm
      on dm.organe_uid = g.groupe_uid
    group by
      g.groupe_uid,
      g.groupe_libelle,
      g.gp_position_politique,
      g.gp_couleur,
      g.groupe_legislature
),
interventions_avec_groupe as (
    select
      g.groupe_uid,
      i.intervention_id,
      i.date_seance,
      i.depute_uid
    from interventions i
    join depute_mandats dm
      on i.depute_uid = dm.depute_uid
     and (
        i.date_seance is null
        or (
          (dm.date_debut is null or i.date_seance >= dm.date_debut)
          and (dm.date_fin is null or i.date_seance <= dm.date_fin)
        )
      )
    join groupes g
      on dm.organe_uid = g.groupe_uid
    qualify row_number() over (
      partition by i.intervention_id
      order by
        coalesce(dm.date_fin, date('9999-12-31')) desc,
        coalesce(dm.date_debut, date('1900-01-01')) desc,
        dm.mandat_uid
    ) = 1
),
groupe_interventions as (
    select
      groupe_uid,
      count(distinct intervention_id) as nb_interventions,
      count(distinct depute_uid) as nb_orateurs,
      min(date_seance) as premiere_intervention,
      max(date_seance) as derniere_intervention
    from interventions_avec_groupe
    group by groupe_uid
)

select
  gm.groupe_uid,
  gm.groupe_libelle,
  gm.gp_position_politique,
  gm.gp_couleur,
  gm.groupe_legislature,
  gm.nb_deputes,
  gm.nb_mandats,
  coalesce(gi.nb_interventions, 0) as nb_interventions,
  coalesce(gi.nb_orateurs, 0) as nb_orateurs,
  gi.premiere_intervention,
  gi.derniere_intervention
from groupe_members gm
left join groupe_interventions gi
  on gm.groupe_uid = gi.groupe_uid
