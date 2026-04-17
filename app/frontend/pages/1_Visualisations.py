from __future__ import annotations


import streamlit as st


from frontend.shared import DEFAULT_API_URL, fetch_json, load_mart_frame, load_marts
from frontend.visualisations import (
    build_visualizers,
    render_dedicated_visualisations,
)


st.set_page_config(page_title="Visualisations dédiées", layout="wide")
st.title("Visualisations dédiées")

api_base_url = DEFAULT_API_URL.rstrip("/")
limit = 500

visualizers = build_visualizers(api_base_url)

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

selected_mart = st.selectbox("Sélectionnez une table mart", options=visualizers.keys())

try:
    payload, frame = load_mart_frame(api_base_url, selected_mart, limit)
except Exception as exc:
    st.error(f"Impossible de charger les données de la table : {exc}")
    st.stop()

st.caption(
    f"Projet : {payload['project']} | Jeu de données : {payload['dataset']} | Lignes renvoyées : {payload['row_count']}"
)

if frame.empty:
    st.info("Aucune ligne renvoyée pour cette table et cette limite.")
    st.stop()

render_dedicated_visualisations(selected_mart, frame, visualizers)
