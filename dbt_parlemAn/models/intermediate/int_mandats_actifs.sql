{{ config(materialized='view') }}

with organes as (    
    select *
    from {{ ref('stg_organes') }}
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