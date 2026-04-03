{{ config(materialized='view') }}

with depute_mandats as (
    select *
    from {{ ref('int_depute_mandats') }}
),
commissions as (
    select *
    from {{ ref('stg_commissions') }}
)

select
  dm.depute_uid,
  dm.nom,
  dm.prenom,
  dm.nom_complet,
  dm.mandat_uid,
  dm.legislature,
  dm.date_debut,
  dm.date_fin,
  c.commission_uid,
  c.libelle as commission_libelle,
  c.libelle_abrege as commission_libelle_abrege,
  c.code_type as commission_code_type
from depute_mandats dm
inner join commissions c
  on dm.organe_uid = c.commission_uid
