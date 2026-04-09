{{ config(materialized='view') }}

with deputes as (
    select *
    from {{ ref('stg_deputes') }}
),
mandats as (
    select *
    from {{ ref('stg_mandats') }}
)

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
from mandats m
left join deputes d
  on m.depute_uid = d.depute_uid
