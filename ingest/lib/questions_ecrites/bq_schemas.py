from google.cloud import bigquery


QUESTIONS_ECRITES_SCHEMAS: dict[str, list[bigquery.SchemaField]] = {
    "questions_ecrites": [
        bigquery.SchemaField("uid", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("numero", "STRING"),
        bigquery.SchemaField("regime", "STRING"),
        bigquery.SchemaField("legislature", "STRING"),
        bigquery.SchemaField("type", "STRING"),
        bigquery.SchemaField("rubrique", "STRING"),
        bigquery.SchemaField("tete_analyse", "STRING"),
        bigquery.SchemaField("analyse", "STRING"),
        bigquery.SchemaField("auteur_acteur_ref", "STRING"),
        bigquery.SchemaField("auteur_mandat_ref", "STRING"),
        bigquery.SchemaField("auteur_groupe_organe_ref", "STRING"),
        bigquery.SchemaField("auteur_groupe_abrege", "STRING"),
        bigquery.SchemaField("auteur_groupe_developpe", "STRING"),
        bigquery.SchemaField("min_int_organe_ref", "STRING"),
        bigquery.SchemaField("min_int_abrege", "STRING"),
        bigquery.SchemaField("min_int_developpe", "STRING"),
        bigquery.SchemaField("texte_question", "STRING"),
        bigquery.SchemaField("date_jo_question", "DATE"),
        bigquery.SchemaField("page_jo_question", "STRING"),
        bigquery.SchemaField("texte_reponse", "STRING"),
        bigquery.SchemaField("date_jo_reponse", "DATE"),
        bigquery.SchemaField("page_jo_reponse", "STRING"),
    ],
    "questions_ecrites_min_attribs": [
        bigquery.SchemaField("question_uid", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("type_jo", "STRING"),
        bigquery.SchemaField("date_jo", "DATE"),
        bigquery.SchemaField("organe_ref", "STRING"),
        bigquery.SchemaField("abrege", "STRING"),
        bigquery.SchemaField("developpe", "STRING"),
    ],
    "questions_ecrites_renouvellements": [
        bigquery.SchemaField("question_uid", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("type_jo", "STRING"),
        bigquery.SchemaField("date_jo", "DATE"),
        bigquery.SchemaField("num_jo", "STRING"),
    ],
}
