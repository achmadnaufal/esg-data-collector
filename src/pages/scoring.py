"""
Scoring page for ESG Data Collector.
Displays per-supplier ESG scores, category breakdowns, and risk classifications.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import create_category_comparison, create_trend_chart
from src.database import get_assessments, get_suppliers
from src.scoring import (
    RISK_COLOR_MAP,
    calculate_category_scores,
    calculate_overall_score,
    classify_risk,
    get_risk_distribution,
)


def _render_overall_scores_table(overall_scores: pd.DataFrame) -> None:
    """Render the per-supplier overall score table with risk badges."""
    st.subheader("Overall ESG Scores per Supplier")

    display = overall_scores[
        [
            "supplier_name",
            "environmental_score",
            "social_score",
            "governance_score",
            "overall_score",
            "risk_level",
        ]
    ].copy()

    display.columns = [
        "Supplier",
        "Environmental (40%)",
        "Social (35%)",
        "Governance (25%)",
        "Overall Score",
        "Risk Level",
    ]

    styled = display.style.applymap(  # type: ignore[attr-defined]
        lambda val: f"color: {RISK_COLOR_MAP.get(val, 'black')}; font-weight: bold;",
        subset=["Risk Level"],
    ).format(
        {
            "Environmental (40%)": "{:.1f}",
            "Social (35%)": "{:.1f}",
            "Governance (25%)": "{:.1f}",
            "Overall Score": "{:.1f}",
        }
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)


def _render_risk_distribution(overall_scores: pd.DataFrame) -> None:
    """Show a breakdown of suppliers by risk level."""
    st.subheader("Risk Level Distribution")
    dist = get_risk_distribution(overall_scores)

    cols = st.columns(5)
    for idx, (level, count) in enumerate(dist.items()):
        color = RISK_COLOR_MAP.get(level, "#000000")
        with cols[idx]:
            st.markdown(
                f"<div style='text-align:center; padding:12px; "
                f"border-radius:8px; border: 2px solid {color};'>"
                f"<span style='font-size:28px; font-weight:bold; color:{color};'>{count}</span>"
                f"<br/><span style='font-size:12px; color:{color};'>{level}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )


def _render_supplier_drilldown(
    assessments_df: pd.DataFrame, suppliers: list[dict]
) -> None:
    """Render a per-supplier score drilldown section."""
    st.subheader("Supplier Drilldown")

    if not suppliers:
        st.info("No suppliers available.")
        return

    supplier_map: dict[str, int] = {s["name"]: s["id"] for s in suppliers}
    selected_name = st.selectbox(
        "Select Supplier", options=list(supplier_map.keys()), key="drilldown_supplier"
    )
    selected_id = supplier_map[selected_name]

    filtered = assessments_df[assessments_df["supplier_id"] == selected_id].copy()
    if filtered.empty:
        st.info(f"No assessments found for {selected_name}.")
        return

    display_cols = ["indicator_code", "indicator_name", "category", "score", "assessor", "assessed_date"]
    available = [c for c in display_cols if c in filtered.columns]
    detail_df = filtered[available].copy()
    detail_df.columns = [c.replace("_", " ").title() for c in detail_df.columns]
    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    cat_scores = calculate_category_scores(filtered)
    if not cat_scores.empty:
        overall = calculate_overall_score(cat_scores)
        if not overall.empty:
            row = overall.iloc[0]
            risk = classify_risk(float(row["overall_score"]))
            color = RISK_COLOR_MAP.get(risk, "#000")
            st.markdown(
                f"**Overall Score:** {row['overall_score']:.1f} — "
                f"<span style='color:{color}; font-weight:bold;'>{risk}</span>",
                unsafe_allow_html=True,
            )


def render() -> None:
    """Entry point called by app.py to render the Scoring page."""
    st.title("ESG Scoring")
    st.markdown(
        "Automatically calculated scores based on GRI indicator assessments. "
        "Weights: Environmental 40% · Social 35% · Governance 25%."
    )

    raw_assessments = get_assessments()
    raw_suppliers = get_suppliers()

    if not raw_assessments:
        st.info("No assessments found. Add assessments via the **Data Entry** page.")
        return

    assessments_df = pd.DataFrame(raw_assessments)
    category_scores = calculate_category_scores(assessments_df)
    overall_scores = calculate_overall_score(category_scores)

    _render_overall_scores_table(overall_scores)
    st.divider()
    _render_risk_distribution(overall_scores)
    st.divider()

    st.subheader("Category Score Comparison")
    fig_compare = create_category_comparison(overall_scores)
    st.plotly_chart(fig_compare, use_container_width=True)

    st.divider()

    st.subheader("Score Trend Over Time")
    fig_trend = create_trend_chart(assessments_df)
    st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()
    _render_supplier_drilldown(assessments_df, raw_suppliers)
