"""
Charts module for ESG Data Collector.
All visualisations use Plotly for interactivity.
Each function returns a new go.Figure and never mutates its inputs.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.scoring import RISK_COLOR_MAP


def create_esg_radar_chart(scores: dict[str, float]) -> go.Figure:
    """
    Build a radar / spider chart for E, S, G category scores.

    Parameters
    ----------
    scores:
        Dict with keys 'Environmental', 'Social', 'Governance' and float values (0-100).
    """
    categories = ["Environmental", "Social", "Governance"]
    values = [scores.get(cat, 0.0) for cat in categories]
    # Close the polygon
    closed_categories = categories + [categories[0]]
    closed_values = values + [values[0]]

    fig = go.Figure(
        data=go.Scatterpolar(
            r=closed_values,
            theta=closed_categories,
            fill="toself",
            fillcolor="rgba(33, 150, 243, 0.25)",
            line={"color": "#1565c0", "width": 2},
            marker={"size": 6, "color": "#1565c0"},
            name="ESG Score",
        )
    )
    fig.update_layout(
        polar={
            "radialaxis": {
                "visible": True,
                "range": [0, 100],
                "tickfont": {"size": 11},
            }
        },
        title={"text": "ESG Category Scores", "x": 0.5, "font": {"size": 16}},
        showlegend=False,
        height=380,
        margin={"l": 60, "r": 60, "t": 60, "b": 40},
    )
    return fig


def create_score_distribution(assessments: pd.DataFrame) -> go.Figure:
    """
    Histogram showing the distribution of individual assessment scores.

    Parameters
    ----------
    assessments:
        DataFrame with at least a 'score' column.
    """
    if assessments.empty or "score" not in assessments.columns:
        fig = go.Figure()
        fig.update_layout(title="Score Distribution (No Data)", height=320)
        return fig

    fig = px.histogram(
        assessments,
        x="score",
        nbins=20,
        color_discrete_sequence=["#1976d2"],
        labels={"score": "Assessment Score", "count": "Number of Assessments"},
        title="Assessment Score Distribution",
    )
    fig.update_layout(
        height=320,
        bargap=0.05,
        xaxis={"range": [0, 100]},
        title={"x": 0.5, "font": {"size": 16}},
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
    )
    return fig


def create_category_comparison(data: pd.DataFrame) -> go.Figure:
    """
    Grouped bar chart comparing E/S/G scores across suppliers.

    Parameters
    ----------
    data:
        DataFrame with columns: supplier_name, environmental_score,
        social_score, governance_score.
    """
    if data.empty:
        fig = go.Figure()
        fig.update_layout(title="Category Comparison (No Data)", height=380)
        return fig

    fig = go.Figure()
    category_map = {
        "environmental_score": ("Environmental", "#4caf50"),
        "social_score": ("Social", "#2196f3"),
        "governance_score": ("Governance", "#9c27b0"),
    }

    for col, (label, color) in category_map.items():
        if col in data.columns:
            fig.add_trace(
                go.Bar(
                    name=label,
                    x=data["supplier_name"],
                    y=data[col],
                    marker_color=color,
                    text=data[col].round(1),
                    textposition="outside",
                )
            )

    fig.update_layout(
        barmode="group",
        title={"text": "E/S/G Score Comparison by Supplier", "x": 0.5, "font": {"size": 16}},
        xaxis={"title": "Supplier", "tickangle": -30},
        yaxis={"title": "Score (0-100)", "range": [0, 110]},
        height=420,
        legend={"orientation": "h", "y": -0.25},
        margin={"l": 40, "r": 20, "t": 60, "b": 100},
    )
    return fig


def create_trend_chart(data: pd.DataFrame) -> go.Figure:
    """
    Line chart showing score trends over time per supplier.

    Parameters
    ----------
    data:
        DataFrame with columns: assessed_date, supplier_name, score.
    """
    if data.empty or "assessed_date" not in data.columns:
        fig = go.Figure()
        fig.update_layout(title="Score Trend (No Data)", height=340)
        return fig

    trend_data = data.copy()
    trend_data["assessed_date"] = pd.to_datetime(
        trend_data["assessed_date"], errors="coerce"
    )
    trend_data = trend_data.dropna(subset=["assessed_date", "score"])

    if trend_data.empty:
        fig = go.Figure()
        fig.update_layout(title="Score Trend (Insufficient Data)", height=340)
        return fig

    daily_avg = (
        trend_data.groupby(["assessed_date", "supplier_name"], as_index=False)["score"]
        .mean()
        .sort_values("assessed_date")
    )

    fig = px.line(
        daily_avg,
        x="assessed_date",
        y="score",
        color="supplier_name",
        markers=True,
        labels={"assessed_date": "Date", "score": "Average Score", "supplier_name": "Supplier"},
        title="ESG Score Trend Over Time",
    )
    fig.update_layout(
        height=340,
        title={"x": 0.5, "font": {"size": 16}},
        yaxis={"range": [0, 100]},
        legend={"orientation": "h", "y": -0.3},
        margin={"l": 40, "r": 20, "t": 60, "b": 80},
    )
    return fig


def create_risk_heatmap(data: pd.DataFrame) -> go.Figure:
    """
    Heatmap of scores by supplier and GRI category.

    Parameters
    ----------
    data:
        DataFrame with columns: supplier_name, category, avg_score.
    """
    if data.empty:
        fig = go.Figure()
        fig.update_layout(title="Risk Heatmap (No Data)", height=360)
        return fig

    pivot = data.pivot_table(
        index="supplier_name", columns="category", values="avg_score", aggfunc="mean"
    ).fillna(0)

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values.tolist(),
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=[
                [0.0, "#d32f2f"],
                [0.30, "#f57c00"],
                [0.50, "#fbc02d"],
                [0.70, "#388e3c"],
                [1.0, "#1565c0"],
            ],
            zmin=0,
            zmax=100,
            text=[[f"{v:.1f}" for v in row] for row in pivot.values.tolist()],
            texttemplate="%{text}",
            hovertemplate="Supplier: %{y}<br>Category: %{x}<br>Score: %{z:.1f}<extra></extra>",
            colorbar={"title": "Score"},
        )
    )
    fig.update_layout(
        title={"text": "ESG Score Heatmap (Supplier × Category)", "x": 0.5, "font": {"size": 16}},
        xaxis={"title": "Category"},
        yaxis={"title": "Supplier"},
        height=360,
        margin={"l": 120, "r": 20, "t": 60, "b": 60},
    )
    return fig
