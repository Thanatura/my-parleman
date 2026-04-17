from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend.visualisations.overview import show_summary
from frontend.visualisations.types import Renderer


def render_dedicated_visualisations(
    table_name: str, frame: pd.DataFrame, visualizers: dict[str, Renderer]
) -> None:
    if frame.empty:
        st.info("Aucune ligne à visualiser.")
        return

    show_summary(frame)

    visualizer = visualizers.get(table_name)
    if visualizer is None:
        st.info(
            "Aucun modèle de visualisation dédié n'existe pour cette mart. Le tableau brut est affiché à la place."
        )
        st.dataframe(frame, use_container_width=True)
        return

    visualizer(frame)
