{{ config(materialized='view') }}

select
  uid as mandat_uid,
  acteur_ref as depute_uid,
  xsi_type,
  legislature,
  type_organe,
  organe_ref as organe_uid,
  date_debut,
  date_fin,
  date_publication,
  preseance,
  nomin_principale,
  code_qualite,
  lib_qualite,
  election_departement,
  election_num_departement,
  election_num_circo,
  election_cause_mandat,
  mandature_date_prise_fonction,
  mandature_cause_fin,
  mandature_premiere_election,
  mandature_place_hemicycle,
  ingested_at
from {{ source('raw_parleman', 'mandats') }}
