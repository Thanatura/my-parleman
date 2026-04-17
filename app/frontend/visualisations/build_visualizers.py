from __future__ import annotations

from frontend.visualisations.co_vote import render_groupes_co_vote
from frontend.visualisations.render_commission_activity import (
    render_commission_activity,
)
from frontend.visualisations.render_depute_activity import render_depute_activity
from frontend.visualisations.render_dossiers_enriched import (
    render_dossiers_enriched,
)
from frontend.visualisations.render_groupe_activity import render_groupe_activity
from frontend.visualisations.render_interventions_time import (
    render_interventions_time,
)
from frontend.visualisations.types import Renderer


def build_visualizers(api_base_url: str) -> dict[str, Renderer]:
    return {
        "mart_depute_activity": render_depute_activity,
        "mart_groupe_activity": render_groupe_activity,
        "mart_commission_activity": render_commission_activity,
        "mart_interventions_time": render_interventions_time,
        "mart_dossiers_enriched": render_dossiers_enriched,
        "mart_groupes_co_vote": lambda frame: render_groupes_co_vote(
            frame, api_base_url
        ),
    }
