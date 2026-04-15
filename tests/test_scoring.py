"""
Tests for src/scoring.py — score calculation and risk classification.

All tests pass newly constructed DataFrames to ensure immutability:
the module must never alter its inputs.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.scoring import (
    RISK_CRITICAL,
    RISK_EXCELLENT,
    RISK_GOOD,
    RISK_HIGH,
    RISK_MEDIUM,
    calculate_category_scores,
    calculate_overall_score,
    classify_risk,
)


# ---------------------------------------------------------------------------
# classify_risk
# ---------------------------------------------------------------------------


def test_classify_risk_critical() -> None:
    """Scores below 30 map to Critical."""
    assert classify_risk(0.0) == RISK_CRITICAL
    assert classify_risk(15.0) == RISK_CRITICAL
    assert classify_risk(29.9) == RISK_CRITICAL


def test_classify_risk_high() -> None:
    """Scores in [30, 50) map to High."""
    assert classify_risk(30.0) == RISK_HIGH
    assert classify_risk(40.0) == RISK_HIGH
    assert classify_risk(49.9) == RISK_HIGH


def test_classify_risk_medium() -> None:
    """Scores in [50, 70) map to Medium."""
    assert classify_risk(50.0) == RISK_MEDIUM
    assert classify_risk(60.0) == RISK_MEDIUM
    assert classify_risk(69.9) == RISK_MEDIUM


def test_classify_risk_good() -> None:
    """Scores in [70, 85) map to Good."""
    assert classify_risk(70.0) == RISK_GOOD
    assert classify_risk(77.5) == RISK_GOOD
    assert classify_risk(84.9) == RISK_GOOD


def test_classify_risk_excellent() -> None:
    """Scores of 85 and above map to Excellent."""
    assert classify_risk(85.0) == RISK_EXCELLENT
    assert classify_risk(95.0) == RISK_EXCELLENT
    assert classify_risk(100.0) == RISK_EXCELLENT


# ---------------------------------------------------------------------------
# calculate_category_scores
# ---------------------------------------------------------------------------


def test_calculate_category_scores_basic(sample_assessments_df: pd.DataFrame) -> None:
    """Returns one row per supplier-category combination."""
    result = calculate_category_scores(sample_assessments_df)

    assert isinstance(result, pd.DataFrame)
    # 2 suppliers × 3 categories = 6 rows
    assert len(result) == 6
    assert set(result.columns) >= {"supplier_name", "category", "avg_score", "risk_level"}


def test_calculate_category_scores_values(sample_assessments_df: pd.DataFrame) -> None:
    """avg_score is the mean of input scores for each supplier-category group."""
    result = calculate_category_scores(sample_assessments_df)

    green_env = result[
        (result["supplier_name"] == "Green Energy Corp")
        & (result["category"] == "Environmental")
    ]["avg_score"].iloc[0]

    assert green_env == pytest.approx(80.0)


def test_calculate_category_scores_assigns_risk_level(
    sample_assessments_df: pd.DataFrame,
) -> None:
    """Every row in the result must have a non-empty risk_level string."""
    result = calculate_category_scores(sample_assessments_df)

    assert result["risk_level"].notna().all()
    valid_levels = {RISK_CRITICAL, RISK_HIGH, RISK_MEDIUM, RISK_GOOD, RISK_EXCELLENT}
    assert set(result["risk_level"].unique()).issubset(valid_levels)


def test_calculate_category_scores_does_not_mutate_input(
    sample_assessments_df: pd.DataFrame,
) -> None:
    """The input DataFrame columns must not be changed after the call."""
    original_columns = list(sample_assessments_df.columns)
    calculate_category_scores(sample_assessments_df)

    assert list(sample_assessments_df.columns) == original_columns


def test_empty_assessments_handling() -> None:
    """An empty assessments DataFrame returns an empty category scores DataFrame."""
    empty_df = pd.DataFrame(columns=["supplier_name", "category", "score"])
    result = calculate_category_scores(empty_df)

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_calculate_category_scores_missing_column_raises() -> None:
    """Passing a DataFrame that lacks required columns raises ValueError."""
    bad_df = pd.DataFrame({"supplier_name": ["A"], "score": [50.0]})

    with pytest.raises(ValueError, match="missing columns"):
        calculate_category_scores(bad_df)


# ---------------------------------------------------------------------------
# calculate_overall_score
# ---------------------------------------------------------------------------


def test_calculate_overall_score_returns_dataframe(
    sample_category_scores_df: pd.DataFrame,
) -> None:
    """calculate_overall_score returns a DataFrame with the expected columns."""
    result = calculate_overall_score(sample_category_scores_df)

    assert isinstance(result, pd.DataFrame)
    expected_cols = {
        "supplier_name",
        "environmental_score",
        "social_score",
        "governance_score",
        "overall_score",
        "risk_level",
    }
    assert expected_cols.issubset(set(result.columns))


def test_calculate_overall_score_weighted_average_correct(
    sample_category_scores_df: pd.DataFrame,
) -> None:
    """Overall score is the weighted average: E×0.4 + S×0.35 + G×0.25."""
    result = calculate_overall_score(sample_category_scores_df)

    green_row = result[result["supplier_name"] == "Green Energy Corp"].iloc[0]
    expected = 80.0 * 0.40 + 75.0 * 0.35 + 90.0 * 0.25
    assert green_row["overall_score"] == pytest.approx(expected, abs=0.01)


def test_calculate_overall_score_risk_level_assigned(
    sample_category_scores_df: pd.DataFrame,
) -> None:
    """Every supplier in the overall scores result has a risk_level."""
    result = calculate_overall_score(sample_category_scores_df)

    assert result["risk_level"].notna().all()


def test_calculate_overall_score_empty_input() -> None:
    """An empty category_scores DataFrame returns an empty overall DataFrame."""
    empty_df = pd.DataFrame(
        columns=["supplier_name", "category", "avg_score", "risk_level"]
    )
    result = calculate_overall_score(empty_df)

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_calculate_overall_score_sorted_descending(
    sample_category_scores_df: pd.DataFrame,
) -> None:
    """Results are sorted by overall_score in descending order."""
    result = calculate_overall_score(sample_category_scores_df)
    scores = result["overall_score"].tolist()

    assert scores == sorted(scores, reverse=True)
