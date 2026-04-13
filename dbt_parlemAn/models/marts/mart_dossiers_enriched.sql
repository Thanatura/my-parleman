{{ config(materialized='table') }}

with dossiers as (
    select
        dossier_uid,
        legislature,
        titre_dossier,
        titre_chemin,
        procedure_parlementaire_code,
        procedure_parlementaire_libelle,
        initiateur_acteur_ref,
        initiateur_mandat_ref,
        initiateur_organe_ref
    from {{ ref('stg_dossiers_parlementaires') }}
),

actes as (
    select
        dossier_uid,
        date_premier_acte,
        date_dernier_acte,
        nombre_actes_total,
        est_adopte
    from {{ ref('int_dossier_actes') }}
),

documents as (
    select
        dossier_uid,
        nombre_documents_total
    from {{ ref('int_dossier_documents') }}
),

scrutins as (
    select
        dossier_uid,
        nombre_scrutins_total,
        nombre_scrutins_adoptes,
        nombre_scrutins_rejetes,
        volume_votants_total,
        volume_votes_pour,
        volume_votes_contre,
        volume_votes_abstentions
    from {{ ref('int_dossier_scrutins') }}
),

amendements as (
    select
        dossier_uid,
        nombre_amendements_total,
        nombre_amendements_adoptes,
        nombre_amendements_rejetes
    from {{ ref('int_dossier_amendements') }}
)

select
    d.dossier_uid,
    d.legislature,
    d.titre_dossier,
    d.titre_chemin,
    d.procedure_parlementaire_code,
    d.procedure_parlementaire_libelle,
    d.initiateur_acteur_ref,
    d.initiateur_mandat_ref,
    d.initiateur_organe_ref,
    
    a.date_premier_acte,
    a.date_dernier_acte,
    coalesce(a.nombre_actes_total, 0) as nombre_actes_total,
    coalesce(a.est_adopte, false) as est_adopte,
    
    coalesce(doc.nombre_documents_total, 0) as nombre_documents_total,
    
    coalesce(s.nombre_scrutins_total, 0) as nombre_scrutins_total,
    coalesce(s.nombre_scrutins_adoptes, 0) as nombre_scrutins_adoptes,
    coalesce(s.nombre_scrutins_rejetes, 0) as nombre_scrutins_rejetes,
    
    coalesce(s.volume_votants_total, 0) as volume_votants_total,
    coalesce(s.volume_votes_pour, 0) as volume_votes_pour,
    coalesce(s.volume_votes_contre, 0) as volume_votes_contre,
    coalesce(s.volume_votes_abstentions, 0) as volume_votes_abstentions,
    
    coalesce(amd.nombre_amendements_total, 0) as nombre_amendements_total,
    coalesce(amd.nombre_amendements_adoptes, 0) as nombre_amendements_adoptes,
    coalesce(amd.nombre_amendements_rejetes, 0) as nombre_amendements_rejetes

from dossiers d
left join actes a using (dossier_uid)
left join documents doc using (dossier_uid)
left join scrutins s using (dossier_uid)
left join amendements amd using (dossier_uid)
