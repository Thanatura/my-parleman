from google.cloud import bigquery


AMENDEMENTS_SCHEMAS: dict[str, list[bigquery.SchemaField]] = {
    "amendements": [
        bigquery.SchemaField("uid", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("legislature", "STRING"),
        bigquery.SchemaField("numero_long", "STRING"),
        bigquery.SchemaField("numero_ordre_depot", "STRING"),
        bigquery.SchemaField("prefixe_organe_examen", "STRING"),
        bigquery.SchemaField("examen_ref", "STRING"),
        bigquery.SchemaField("texte_legislatif_ref", "STRING"),
        bigquery.SchemaField("division_titre", "STRING"),
        bigquery.SchemaField("article_designation_courte", "STRING"),
        bigquery.SchemaField("division_type", "STRING"),
        bigquery.SchemaField("dispositif", "STRING"),
        bigquery.SchemaField("expose_sommaire", "STRING"),
        bigquery.SchemaField("date_depot", "DATE"),
        bigquery.SchemaField("date_publication", "DATE"),
        bigquery.SchemaField("etat_code", "STRING"),
        bigquery.SchemaField("etat_libelle", "STRING"),
        bigquery.SchemaField("sous_etat_code", "STRING"),
        bigquery.SchemaField("sous_etat_libelle", "STRING"),
        bigquery.SchemaField("sort", "STRING"),
        bigquery.SchemaField("auteur_type", "STRING"),
        bigquery.SchemaField("auteur_acteur_ref", "STRING"),
        bigquery.SchemaField("auteur_groupe_politique_ref", "STRING"),
        bigquery.SchemaField("dossier_legislatif_ref", "STRING"),
    ],
    "amendement_signataires": [
        bigquery.SchemaField("amendement_uid", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("acteur_ref", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("type_auteur", "STRING"),
        bigquery.SchemaField("groupe_politique_ref", "STRING"),
        bigquery.SchemaField("ordre_presentation", "INTEGER"),
    ],
    "amendement_cosignataires": [
        bigquery.SchemaField("amendement_uid", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("cosignataire_acteur_ref", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("ordre_presentation", "INTEGER"),
    ],
}
