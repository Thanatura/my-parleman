{{ config(materialized='view') }}

with interventions as (
    select *
    from {{ source('raw_parleman', 'interventions') }}
),
comptes_rendus as (
    select *
    from {{ source('raw_parleman', 'comptes_rendus') }}
)

select
  i.compte_rendu_uid,
  i.point_id,
  i.point_valeur_ptsodj,
  i.intervention_id,
  i.ordre_absolu_seance,
  i.ordinal_prise,
  i.code_grammaire,
  i.code_style,
  i.code_parole,
  i.roledebat,
  i.orateur_nom,
  case
    when i.orateur_id is null then null
    else concat('PA', cast(i.orateur_id as string))
  end as depute_uid,
  i.orateur_qualite,
  i.texte,
  safe_cast(cr.date_seance as date) as date_seance,
  cr.legislature,
  cr.type_assemblee,
  cr.session,
  cr.num_seance
from interventions i
left join comptes_rendus cr
  on i.compte_rendu_uid = cr.uid
