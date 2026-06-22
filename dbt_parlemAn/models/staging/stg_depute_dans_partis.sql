

with acteurs as (
    select
      uid as depute_uid
    from {{ source('raw_parleman', 'acteurs') }}
),
organes as (
    select
      uid as organe_uid,
      libelle,
      gp_couleur
    from {{ source('raw_parleman', 'organes') }}
),
mandats as (
    select
      acteur_ref as depute_uid,
      organe_ref as organe_uid,
      type_organe
    from {{ source('raw_parleman', 'mandats') }}
)

SELECT DISTINCT 
    a.depute_uid, 
    o.libelle as gp_libelle, 
    o.gp_couleur
FROM mandats m
LEFT JOIN acteurs a
    ON m.depute_uid = a.depute_uid
LEFT JOIN organes o
    ON m.organe_uid = o.organe_uid
WHERE m.type_organe = 'GP'
ORDER BY o.libelle