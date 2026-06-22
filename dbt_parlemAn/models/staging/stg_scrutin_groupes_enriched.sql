with groupes as (
  select groupe_uid,
    groupe_libelle,
    gp_position_politique,
    gp_couleur,
    groupe_legislature,
    groupe_date_debut,
    groupe_date_fin,
  from {{ ref('stg_groupes') }}
),
scrutins_groupes as (
  select scrutin_uid,
    position_majoritaire,
    groupe_uid
  from {{ ref('stg_scrutin_groupes') }}
)
select g.groupe_uid,
  g.groupe_libelle,
  g.gp_position_politique,
  g.gp_couleur,
  g.groupe_legislature,
  g.groupe_date_debut,
  g.groupe_date_fin,
  s.scrutin_uid,
  s.position_majoritaire
from groupes g
  inner join scrutins_groupes s on g.groupe_uid = s.groupe_uid