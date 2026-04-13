{{ config(materialized='table') }}

with votes_groupes as (
    select
        scrutin_uid,
        groupe_organe_ref,
        position_majoritaire,
        organe_ref_assemblee,
        pour,
        contre,
        abstentions
    from {{ ref('stg_scrutin_groupes_votes') }}
),

actes as (
    select
        dossier_uid,
        vote_ref as scrutin_uid
    from {{ ref('stg_dossier_actes_legislatifs') }}
    where vote_ref is not null
),

dossiers as (
    select
        d.dossier_uid,
        d.titre_dossier,
        d.legislature,
        coalesce(ia.est_adopte, false) as est_adopte
    from {{ ref('stg_dossiers_parlementaires') }} d
    left join {{ ref('int_dossier_actes') }} ia using (dossier_uid)
),

organes as (
    select
        organe_uid,
        libelle as groupe_libelle,
        libelle_abrege as groupe_libelle_abrege
    from {{ ref('stg_organes') }}
)

select
    d.dossier_uid,
    d.titre_dossier,
    d.legislature,
    d.est_adopte,
    v.groupe_organe_ref,
    o.groupe_libelle,
    o.groupe_libelle_abrege,
    v.organe_ref_assemblee,
    
    count(v.scrutin_uid) as total_scrutins_participes,
    
    coalesce(sum(v.pour), 0) as volume_total_pour,
    coalesce(sum(v.contre), 0) as volume_total_contre,
    coalesce(sum(v.abstentions), 0) as volume_total_abstention

from votes_groupes v
inner join actes a on v.scrutin_uid = a.scrutin_uid
inner join dossiers d on a.dossier_uid = d.dossier_uid
left join organes o on v.groupe_organe_ref = o.organe_uid
group by 1, 2, 3, 4, 5, 6, 7, 8
