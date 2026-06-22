

with documents as (
    select
        dossier_ref as dossier_uid,
        uid as document_uid,
        type_code
    from {{ source('raw_parleman', 'documents') }}
)

select
    dossier_uid,
    count(distinct document_uid) as nombre_documents_total
from documents
where dossier_uid is not null
group by 1
