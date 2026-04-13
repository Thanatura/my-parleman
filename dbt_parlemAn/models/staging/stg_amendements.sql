{{ config(materialized='view') }}

select
  uid as amendement_uid,
  legislature,
  numero_long,
  numero_ordre_depot,
  prefixe_organe_examen,
  examen_ref,
  texte_legislatif_ref,
  dossier_legislatif_ref,
  division_titre,
  article_designation_courte,
  division_type,
  -- We don't bring in large text fields like dispositif/expose_sommaire unless needed for NLP, 
  -- but let's leave them out for analytical staging unless specified.
  date_depot,
  date_publication,
  etat_code,
  etat_libelle,
  sous_etat_code,
  sous_etat_libelle,
  sort,
  auteur_type,
  auteur_acteur_ref,
  auteur_groupe_politique_ref
from {{ source('raw_parleman', 'amendements') }}
