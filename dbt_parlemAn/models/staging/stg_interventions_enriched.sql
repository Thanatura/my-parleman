

with interventions as (
    select
      compte_rendu_uid,
      point_id,
      point_valeur_ptsodj,
      intervention_id,
      ordre_absolu_seance,
      ordinal_prise,
      code_grammaire,
      code_style,
      code_parole,
      roledebat,
      orateur_nom,
      orateur_id,
      orateur_qualite,
      texte
    from {{ source('raw_parleman', 'interventions') }}
),
comptes_rendus as (
    select
      uid,
      safe_cast(date_seance as date) as date_seance,
      legislature,
      session,
      num_seance
    from {{ source('raw_parleman', 'comptes_rendus') }}
),
deputes as (
    select
      uid as depute_uid,
      concat(coalesce(prenom, ''), ' ', coalesce(nom, '')) as nom_complet,
      trigramme,
      profession_categorie,
      profession_famille
    from {{ source('raw_parleman', 'acteurs') }}
)

select
  i.intervention_id,
  i.compte_rendu_uid,
  i.point_id,
  i.point_valeur_ptsodj,
  cr.date_seance,
  cr.legislature,
  cr.session,
  cr.num_seance,
  i.roledebat,
  i.texte,
  case
    when i.orateur_id is null then null
    else concat('PA', cast(i.orateur_id as string))
  end as depute_uid,
  coalesce(d.nom_complet, i.orateur_nom) as orateur_nom,
  d.trigramme,
  d.profession_categorie,
  d.profession_famille
from interventions i
left join comptes_rendus cr
  on i.compte_rendu_uid = cr.uid
left join deputes d
  on case when i.orateur_id is null then null else concat('PA', cast(i.orateur_id as string)) end = d.depute_uid
