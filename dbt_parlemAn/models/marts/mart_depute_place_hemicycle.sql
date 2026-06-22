with deputes_dans_partis as (
    select depute_uid,
        gp_libelle,
        gp_couleur
    from {{ ref('stg_depute_dans_partis') }}
),
liste_sieges as (
    select depute_uid,
        mandature_place_hemicycle
    from {{ ref('stg_liste_siege') }}
),
acteurs as (
    select uid as depute_uid,
        nom,
        prenom
    from {{ source('raw_parleman', 'acteurs') }}
)
SELECT DISTINCT dp.depute_uid,
    a.nom,
    a.prenom,
    ls.mandature_place_hemicycle,
    dp.gp_libelle,
    dp.gp_couleur
FROM deputes_dans_partis dp
    LEFT JOIN liste_sieges ls ON dp.depute_uid = ls.depute_uid
    LEFT JOIN acteurs a ON dp.depute_uid = a.depute_uid
ORDER BY ls.mandature_place_hemicycle