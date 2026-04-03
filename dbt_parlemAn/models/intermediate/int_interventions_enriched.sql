{{ config(materialized='view') }}

with interventions as (
    select *
    from {{ ref('stg_interventions') }}
),
deputes as (
    select *
    from {{ ref('stg_deputes') }}
)

select
  i.intervention_id,
  i.compte_rendu_uid,
  i.point_id,
  i.point_valeur_ptsodj,
  i.date_seance,
  i.legislature,
  i.session,
  i.num_seance,
  i.roledebat,
  i.texte,
  i.depute_uid,
  coalesce(d.nom_complet, i.orateur_nom) as orateur_nom,
  d.trigramme,
  d.profession_categorie,
  d.profession_famille
from interventions i
left join deputes d
  on i.depute_uid = d.depute_uid
