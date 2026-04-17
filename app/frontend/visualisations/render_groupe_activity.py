from __future__ import annotations

import pandas as pd
import streamlit as st


def render_groupe_activity(frame: pd.DataFrame) -> None:
    st.subheader("Activité des groupes politiques")
    top = frame.nlargest(min(15, len(frame)), "nb_interventions")
    st.caption("Groupes les plus actifs par nombre d'interventions")
    st.bar_chart(top.set_index("groupe_libelle")[["nb_interventions", "nb_deputes"]])

    scatter = frame[["nb_deputes", "nb_interventions", "nb_orateurs"]].dropna()
    if not scatter.empty:
        st.caption("Membres vs interventions")
        st.scatter_chart(scatter, x="nb_deputes", y="nb_interventions")
