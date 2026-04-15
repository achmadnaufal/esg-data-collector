"""
Export module for ESG Data Collector.
Provides CSV export and plain-text report summary generation.
All functions return new objects and never mutate their inputs.
"""

from __future__ import annotations

import io

import pandas as pd

from src.scoring import RISK_CRITICAL, RISK_HIGH, RISK_MEDIUM, RISK_GOOD, RISK_EXCELLENT


def export_to_csv(data: pd.DataFrame) -> bytes:
    """Serialise a DataFrame to UTF-8 encoded CSV bytes.

    Parameters
    ----------
    data:
        Any pandas DataFrame to serialise. An empty DataFrame produces a CSV
        with only the header row (or a completely empty byte string if the
        DataFrame has no columns).

    Returns
    -------
    UTF-8 encoded bytes suitable for ``st.download_button`` or file I/O.
    """
    buffer = io.StringIO()
    data.to_csv(buffer, index=False, encoding="utf-8")
    return buffer.getvalue().encode("utf-8")


def generate_report_summary(scores: pd.DataFrame) -> str:
    """Generate a human-readable plain-text report summary.

    Parameters
    ----------
    scores:
        DataFrame returned by ``calculate_overall_score``.
        Expected columns: supplier_name, overall_score, risk_level.

    Returns
    -------
    Multi-line string report. Returns a short "no data" message when the
    DataFrame is empty.
    """
    if scores.empty:
        return "No assessment data available for report generation."

    required_cols = {"supplier_name", "overall_score", "risk_level"}
    missing = required_cols - set(scores.columns)
    if missing:
        raise ValueError(f"scores DataFrame is missing columns: {missing}")

    total = len(scores)
    avg_score = scores["overall_score"].mean()

    risk_counts: dict[str, int] = {
        level: int((scores["risk_level"] == level).sum())
        for level in [RISK_CRITICAL, RISK_HIGH, RISK_MEDIUM, RISK_GOOD, RISK_EXCELLENT]
    }

    top_row = scores.loc[scores["overall_score"].idxmax()]

    lines = [
        "=" * 60,
        "ESG SUPPLIER ASSESSMENT — REPORT SUMMARY",
        "=" * 60,
        f"Total suppliers assessed : {total}",
        f"Portfolio average score  : {avg_score:.1f} / 100",
        "",
        "Risk distribution:",
        f"  Critical  (< 30) : {risk_counts[RISK_CRITICAL]} supplier(s)",
        f"  High      (< 50) : {risk_counts[RISK_HIGH]} supplier(s)",
        f"  Medium    (< 70) : {risk_counts[RISK_MEDIUM]} supplier(s)",
        f"  Good      (< 85) : {risk_counts[RISK_GOOD]} supplier(s)",
        f"  Excellent (≥ 85) : {risk_counts[RISK_EXCELLENT]} supplier(s)",
        "",
        "Top performer:",
        f"  {top_row['supplier_name']} — {top_row['overall_score']:.1f} ({top_row['risk_level']})",
        "=" * 60,
    ]
    return "\n".join(lines)
