

with organes as (
    select
      uid as organe_uid,
      libelle,
      libelle_abrev,
      gp_position_politique,
      gp_couleur,
      legislature,
      date_debut,
      date_fin,
      code_type
    from {{ source('raw_parleman', 'organes') }}
)
select
      organe_uid as groupe_uid,
      libelle as groupe_libelle,
      libelle_abrev as groupe_libelle_abrev,
      gp_position_politique,
      gp_couleur,
      legislature as groupe_legislature,
      date_debut as groupe_date_debut,
      date_fin as groupe_date_fin
    from organes
    where lower(coalesce(code_type, '')) in ('gp', 'groupepolitique')
       or lower(coalesce(libelle, '')) like '%groupe%'
