"""
Dashboard page for ESG Data Collector.
Displays KPI cards, radar chart, score distribution, and top/bottom performers.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import (
    create_category_comparison,
    create_esg_radar_chart,
    create_risk_heatmap,
    create_score_distribution,
)
from src.database import get_assessments, get_suppliers
from src.scoring import (
    RISK_COLOR_MAP,
    calculate_category_scores,
    calculate_overall_score,
    get_risk_distribution,
)


def _render_kpi_cards(
    suppliers: list[dict],
    overall_scores: pd.DataFrame,
    assessments: list[dict],
) -> None:
    """Render the four top-level KPI metric cards."""
    total_suppliers = len(suppliers)
    avg_score = overall_scores["overall_score"].mean() if not overall_scores.empty else 0.0
    assessment_count = len(assessments)

    risk_dist = get_risk_distribution(overall_scores)
    critical_high = risk_dist.get("Critical", 0) + risk_dist.get("High", 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Suppliers", total_suppliers)
    with col2:
        st.metric("Avg ESG Score", f"{avg_score:.1f} / 100")
    with col3:
        st.metric("Total Assessments", assessment_count)
    with col4:
        st.metric("Critical / High Risk", critical_high, delta=None)


def _render_radar_section(overall_scores: pd.DataFrame) -> None:
    """Render the average E/S/G radar chart."""
    if overall_scores.empty:
        st.info("No scoring data yet. Add assessments in the Data Entry page.")
        return

    avg_scores: dict[str, float] = {
        "Environmental": float(overall_scores["environmental_score"].mean()),
        "Social": float(overall_scores["social_score"].mean()),
        "Governance": float(overall_scores["governance_score"].mean()),
    }
    fig = create_esg_radar_chart(avg_scores)
    st.plotly_chart(fig, use_container_width=True)


def _render_risk_badges(overall_scores: pd.DataFrame) -> None:
    """Show a compact risk summary table with colour-coded badges."""
    if overall_scores.empty:
        return

    st.subheader("Supplier Risk Summary")
    display_df = overall_scores[
        ["supplier_name", "overall_score", "risk_level"]
    ].copy()
    display_df.columns = ["Supplier", "Overall Score", "Risk Level"]
    st.dataframe(
        display_df.style.applymap(  # type: ignore[attr-defined]
            lambda val: f"color: {RISK_COLOR_MAP.get(val, 'black')}; font-weight: bold;",
            subset=["Risk Level"],
        ),
        use_container_width=True,
        hide_index=True,
    )


def render() -> None:
    """Entry point called by app.py to render the Dashboard page."""
    st.title("ESG Dashboard")
    st.markdown("Overview of ESG performance across all tracked suppliers.")

    raw_suppliers = get_suppliers()
    raw_assessments = get_assessments()

    assessments_df = pd.DataFrame(raw_assessments) if raw_assessments else pd.DataFrame()

    if assessments_df.empty:
        _render_kpi_cards(raw_suppliers, pd.DataFrame(), raw_assessments)
        st.info(
            "No assessment data available. "
            "Navigate to **Data Entry** to add suppliers and assessments."
        )
        return

    category_scores = calculate_category_scores(assessments_df)
    overall_scores = calculate_overall_score(category_scores)

    _render_kpi_cards(raw_suppliers, overall_scores, raw_assessments)

    st.divider()

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Category Scores (Portfolio Average)")
        _render_radar_section(overall_scores)

    with right:
        st.subheader("Assessment Score Distribution")
        fig_dist = create_score_distribution(assessments_df)
        st.plotly_chart(fig_dist, use_container_width=True)

    st.divider()

    st.subheader("Supplier Performance Comparison")
    fig_compare = create_category_comparison(overall_scores)
    st.plotly_chart(fig_compare, use_container_width=True)

    st.divider()

    left2, right2 = st.columns([1, 1])
    with left2:
        _render_risk_badges(overall_scores)
    with right2:
        st.subheader("Risk Heatmap")
        fig_heat = create_risk_heatmap(category_scores)
        st.plotly_chart(fig_heat, use_container_width=True)
