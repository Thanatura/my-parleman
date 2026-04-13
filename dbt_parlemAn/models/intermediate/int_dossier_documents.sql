{{ config(materialized='view') }}

with documents as (
    select
        dossier_uid,
        document_uid,
        type_code
    from {{ ref('stg_documents') }}
)

select
    dossier_uid,
    count(distinct document_uid) as nombre_documents_total
from documents
where dossier_uid is not null
group by 1
