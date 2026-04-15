"""
Scoring module for ESG Data Collector.
Calculates category and overall ESG scores from assessment data.
All functions return new DataFrames and never mutate inputs.
"""

from __future__ import annotations

from typing import Final

import pandas as pd

from src.gri_framework import get_category_weights

RISK_CRITICAL: Final[str] = "Critical"
RISK_HIGH: Final[str] = "High"
RISK_MEDIUM: Final[str] = "Medium"
RISK_GOOD: Final[str] = "Good"
RISK_EXCELLENT: Final[str] = "Excellent"

RISK_COLOR_MAP: Final[dict[str, str]] = {
    RISK_CRITICAL: "#d32f2f",
    RISK_HIGH: "#f57c00",
    RISK_MEDIUM: "#fbc02d",
    RISK_GOOD: "#388e3c",
    RISK_EXCELLENT: "#1565c0",
}


def classify_risk(score: float) -> str:
    """Map a numeric score (0-100) to a risk level label."""
    if score < 30:
        return RISK_CRITICAL
    if score < 50:
        return RISK_HIGH
    if score < 70:
        return RISK_MEDIUM
    if score < 85:
        return RISK_GOOD
    return RISK_EXCELLENT


def calculate_category_scores(assessments: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the mean score per supplier per ESG category.

    Parameters
    ----------
    assessments:
        DataFrame with at least columns: supplier_name, category, score.

    Returns
    -------
    New DataFrame with columns: supplier_name, category, avg_score, risk_level.
    """
    if assessments.empty:
        return pd.DataFrame(
            columns=["supplier_name", "category", "avg_score", "risk_level"]
        )

    required_cols = {"supplier_name", "category", "score"}
    missing = required_cols - set(assessments.columns)
    if missing:
        raise ValueError(f"assessments DataFrame is missing columns: {missing}")

    grouped = (
        assessments.groupby(["supplier_name", "category"], as_index=False)["score"]
        .mean()
        .rename(columns={"score": "avg_score"})
    )

    risk_levels = grouped["avg_score"].apply(classify_risk)
    return grouped.assign(risk_level=risk_levels)


def calculate_overall_score(category_scores: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the weighted overall ESG score per supplier.

    Parameters
    ----------
    category_scores:
        DataFrame returned by calculate_category_scores.

    Returns
    -------
    New DataFrame with columns:
        supplier_name, environmental_score, social_score,
        governance_score, overall_score, risk_level.
    """
    if category_scores.empty:
        return pd.DataFrame(
            columns=[
                "supplier_name",
                "environmental_score",
                "social_score",
                "governance_score",
                "overall_score",
                "risk_level",
            ]
        )

    weights = get_category_weights()
    pivoted = category_scores.pivot_table(
        index="supplier_name", columns="category", values="avg_score", aggfunc="mean"
    ).reset_index()

    # Ensure all category columns exist (fill 0 if a supplier has no data for a category)
    for col in ["Environmental", "Social", "Governance"]:
        if col not in pivoted.columns:
            pivoted = pivoted.assign(**{col: 0.0})

    overall = (
        pivoted["Environmental"].fillna(0) * weights["Environmental"]
        + pivoted["Social"].fillna(0) * weights["Social"]
        + pivoted["Governance"].fillna(0) * weights["Governance"]
    )

    result = pd.DataFrame(
        {
            "supplier_name": pivoted["supplier_name"],
            "environmental_score": pivoted["Environmental"].fillna(0).round(2),
            "social_score": pivoted["Social"].fillna(0).round(2),
            "governance_score": pivoted["Governance"].fillna(0).round(2),
            "overall_score": overall.round(2),
        }
    )

    risk_levels = result["overall_score"].apply(classify_risk)
    return result.assign(risk_level=risk_levels).sort_values(
        "overall_score", ascending=False
    ).reset_index(drop=True)


def get_risk_distribution(overall_scores: pd.DataFrame) -> dict[str, int]:
    """Return a count of suppliers per risk level."""
    if overall_scores.empty or "risk_level" not in overall_scores.columns:
        return {level: 0 for level in [RISK_CRITICAL, RISK_HIGH, RISK_MEDIUM, RISK_GOOD, RISK_EXCELLENT]}

    counts = overall_scores["risk_level"].value_counts().to_dict()
    return {
        level: counts.get(level, 0)
        for level in [RISK_CRITICAL, RISK_HIGH, RISK_MEDIUM, RISK_GOOD, RISK_EXCELLENT]
    }
