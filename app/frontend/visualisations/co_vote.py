from __future__ import annotations

from collections.abc import Callable, Mapping
from html import escape
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from frontend.shared import load_group_lookup


def _safe_color(value: str) -> str:
    value = (value or "").strip()
    if value.startswith("#") and len(value) in {4, 7}:
        return value
    return "#1f77b4"


def _build_metadata_provider(
    group_lookup: pd.DataFrame,
) -> Callable[[object], Mapping[str, str]]:
    lookup_columns = [
        "groupe_uid",
        "groupe_libelle",
        "groupe_libelle_abrev",
        "gp_couleur",
    ]
    if not group_lookup.empty:
        available_lookup_columns = [
            column for column in lookup_columns if column in group_lookup.columns
        ]
        if "groupe_uid" in available_lookup_columns:
            lookup_frame = group_lookup[available_lookup_columns].drop_duplicates(
                "groupe_uid"
            )
        else:
            lookup_frame = pd.DataFrame(columns=lookup_columns)
    else:
        lookup_frame = pd.DataFrame(columns=lookup_columns)

    def _metadata_for(group_uid: object) -> dict[str, str]:
        group_uid_str = str(group_uid)
        if not lookup_frame.empty and "groupe_uid" in lookup_frame.columns:
            match = lookup_frame[
                lookup_frame["groupe_uid"].astype(str) == group_uid_str
            ]
            if not match.empty:
                row = match.iloc[0]
                return {
                    "uid": group_uid_str,
                    "label": str(row.get("groupe_libelle") or group_uid_str),
                    "abbrev": str(
                        row.get("groupe_libelle_abrev")
                        or row.get("groupe_libelle")
                        or group_uid_str
                    ),
                    "color": str(row.get("gp_couleur") or "#1f77b4"),
                }

        short_label = group_uid_str[:8]
        return {
            "uid": group_uid_str,
            "label": group_uid_str,
            "abbrev": short_label,
            "color": "#1f77b4",
        }

    return _metadata_for


def _render_groupes_co_vote_table(
    pair_frame: pd.DataFrame, metadata_for: Callable[[object], Mapping[str, str]]
) -> None:
    st.caption("Principaux couples de co-vote")
    display_pairs = pair_frame.copy()
    display_pairs["groupe_1_abbrev"] = display_pairs["groupe_uid_1"].map(
        lambda value: metadata_for(value)["abbrev"]
    )
    display_pairs["groupe_1_label"] = display_pairs["groupe_uid_1"].map(
        lambda value: metadata_for(value)["label"]
    )
    display_pairs["groupe_1_color"] = display_pairs["groupe_uid_1"].map(
        lambda value: metadata_for(value)["color"]
    )
    display_pairs["groupe_2_abbrev"] = display_pairs["groupe_uid_2"].map(
        lambda value: metadata_for(value)["abbrev"]
    )
    display_pairs["groupe_2_label"] = display_pairs["groupe_uid_2"].map(
        lambda value: metadata_for(value)["label"]
    )
    display_pairs["groupe_2_color"] = display_pairs["groupe_uid_2"].map(
        lambda value: metadata_for(value)["color"]
    )
    st.dataframe(
        display_pairs[
            [
                "groupe_1_abbrev",
                "groupe_1_label",
                "groupe_1_color",
                "groupe_2_abbrev",
                "groupe_2_label",
                "groupe_2_color",
                "nb_co_votes",
            ]
        ],
        use_container_width=True,
    )


def _render_groupes_co_vote_matrix(
    pair_frame: pd.DataFrame, node_metadata: list[Mapping[str, str]]
) -> None:
    heatmap = pair_frame.pivot_table(
        index="groupe_uid_1",
        columns="groupe_uid_2",
        values="nb_co_votes",
        fill_value=0,
        aggfunc="max",
    )
    if heatmap.empty:
        return

    uid_to_meta = {str(node["uid"]): node for node in node_metadata}

    uid_to_abbrev: dict[str, str] = {}
    used_abbrev: dict[str, int] = {}
    for uid, meta in uid_to_meta.items():
        base = str(meta.get("abbrev") or uid)
        occurrence = used_abbrev.get(base, 0)
        used_abbrev[base] = occurrence + 1
        if occurrence == 0:
            uid_to_abbrev[uid] = base
        else:
            uid_to_abbrev[uid] = f"{base} ({uid[:6]})"

    labelled_heatmap = heatmap.copy()
    labelled_heatmap.index = [
        uid_to_abbrev.get(str(uid), str(uid)) for uid in labelled_heatmap.index
    ]
    labelled_heatmap.columns = [
        uid_to_abbrev.get(str(uid), str(uid)) for uid in labelled_heatmap.columns
    ]

    st.caption("Matrice des couples (vue tableau)")
    st.dataframe(labelled_heatmap, use_container_width=True)


def render_groupes_co_vote(frame: pd.DataFrame, api_base_url: str) -> None:
    st.subheader("Co-vote entre groupes")
    try:
        group_lookup = load_group_lookup(api_base_url)
    except Exception as exc:
        st.warning(f"Impossible de charger les métadonnées des groupes : {exc}")
        group_lookup = pd.DataFrame()

    pair_frame = frame.copy()
    if pair_frame.empty:
        st.info("Aucun couple de co-vote disponible.")
        return

    max_votes = int(pair_frame["nb_co_votes"].max())
    min_votes = st.slider(
        "Nombre minimal de co-votes à afficher",
        min_value=1,
        max_value=max(1, max_votes),
        value=max(1, min(max_votes, 1000)),
        step=1,
        key="covote-min-votes",
    )
    pair_frame = pair_frame[pair_frame["nb_co_votes"] >= min_votes].copy()
    pair_frame = pair_frame.nlargest(min(50, len(pair_frame)), "nb_co_votes")
    if pair_frame.empty:
        st.info("Aucun couple de co-vote ne correspond au seuil sélectionné.")
        return

    metadata_for = _build_metadata_provider(group_lookup)

    group_ids = sorted(
        set(pair_frame["groupe_uid_1"].astype(str))
        | set(pair_frame["groupe_uid_2"].astype(str))
    )
    totals_by_group = (
        pd.concat(
            [
                pair_frame[["groupe_uid_1", "nb_co_votes"]].rename(
                    columns={"groupe_uid_1": "groupe_uid"}
                ),
                pair_frame[["groupe_uid_2", "nb_co_votes"]].rename(
                    columns={"groupe_uid_2": "groupe_uid"}
                ),
            ],
            ignore_index=True,
        )
        .assign(groupe_uid=lambda data: data["groupe_uid"].astype(str))
        .groupby("groupe_uid")["nb_co_votes"]
        .sum()
        .to_dict()
    )
    ordered_group_ids = [
        str(group_id)
        for group_id, _ in sorted(
            totals_by_group.items(), key=lambda item: item[1], reverse=True
        )
    ]
    for group_id in group_ids:
        if group_id not in ordered_group_ids:
            ordered_group_ids.append(group_id)

    node_metadata = [metadata_for(group_id) for group_id in ordered_group_ids]
    node_count = len(node_metadata)
    radius = 1.0
    total_counts = {
        str(group_id): float(value) for group_id, value in totals_by_group.items()
    }

    def _node_size(node: Mapping[str, str]) -> int:
        score = float(total_counts.get(node["uid"], 0))
        return int(20 + min(20, score / 250))

    positions = {
        node["uid"]: (
            radius * math.cos((2 * math.pi * index) / max(node_count, 1)),
            radius * math.sin((2 * math.pi * index) / max(node_count, 1)),
        )
        for index, node in enumerate(node_metadata)
    }

    fig = go.Figure()
    max_weight = max(float(pair_frame["nb_co_votes"].max()), 1.0)
    for _, row in pair_frame.iterrows():
        left = metadata_for(row["groupe_uid_1"])
        right = metadata_for(row["groupe_uid_2"])
        x0, y0 = positions[left["uid"]]
        x1, y1 = positions[right["uid"]]
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line={
                    "color": "rgba(120, 120, 120, 0.25)",
                    "width": max(1.0, 8.0 * float(row["nb_co_votes"]) / max_weight),
                },
                hoverinfo="skip",
                showlegend=False,
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[positions[node["uid"]][0] for node in node_metadata],
            y=[positions[node["uid"]][1] for node in node_metadata],
            mode="markers+text",
            text=[node["abbrev"] for node in node_metadata],
            textposition="top center",
            hovertext=[
                f"{node['abbrev']}<br>{node['label']}<br>Couleur: {node['color']}"
                for node in node_metadata
            ],
            hoverinfo="text",
            marker={
                "size": [_node_size(node) for node in node_metadata],
                "color": [_safe_color(str(node["color"])) for node in node_metadata],
                "line": {"width": 1, "color": "#222"},
            },
            customdata=[node["label"] for node in node_metadata],
            showlegend=False,
        )
    )

    fig.update_layout(
        title="Réseau de co-vote",
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        height=700,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Légende des groupes")
    legend_items = []
    for node in node_metadata:
        legend_items.append(
            "<span style='display:inline-flex;align-items:center;margin:0 18px 8px 0;'>"
            f"<span style='display:inline-block;width:12px;height:12px;border-radius:999px;background:{escape(_safe_color(str(node['color'])))};margin-right:8px;border:1px solid #333;'></span>"
            f"<strong style='margin-right:6px;'>{escape(str(node['abbrev']))}</strong>"
            f"<span>{escape(str(node['label']))}</span>"
            "</span>"
        )
    st.markdown(
        "<div style='display:flex;flex-wrap:wrap;'>" + "".join(legend_items) + "</div>",
        unsafe_allow_html=True,
    )

    _render_groupes_co_vote_matrix(pair_frame, node_metadata)
    _render_groupes_co_vote_table(pair_frame, metadata_for)
