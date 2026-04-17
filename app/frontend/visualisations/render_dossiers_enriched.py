from __future__ import annotations

import pandas as pd
import streamlit as st


def render_dossiers_enriched(frame: pd.DataFrame) -> None:
    st.subheader("Dossiers législatifs")
    if "titre_dossier" in frame.columns:
        top = frame.nlargest(min(15, len(frame)), "nombre_actes_total")
        st.caption("Dossiers avec le plus d'actes")
        st.bar_chart(
            top.set_index("titre_dossier")[
                ["nombre_actes_total", "nombre_documents_total"]
            ]
        )

    scatter_columns = [
        column
        for column in [
            "nombre_actes_total",
            "nombre_documents_total",
            "nombre_scrutins_total",
            "nombre_amendements_total",
        ]
        if column in frame.columns
    ]
    if len(scatter_columns) >= 2:
        scatter = frame[scatter_columns].dropna()
        if not scatter.empty:
            st.caption("Taille des dossiers vs volume de votes/amendements")
            st.scatter_chart(scatter, x=scatter_columns[0], y=scatter_columns[1])

    vote_columns = [
        column
        for column in [
            "volume_votes_pour",
            "volume_votes_contre",
            "volume_votes_abstentions",
        ]
        if column in frame.columns
    ]
    if len(vote_columns) == 3 and "titre_dossier" in frame.columns:
        top_votes = frame.nlargest(min(10, len(frame)), "volume_votants_total")
        st.caption("Volumes de vote pour les dossiers les plus votés")
        st.bar_chart(top_votes.set_index("titre_dossier")[vote_columns])
