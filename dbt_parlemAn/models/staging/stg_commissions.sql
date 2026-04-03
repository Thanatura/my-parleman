{{ config(materialized='view') }}

with organes as (
    select *
    from {{ source('raw_parleman', 'organes') }}
)

select
  uid as commission_uid,
  code_type,
  libelle,
  libelle_abrege,
  libelle_abrev,
  legislature,
  date_debut,
  date_fin,
  circo_region_type,
  circo_region_libelle,
  gp_position_politique,
  ingested_at
from organes
where lower(coalesce(code_type, '')) like '%com%'
   or lower(coalesce(libelle, '')) like '%commission%'
