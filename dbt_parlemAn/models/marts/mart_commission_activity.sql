{{ config(materialized='table') }}

with depute_commissions as (
    select *
    from {{ ref('int_depute_commissions') }}
),
interventions as (
    select *
    from {{ ref('int_interventions_enriched') }}
),
commission_members as (
    select
      commission_uid,
      max(commission_libelle) as commission_libelle,
      max(commission_libelle_abrege) as commission_libelle_abrege,
      max(commission_code_type) as commission_code_type,
      count(distinct depute_uid) as nb_deputes,
      count(distinct mandat_uid) as nb_mandats
    from depute_commissions
    group by commission_uid
),
interventions_avec_commission as (
    select
      dc.commission_uid,
      i.intervention_id,
      i.date_seance,
      i.depute_uid
    from interventions i
    join depute_commissions dc
      on i.depute_uid = dc.depute_uid
     and (
        i.date_seance is null
        or (
          (dc.date_debut is null or i.date_seance >= dc.date_debut)
          and (dc.date_fin is null or i.date_seance <= dc.date_fin)
        )
      )
    qualify row_number() over (
      partition by i.intervention_id
      order by
        coalesce(dc.date_fin, date('9999-12-31')) desc,
        coalesce(dc.date_debut, date('1900-01-01')) desc,
        dc.mandat_uid
    ) = 1
),
commission_interventions as (
    select
      commission_uid,
      count(distinct intervention_id) as nb_interventions_des_membres,
      count(distinct depute_uid) as nb_orateurs,
      min(date_seance) as premiere_intervention,
      max(date_seance) as derniere_intervention
    from interventions_avec_commission
    group by commission_uid
)

select
  cm.commission_uid,
  cm.commission_libelle,
  cm.commission_libelle_abrege,
  cm.commission_code_type,
  cm.nb_deputes,
  cm.nb_mandats,
  coalesce(ci.nb_interventions_des_membres, 0) as nb_interventions_des_membres,
  coalesce(ci.nb_orateurs, 0) as nb_orateurs,
  ci.premiere_intervention,
  ci.derniere_intervention
from commission_members cm
left join commission_interventions ci
  on cm.commission_uid = ci.commission_uid
