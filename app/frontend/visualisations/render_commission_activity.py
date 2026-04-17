from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def render_commission_activity(frame: pd.DataFrame) -> None:
    st.subheader("Activité des commissions")
    top = frame.nlargest(min(15, len(frame)), "nb_interventions_des_membres")
    st.caption("Commissions classées par interventions des membres")
    st.bar_chart(
        top.set_index("commission_libelle_abrege")[
            ["nb_interventions_des_membres", "nb_deputes"]
        ]
    )

    scatter_columns = [
        column
        for column in [
            "commission_libelle",
            "commission_libelle_abrege",
            "nb_deputes",
            "nb_interventions_des_membres",
            "nb_orateurs",
        ]
        if column in frame.columns
    ]
    scatter = frame[scatter_columns].dropna(
        subset=[
            column
            for column in ["nb_deputes", "nb_interventions_des_membres"]
            if column in frame.columns
        ]
    )
    if not scatter.empty:
        st.caption("Membres vs interventions")
        hover_name = (
            "commission_libelle"
            if "commission_libelle" in scatter.columns
            else (
                "commission_libelle_abrege"
                if "commission_libelle_abrege" in scatter.columns
                else None
            )
        )
        hover_data = {
            column: True
            for column in ["commission_libelle_abrege", "nb_orateurs"]
            if column in scatter.columns and column != hover_name
        }
        fig = px.scatter(
            scatter,
            x="nb_deputes",
            y="nb_interventions_des_membres",
            hover_name=hover_name,
            hover_data=hover_data or None,
        )
        fig.update_traces(marker={"size": 10, "opacity": 0.8})
        fig.update_layout(
            xaxis_title="Nombre de députés",
            yaxis_title="Nombre d'interventions des membres",
            height=480,
        )
        st.plotly_chart(fig, use_container_width=True)
