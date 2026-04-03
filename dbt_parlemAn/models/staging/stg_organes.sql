{{ config(materialized='view') }}

select
  uid as organe_uid,
  xsi_type,
  code_type,
  libelle,
  libelle_abrege,
  libelle_abrev,
  regime,
  legislature,
  date_debut,
  date_fin,
  circo_numero,
  circo_region_type,
  circo_region_libelle,
  circo_dep_code,
  circo_dep_libelle,
  gp_couleur,
  gp_preseance,
  gp_position_politique,
  ingested_at
from {{ source('raw_parleman', 'organes') }}
