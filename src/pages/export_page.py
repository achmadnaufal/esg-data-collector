"""
Export page for ESG Data Collector.
Provides CSV downloads and a plain-text summary report.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from src.database import get_assessments, get_evidence_files, get_suppliers
from src.export import export_to_csv, generate_report_summary
from src.scoring import calculate_category_scores, calculate_overall_score


def _build_full_export_df(
    suppliers: list[dict],
    assessments: list[dict],
    overall_scores: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """
    Assemble export-ready DataFrames for each data domain.
    Returns a dict keyed by sheet/file name.
    """
    suppliers_df = pd.DataFrame(suppliers) if suppliers else pd.DataFrame()
    assessments_df = pd.DataFrame(assessments) if assessments else pd.DataFrame()
    evidence_df = pd.DataFrame(get_evidence_files())

    return {
        "suppliers": suppliers_df,
        "assessments": assessments_df,
        "overall_scores": overall_scores,
        "evidence_files": evidence_df.drop(columns=[], errors="ignore"),
    }


def _render_download_buttons(export_frames: dict[str, pd.DataFrame]) -> None:
    """Render one download button per dataset."""
    today_str = date.today().strftime("%Y%m%d")
    st.subheader("Download Individual Datasets")

    labels = {
        "suppliers": "Suppliers",
        "assessments": "Assessments",
        "overall_scores": "ESG Scores",
        "evidence_files": "Evidence File Index",
    }

    cols = st.columns(2)
    for idx, (key, label) in enumerate(labels.items()):
        df = export_frames.get(key, pd.DataFrame())
        csv_bytes = export_to_csv(df)
        with cols[idx % 2]:
            st.download_button(
                label=f"Download {label} CSV",
                data=csv_bytes,
                file_name=f"esg_{key}_{today_str}.csv",
                mime="text/csv",
                disabled=df.empty,
                key=f"dl_{key}",
            )


def _render_summary_report(overall_scores: pd.DataFrame) -> None:
    """Render and offer download of the text summary report."""
    st.subheader("Summary Report")

    try:
        report_text = generate_report_summary(overall_scores)
    except ValueError as exc:
        st.error(f"Could not generate report: {exc}")
        return

    st.text(report_text)

    today_str = date.today().strftime("%Y%m%d")
    st.download_button(
        label="Download Report as TXT",
        data=report_text.encode("utf-8"),
        file_name=f"esg_summary_report_{today_str}.txt",
        mime="text/plain",
        key="dl_report_txt",
    )


def _render_statistics_panel(
    suppliers: list[dict],
    assessments: list[dict],
    overall_scores: pd.DataFrame,
) -> None:
    """Render summary statistics cards."""
    st.subheader("Summary Statistics")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Suppliers", len(suppliers))
    with col2:
        st.metric("Total Assessments", len(assessments))
    with col3:
        avg = overall_scores["overall_score"].mean() if not overall_scores.empty else 0.0
        st.metric("Avg ESG Score", f"{avg:.1f}")
    with col4:
        if not overall_scores.empty:
            top = overall_scores.iloc[0]["supplier_name"]
            top_score = overall_scores.iloc[0]["overall_score"]
            st.metric("Top Performer", top, delta=f"{top_score:.1f}")
        else:
            st.metric("Top Performer", "—")


def render() -> None:
    """Entry point called by app.py to render the Export page."""
    st.title("Export & Reports")
    st.markdown(
        "Download ESG data as CSV files or generate a portfolio summary report."
    )

    suppliers = get_suppliers()
    assessments = get_assessments()

    assessments_df = pd.DataFrame(assessments) if assessments else pd.DataFrame()

    if assessments_df.empty:
        overall_scores: pd.DataFrame = pd.DataFrame()
    else:
        category_scores = calculate_category_scores(assessments_df)
        overall_scores = calculate_overall_score(category_scores)

    _render_statistics_panel(suppliers, assessments, overall_scores)
    st.divider()

    export_frames = _build_full_export_df(suppliers, assessments, overall_scores)
    _render_download_buttons(export_frames)
    st.divider()

    _render_summary_report(overall_scores)
