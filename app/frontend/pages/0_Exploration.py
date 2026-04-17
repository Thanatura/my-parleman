from __future__ import annotations


import pandas as pd
import streamlit as st

from frontend.shared import (
    DEFAULT_API_URL,
    fetch_json,
    load_mart_frame,
    load_marts,
    summarize_columns,
)


st.set_page_config(page_title="Exploration des marts", layout="wide")
st.title("Exploration des marts")

api_base_url = DEFAULT_API_URL.rstrip("/")
limit = 100  # Fixed default limit


def display_graphs(frame: pd.DataFrame, mart_name: str) -> None:
    numeric_columns, categorical_columns = summarize_columns(frame)

    st.subheader("Graphiques")

    col_left, col_right = st.columns(2)

    with col_left:
        if categorical_columns:
            category_column = st.selectbox(
                "Colonne catégorielle",
                options=categorical_columns,
                key=f"category-column-{mart_name}",
            )
            category_count = int(frame[category_column].nunique(dropna=True))
            if category_count > 1:
                top_n = st.slider(
                    "Catégories principales",
                    min_value=1,
                    max_value=min(25, category_count),
                    value=min(10, category_count),
                    key=f"top-categories-{category_column}",
                )
            else:
                top_n = 1
                st.caption(
                    "Une seule valeur de catégorie trouvée ; affichage de la distribution complète."
                )
            counts = (
                frame[category_column]
                .fillna("<missing>")
                .astype(str)
                .value_counts()
                .head(top_n)
            )
            st.caption(f"Répartition par {category_column}")
            st.bar_chart(counts)
        else:
            st.info(
                "Aucune colonne catégorielle de faible cardinalité n'a été trouvée pour un graphique en barres."
            )

    with col_right:
        if numeric_columns:
            numeric_column = st.selectbox(
                "Colonne numérique",
                options=numeric_columns,
                key=f"numeric-column-{mart_name}",
            )
            aggregations = {
                "Moyenne": "mean",
                "Somme": "sum",
                "Médiane": "median",
            }
            aggregation = st.selectbox(
                "Agrégation",
                options=list(aggregations.keys()),
                key=f"numeric-aggregation-{numeric_column}",
            )
            aggregation_fn = aggregations[aggregation]

            if categorical_columns:
                group_column = st.selectbox(
                    "Regrouper par",
                    options=categorical_columns,
                    key=f"group-column-{numeric_column}",
                )
                grouped = (
                    frame.groupby(frame[group_column].fillna("<missing>").astype(str))[
                        numeric_column
                    ]
                    .agg(aggregation_fn)
                    .sort_values(ascending=False)
                    .head(15)
                )
                st.caption(f"{aggregation} de {numeric_column} par {group_column}")
                st.bar_chart(grouped)
            else:
                series = frame[numeric_column].dropna().sort_index()
                if len(series) > 0:
                    st.caption(f"{numeric_column} selon l'index des lignes")
                    st.line_chart(series)
                else:
                    st.info(
                        f"Aucune donnée disponible pour la colonne numérique {numeric_column}."
                    )
        else:
            st.info(
                "Aucune colonne numérique n'a été trouvée pour un graphique numérique."
            )


try:
    health = fetch_json(api_base_url=api_base_url, path="/health")
    st.sidebar.success(f"Statut API : {health['status']}")
except Exception as exc:
    st.sidebar.error(f"API injoignable : {exc}")
    st.stop()

try:
    marts = load_marts(api_base_url)
except Exception as exc:
    st.error(f"Impossible de charger la liste des marts : {exc}")
    st.stop()

if not marts:
    st.warning("Aucune table mart_ trouvée dans le jeu de données BigQuery.")
    st.stop()

mart_names = [str(item["table_name"]) for item in marts]
selected_mart = st.selectbox("Sélectionnez une table mart", options=mart_names)

if st.button("Charger les données de la mart", type="primary"):
    try:
        data_payload, frame = load_mart_frame(api_base_url, selected_mart, limit)
    except Exception as exc:
        st.error(f"Impossible de charger les données de la table : {exc}")
        st.stop()

    st.caption(
        f"Projet : {data_payload['project']} | Jeu de données : {data_payload['dataset']} | Lignes renvoyées : {data_payload['row_count']}"
    )

    if frame.empty:
        st.info("Aucune ligne renvoyée pour cette table et cette limite.")
        st.stop()

    tab_table, tab_graphs = st.tabs(["Tableau", "Graphiques"])

    with tab_table:
        st.dataframe(frame, use_container_width=True)
        st.download_button(
            "Télécharger le CSV",
            data=frame.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected_mart}.csv",
            mime="text/csv",
        )

    with tab_graphs:
        display_graphs(frame, selected_mart)
