"""
GRI Framework definitions for ESG Data Collector.
Contains frozen dataclass definitions and functions to seed / query GRI indicators.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from src.database import get_gri_indicators_by_category, upsert_gri_indicator

CATEGORY_ENVIRONMENTAL: Final[str] = "Environmental"
CATEGORY_SOCIAL: Final[str] = "Social"
CATEGORY_GOVERNANCE: Final[str] = "Governance"

ALL_CATEGORIES: Final[tuple[str, ...]] = (
    CATEGORY_ENVIRONMENTAL,
    CATEGORY_SOCIAL,
    CATEGORY_GOVERNANCE,
)


@dataclass(frozen=True)
class GRIIndicator:
    """Immutable representation of a single GRI indicator."""

    code: str
    name: str
    category: str
    description: str


# ---------------------------------------------------------------------------
# Master indicator catalogue (at least 15 indicators across all categories)
# ---------------------------------------------------------------------------

GRI_INDICATORS: Final[tuple[GRIIndicator, ...]] = (
    # --- Environmental (GRI 300 series) ---
    GRIIndicator(
        code="GRI 301-1",
        name="Materials Used by Weight or Volume",
        category=CATEGORY_ENVIRONMENTAL,
        description="Total materials used to produce and package an organization's primary products and services.",
    ),
    GRIIndicator(
        code="GRI 302-1",
        name="Energy Consumption Within the Organization",
        category=CATEGORY_ENVIRONMENTAL,
        description="Total fuel consumption, electricity, heating, cooling, and steam consumption.",
    ),
    GRIIndicator(
        code="GRI 303-1",
        name="Water Withdrawal by Source",
        category=CATEGORY_ENVIRONMENTAL,
        description="Total water withdrawal from all sources in megaliters.",
    ),
    GRIIndicator(
        code="GRI 305-1",
        name="Direct (Scope 1) GHG Emissions",
        category=CATEGORY_ENVIRONMENTAL,
        description="Gross direct greenhouse gas emissions in metric tons of CO2 equivalent.",
    ),
    GRIIndicator(
        code="GRI 306-3",
        name="Significant Waste-Related Impacts",
        category=CATEGORY_ENVIRONMENTAL,
        description="Significant actual and potential waste-related impacts in the value chain.",
    ),
    GRIIndicator(
        code="GRI 307-1",
        name="Non-Compliance with Environmental Laws",
        category=CATEGORY_ENVIRONMENTAL,
        description="Significant fines and non-monetary sanctions for non-compliance with environmental laws.",
    ),
    GRIIndicator(
        code="GRI 308-1",
        name="New Suppliers Screened Using Environmental Criteria",
        category=CATEGORY_ENVIRONMENTAL,
        description="Percentage of new suppliers screened using environmental criteria.",
    ),
    # --- Social (GRI 400 series) ---
    GRIIndicator(
        code="GRI 401-1",
        name="New Employee Hires and Employee Turnover",
        category=CATEGORY_SOCIAL,
        description="Total number and rate of new employee hires and employee turnover by age group, gender, and region.",
    ),
    GRIIndicator(
        code="GRI 403-1",
        name="Occupational Health and Safety Management System",
        category=CATEGORY_SOCIAL,
        description="Scope of worker coverage in the occupational health and safety management system.",
    ),
    GRIIndicator(
        code="GRI 405-1",
        name="Diversity of Governance Bodies and Employees",
        category=CATEGORY_SOCIAL,
        description="Percentage of individuals within governance bodies and employees by gender and age group.",
    ),
    GRIIndicator(
        code="GRI 408-1",
        name="Operations at Significant Risk of Child Labor",
        category=CATEGORY_SOCIAL,
        description="Operations and suppliers at significant risk for incidents of child labor.",
    ),
    GRIIndicator(
        code="GRI 413-1",
        name="Local Community Engagement",
        category=CATEGORY_SOCIAL,
        description="Percentage of operations with local community engagement, impact assessments, and development programs.",
    ),
    GRIIndicator(
        code="GRI 414-1",
        name="New Suppliers Screened Using Social Criteria",
        category=CATEGORY_SOCIAL,
        description="Percentage of new suppliers screened using social criteria.",
    ),
    # --- Governance (GRI 200 series) ---
    GRIIndicator(
        code="GRI 201-1",
        name="Direct Economic Value Generated and Distributed",
        category=CATEGORY_GOVERNANCE,
        description="Direct economic value generated and distributed on an accruals basis.",
    ),
    GRIIndicator(
        code="GRI 205-1",
        name="Operations Assessed for Corruption Risks",
        category=CATEGORY_GOVERNANCE,
        description="Total number and percentage of operations assessed for corruption-related risks.",
    ),
    GRIIndicator(
        code="GRI 206-1",
        name="Legal Actions for Anti-Competitive Behavior",
        category=CATEGORY_GOVERNANCE,
        description="Number of legal actions pending or completed regarding anti-competitive behavior.",
    ),
    GRIIndicator(
        code="GRI 207-1",
        name="Approach to Tax",
        category=CATEGORY_GOVERNANCE,
        description="Organization's approach to tax governance, control, and risk management.",
    ),
)


def seed_gri_indicators() -> None:
    """Persist all GRI indicators into the database (idempotent)."""
    for indicator in GRI_INDICATORS:
        upsert_gri_indicator(
            code=indicator.code,
            name=indicator.name,
            category=indicator.category,
            description=indicator.description,
        )


def get_indicators_by_category(category: str) -> list[dict]:
    """Return database rows for indicators in the requested category."""
    if category not in ALL_CATEGORIES:
        raise ValueError(f"Unknown category '{category}'. Must be one of {ALL_CATEGORIES}.")
    return get_gri_indicators_by_category(category)


def get_category_weights() -> dict[str, float]:
    """Return the ESG category weighting scheme."""
    return {
        CATEGORY_ENVIRONMENTAL: 0.40,
        CATEGORY_SOCIAL: 0.35,
        CATEGORY_GOVERNANCE: 0.25,
    }
