

with scrutin_groupes_votes as (
    select groupe_organe_ref,
           organe_ref_assemblee,
           scrutin_uid,
           nombre_membres_groupe,
           position_majoritaire,
           non_votants,
           pour,
           contre,
           abstentions,
           non_votants_volontaires
    from {{ source('raw_parleman', 'scrutin_groupes_votes') }}
)

select
    groupe_organe_ref as groupe_uid,
    organe_ref_assemblee as assemblee_uid,
    scrutin_uid,
    nombre_membres_groupe,
    position_majoritaire,
    non_votants,
    pour,
    contre,
    abstentions,
    non_votants_volontaires
from scrutin_groupes_votes