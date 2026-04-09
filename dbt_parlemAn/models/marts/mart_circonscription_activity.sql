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
  organes as (
    select *
    from {{ ref('stg_organes') }}
  ),
interventions_depute as (
    select
      depute_uid,
      count(distinct intervention_id) as nb_interventions_depute,
      min(date_seance) as premiere_intervention_depute,
      max(date_seance) as derniere_intervention_depute
    from {{ ref('int_interventions_enriched') }}
    group by depute_uid
),
groupes_politiques as (
    select
      organe_uid,
      libelle as groupe_libelle,
      gp_position_politique,
      gp_couleur
    from organes
    where lower(coalesce(code_type, '')) in ('gp', 'groupepolitique')
       or lower(coalesce(libelle, '')) like '%groupe%'
),
depute_appartenance_politique as (
    select
      dm.depute_uid,
      gp.groupe_libelle,
      gp.gp_position_politique,
      gp.gp_couleur,
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
    inner join groupes_politiques gp
      on dm.organe_uid = gp.organe_uid
),
depute_appartenance as (
    select
      depute_uid,
      groupe_libelle,
      gp_position_politique,
      gp_couleur
    from depute_appartenance_politique
    where rn = 1
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
      me.mandat_uid,
      me.legislature,
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
)

select
  dc.circonscription_code,
  concat(dc.departement_code, dc.circonscription_numero) as circonscription_code_nodash,
  dc.departement_code,
  dc.circonscription_numero,
  max(dc.election_departement) as election_departement,
  max(dc.legislature) as legislature,
  count(distinct dc.depute_uid) as nb_deputes,
  count(distinct dc.mandat_uid) as nb_mandats,
  coalesce(sum(i.nb_interventions_depute), 0) as nb_interventions,
  min(i.premiere_intervention_depute) as premiere_intervention,
  max(i.derniere_intervention_depute) as derniere_intervention,
  string_agg(distinct da.groupe_libelle, ', ' order by da.groupe_libelle) as groupes_politiques,
  string_agg(
    distinct da.gp_position_politique,
    ', ' order by da.gp_position_politique
  ) as positionnements_politiques,
  string_agg(distinct da.gp_couleur, ', ' order by da.gp_couleur) as couleurs_groupes,
  string_agg(distinct dc.nom_complet, ', ' order by dc.nom_complet) as deputes
from deputes_circo dc
left join interventions_depute i
  on dc.depute_uid = i.depute_uid
left join depute_appartenance da
  on dc.depute_uid = da.depute_uid
group by
  dc.circonscription_code,
  dc.departement_code,
  dc.circonscription_numero
