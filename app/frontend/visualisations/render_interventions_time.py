from __future__ import annotations

import pandas as pd
import streamlit as st


def render_interventions_time(frame: pd.DataFrame) -> None:
    st.subheader("Interventions dans le temps")
    series = frame.copy()
    series["date_seance"] = pd.to_datetime(series["date_seance"], errors="coerce")
    series = series.dropna(subset=["date_seance"]).sort_values("date_seance")
    if series.empty:
        st.info("Aucune date valide disponible pour la série temporelle.")
        return

    chart_frame = series.set_index("date_seance")[
        ["nb_interventions", "nb_orateurs", "nb_comptes_rendus"]
    ]
    st.line_chart(chart_frame)

    if "legislature" in series.columns:
        by_legislature = series.groupby("legislature")[
            ["nb_interventions", "nb_orateurs"]
        ].sum()
        st.caption("Interventions par législature")
        st.bar_chart(by_legislature)
