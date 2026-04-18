from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def _safe_datetime_series(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_datetime(frame[column], errors="coerce")


def render_depute_activity(frame: pd.DataFrame) -> None:
    st.subheader("Activité des députés")
    top = frame.nlargest(min(15, len(frame)), "nb_interventions")
    st.caption("Députés les plus actifs par nombre d'interventions")
    st.bar_chart(top.set_index("nom_complet")[["nb_interventions"]])

    scatter_columns = [
        column
        for column in ["nom_complet", "nb_mandats", "nb_interventions"]
        if column in frame.columns
    ]
    scatter = frame[scatter_columns].dropna(
        subset=[column for column in ["nb_mandats", "nb_interventions"] if column in frame.columns]
    )
    if not scatter.empty:
        st.caption("Mandats vs interventions")
        hover_name = "nom_complet" if "nom_complet" in scatter.columns else None
        fig = px.scatter(
            scatter,
            x="nb_mandats",
            y="nb_interventions",
            hover_name=hover_name,
        )
        fig.update_traces(marker={"size": 10, "opacity": 0.8})
        fig.update_layout(
            xaxis_title="Nombre de mandats",
            yaxis_title="Nombre d'interventions",
            height=480,
        )
        st.plotly_chart(fig, use_container_width=True)

    timeline = frame[
        ["premiere_intervention", "derniere_intervention", "nom_complet"]
    ].copy()
    timeline["premiere_intervention"] = _safe_datetime_series(
        timeline, "premiere_intervention"
    )
    timeline["derniere_intervention"] = _safe_datetime_series(
        timeline, "derniere_intervention"
    )
    timeline = timeline.dropna(
        subset=["premiere_intervention", "derniere_intervention"]
    )
    if not timeline.empty:
        timeline["activity_span_days"] = (
            timeline["derniere_intervention"] - timeline["premiere_intervention"]
        ).dt.days
        st.caption("Durée d'activité (jours)")
        st.bar_chart(timeline.set_index("nom_complet")[["activity_span_days"]])
