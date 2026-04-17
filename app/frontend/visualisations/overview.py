from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend.shared import summarize_columns


def show_summary(frame: pd.DataFrame) -> None:
    numeric_columns, categorical_columns = summarize_columns(frame)
    col_left, col_right = st.columns(2)

    with col_left:
        st.metric("Lignes chargées", len(frame))
        st.metric("Colonnes numériques", len(numeric_columns))

    with col_right:
        st.metric("Colonnes catégorielles", len(categorical_columns))
        st.metric("Colonnes distinctes", frame.nunique(dropna=True).shape[0])
