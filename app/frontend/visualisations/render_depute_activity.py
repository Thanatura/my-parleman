from __future__ import annotations

import pandas as pd
import streamlit as st


def _safe_datetime_series(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_datetime(frame[column], errors="coerce")


def render_depute_activity(frame: pd.DataFrame) -> None:
    st.subheader("Activité des députés")
    top = frame.nlargest(min(15, len(frame)), "nb_interventions")
    st.caption("Députés les plus actifs par nombre d'interventions")
    st.bar_chart(top.set_index("nom_complet")[["nb_interventions"]])

    scatter = frame[["nb_mandats", "nb_interventions"]].dropna()
    if not scatter.empty:
        st.caption("Mandats vs interventions")
        st.scatter_chart(scatter, x="nb_mandats", y="nb_interventions")

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
