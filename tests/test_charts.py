"""
Tests for src/charts.py — Plotly figure generation.

Each test asserts that the function returns a go.Figure instance and that
the figure contains meaningful layout/trace data.  No database or file I/O
is required; all inputs are constructed inline or via fixtures.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.charts import (
    create_category_comparison,
    create_esg_radar_chart,
    create_risk_heatmap,
    create_score_distribution,
    create_trend_chart,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_category_df() -> pd.DataFrame:
    """Return a minimal category scores DataFrame for chart tests."""
    return pd.DataFrame(
        {
            "supplier_name": ["Acme Corp", "Acme Corp", "BetaCo", "BetaCo"],
            "category": ["Environmental", "Social", "Environmental", "Social"],
            "avg_score": [75.0, 60.0, 50.0, 45.0],
        }
    )


def _make_overall_scores_df() -> pd.DataFrame:
    """Return a minimal overall scores DataFrame for chart tests."""
    return pd.DataFrame(
        {
            "supplier_name": ["Acme Corp", "BetaCo"],
            "environmental_score": [75.0, 50.0],
            "social_score": [60.0, 45.0],
            "governance_score": [80.0, 30.0],
            "overall_score": [71.5, 42.5],
            "risk_level": ["Good", "High"],
        }
    )


# ---------------------------------------------------------------------------
# create_esg_radar_chart
# ---------------------------------------------------------------------------


def test_create_radar_chart_returns_figure() -> None:
    """create_esg_radar_chart must return a go.Figure."""
    scores = {"Environmental": 75.0, "Social": 60.0, "Governance": 80.0}
    fig = create_esg_radar_chart(scores)

    assert isinstance(fig, go.Figure)


def test_create_radar_chart_has_scatterpolar_trace() -> None:
    """The radar chart must contain at least one Scatterpolar trace."""
    scores = {"Environmental": 75.0, "Social": 60.0, "Governance": 80.0}
    fig = create_esg_radar_chart(scores)

    trace_types = [type(trace).__name__ for trace in fig.data]
    assert "Scatterpolar" in trace_types


def test_create_radar_chart_with_zero_scores() -> None:
    """create_esg_radar_chart must not raise when all scores are zero."""
    scores = {"Environmental": 0.0, "Social": 0.0, "Governance": 0.0}
    fig = create_esg_radar_chart(scores)

    assert isinstance(fig, go.Figure)


def test_create_radar_chart_values_reflected_in_trace() -> None:
    """The r-values of the polar trace must include the provided scores."""
    scores = {"Environmental": 55.0, "Social": 70.0, "Governance": 40.0}
    fig = create_esg_radar_chart(scores)

    polar_trace = next(t for t in fig.data if isinstance(t, go.Scatterpolar))
    r_values = list(polar_trace.r)

    assert 55.0 in r_values
    assert 70.0 in r_values
    assert 40.0 in r_values


# ---------------------------------------------------------------------------
# create_score_distribution
# ---------------------------------------------------------------------------


def test_create_score_distribution_returns_figure(
    sample_assessments_df: pd.DataFrame,
) -> None:
    """create_score_distribution must return a go.Figure."""
    fig = create_score_distribution(sample_assessments_df)

    assert isinstance(fig, go.Figure)


def test_create_score_distribution_empty_dataframe() -> None:
    """An empty DataFrame must return a Figure (not raise)."""
    empty_df = pd.DataFrame(columns=["score"])
    fig = create_score_distribution(empty_df)

    assert isinstance(fig, go.Figure)


def test_create_score_distribution_no_score_column() -> None:
    """A DataFrame without a score column must return a Figure (not raise)."""
    df = pd.DataFrame({"supplier_name": ["A", "B"]})
    fig = create_score_distribution(df)

    assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# create_category_comparison
# ---------------------------------------------------------------------------


def test_create_category_comparison_returns_figure() -> None:
    """create_category_comparison must return a go.Figure."""
    df = _make_overall_scores_df()
    fig = create_category_comparison(df)

    assert isinstance(fig, go.Figure)


def test_create_category_comparison_has_bar_traces() -> None:
    """The category comparison chart must include at least one Bar trace."""
    df = _make_overall_scores_df()
    fig = create_category_comparison(df)

    trace_types = [type(trace).__name__ for trace in fig.data]
    assert "Bar" in trace_types


def test_create_category_comparison_empty_dataframe() -> None:
    """An empty DataFrame must return a Figure (not raise)."""
    empty_df = pd.DataFrame(
        columns=["supplier_name", "environmental_score", "social_score", "governance_score"]
    )
    fig = create_category_comparison(empty_df)

    assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# create_trend_chart
# ---------------------------------------------------------------------------


def test_create_trend_chart_returns_figure(
    sample_assessments_df: pd.DataFrame,
) -> None:
    """create_trend_chart must return a go.Figure."""
    fig = create_trend_chart(sample_assessments_df)

    assert isinstance(fig, go.Figure)


def test_create_trend_chart_empty_dataframe() -> None:
    """An empty DataFrame must return a Figure (not raise)."""
    empty_df = pd.DataFrame(columns=["assessed_date", "supplier_name", "score"])
    fig = create_trend_chart(empty_df)

    assert isinstance(fig, go.Figure)


def test_create_trend_chart_invalid_dates_handled() -> None:
    """Rows with invalid date strings must be dropped gracefully."""
    df = pd.DataFrame(
        {
            "assessed_date": ["not-a-date", "also-bad"],
            "supplier_name": ["A", "B"],
            "score": [50.0, 60.0],
        }
    )
    fig = create_trend_chart(df)

    assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# create_risk_heatmap
# ---------------------------------------------------------------------------


def test_create_risk_heatmap_returns_figure() -> None:
    """create_risk_heatmap must return a go.Figure."""
    df = _make_category_df()
    fig = create_risk_heatmap(df)

    assert isinstance(fig, go.Figure)


def test_create_risk_heatmap_has_heatmap_trace() -> None:
    """The risk heatmap must contain a Heatmap trace."""
    df = _make_category_df()
    fig = create_risk_heatmap(df)

    trace_types = [type(trace).__name__ for trace in fig.data]
    assert "Heatmap" in trace_types


def test_create_risk_heatmap_empty_dataframe() -> None:
    """An empty DataFrame must return a Figure (not raise)."""
    empty_df = pd.DataFrame(
        columns=["supplier_name", "category", "avg_score"]
    )
    fig = create_risk_heatmap(empty_df)

    assert isinstance(fig, go.Figure)
