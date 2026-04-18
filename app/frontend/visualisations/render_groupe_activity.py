from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def render_groupe_activity(frame: pd.DataFrame) -> None:
    st.subheader("Activité des groupes politiques")
    top = frame.nlargest(min(15, len(frame)), "nb_interventions")
    st.caption("Groupes les plus actifs par nombre d'interventions")
    st.bar_chart(top.set_index("groupe_libelle")[["nb_interventions", "nb_deputes"]])

    scatter_columns = [
        column
        for column in [
            "groupe_libelle",
            "groupe_libelle_abrege",
            "nb_deputes",
            "nb_interventions",
            "nb_orateurs",
        ]
        if column in frame.columns
    ]
    scatter = frame[scatter_columns].dropna(
        subset=[
            column
            for column in ["nb_deputes", "nb_interventions"]
            if column in frame.columns
        ]
    )
    if not scatter.empty:
        st.caption("Membres vs interventions")
        hover_name = (
            "groupe_libelle"
            if "groupe_libelle" in scatter.columns
            else (
                "groupe_libelle_abrege"
                if "groupe_libelle_abrege" in scatter.columns
                else None
            )
        )
        hover_data = {
            column: True
            for column in ["groupe_libelle_abrege", "nb_orateurs"]
            if column in scatter.columns and column != hover_name
        }
        fig = px.scatter(
            scatter,
            x="nb_deputes",
            y="nb_interventions",
            hover_name=hover_name,
            hover_data=hover_data or None,
        )
        fig.update_traces(marker={"size": 10, "opacity": 0.8})
        fig.update_layout(
            xaxis_title="Nombre de deputes",
            yaxis_title="Nombre d'interventions",
            height=480,
        )
        st.plotly_chart(fig, use_container_width=True)
