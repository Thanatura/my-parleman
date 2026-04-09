{{ config(materialized='table') }}

with depute_mandats as (
    select
      m.mandat_uid,
      m.depute_uid,
      d.nom,
      d.prenom,
      d.nom_complet,
      d.trigramme,
      m.legislature,
      m.type_organe,
      m.organe_uid,
      m.election_departement,
      m.election_num_departement,
      m.election_num_circo,
      m.date_debut,
      m.date_fin,
      m.code_qualite,
      m.lib_qualite,
      m.nomin_principale,
      m.mandature_premiere_election,
      m.mandature_place_hemicycle
    from {{ ref('stg_mandats') }} m
    left join {{ ref('stg_deputes') }} d
      on m.depute_uid = d.depute_uid
),
interventions as (
    select
      depute_uid,
      count(distinct intervention_id) as nb_interventions,
      min(date_seance) as premiere_intervention,
      max(date_seance) as derniere_intervention
    from {{ ref('int_interventions_enriched') }}
    group by depute_uid
),
mandats_eligibles as (
    select
      dm.*,
      row_number() over (
        partition by dm.depute_uid
        order by
          case
            when dm.date_fin is null or dm.date_fin >= current_date() then 1
            else 0
          end desc,
          coalesce(dm.date_fin, date('9999-12-31')) desc,
          coalesce(dm.date_debut, date('1900-01-01')) desc,
          dm.mandat_uid desc
      ) as rn
    from depute_mandats dm
    where dm.election_num_departement is not null
      and dm.election_num_circo is not null
),
deputes_circo as (
    select
      me.depute_uid,
      me.nom_complet,
      me.trigramme,
      me.legislature,
      me.mandat_uid,
      me.date_debut,
      me.date_fin,
      me.election_departement,
      upper(trim(me.election_num_departement)) as departement_code,
      lpad(trim(me.election_num_circo), 2, '0') as circonscription_numero,
      concat(
        upper(trim(me.election_num_departement)),
        '-',
        lpad(trim(me.election_num_circo), 2, '0')
      ) as circonscription_code
    from mandats_eligibles me
    where me.rn = 1
),
interventions_circo as (
    select
      dc.circonscription_code,
      count(distinct dc.depute_uid) as nb_deputes,
      count(distinct dc.mandat_uid) as nb_mandats,
      coalesce(sum(i.nb_interventions), 0) as nb_interventions,
      min(i.premiere_intervention) as premiere_intervention,
      max(i.derniere_intervention) as derniere_intervention,
      string_agg(dc.nom_complet, ', ' order by dc.nom_complet) as deputes
    from deputes_circo dc
    left join interventions i
      on dc.depute_uid = i.depute_uid
    group by dc.circonscription_code
)

select
  dc.depute_uid,
  dc.nom_complet,
  dc.trigramme,
  dc.legislature,
  dc.mandat_uid,
  dc.date_debut,
  dc.date_fin,
  dc.election_departement,
  dc.departement_code,
  dc.circonscription_numero,
  dc.circonscription_code,
  coalesce(i.nb_interventions, 0) as nb_interventions_depute,
  i.premiere_intervention as premiere_intervention_depute,
  i.derniere_intervention as derniere_intervention_depute,
  ic.nb_deputes,
  ic.nb_mandats,
  ic.nb_interventions,
  ic.premiere_intervention,
  ic.derniere_intervention,
  ic.deputes
from deputes_circo dc
left join interventions i
  on dc.depute_uid = i.depute_uid
left join interventions_circo ic
  on dc.circonscription_code = ic.circonscription_code
