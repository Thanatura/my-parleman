{{ config(materialized='view') }}

with deputes as (
    select
      uid as depute_uid,
      nom,
      prenom,
      concat(coalesce(prenom, ''), ' ', coalesce(nom, '')) as nom_complet,
      trigramme
    from {{ source('raw_parleman', 'acteurs') }}
),
mandats as (
    select
      uid as mandat_uid,
      acteur_ref as depute_uid,
      legislature,
      type_organe,
      organe_ref as organe_uid,
      election_departement,
      election_num_departement,
      election_num_circo,
      date_debut,
      date_fin,
      code_qualite,
      lib_qualite,
      nomin_principale,
      mandature_premiere_election,
      mandature_place_hemicycle
    from {{ source('raw_parleman', 'mandats') }}
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
