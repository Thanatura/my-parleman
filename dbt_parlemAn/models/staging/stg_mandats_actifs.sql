

with organes as (
    select
      uid as organe_uid,
      circo_dep_code,
      circo_dep_libelle,
      circo_numero,
      circo_region_type,
      circo_region_libelle,
      date_fin,
      code_type
    from {{ source('raw_parleman', 'organes') }}
)

SELECT 
    o.organe_uid, 
    o.circo_dep_code, 
    o.circo_dep_libelle, 
    o.circo_numero, 
    o.circo_region_type, 
    o.circo_region_libelle
FROM organes o
WHERE o.date_fin is null
AND o.code_type = 'CIRCONSCRIPTION'