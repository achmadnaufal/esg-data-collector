"""
Tests for src/gri_framework.py — GRI indicator definitions, seeding, and lookup.

Tests use the seeded_db_path fixture so the database is pre-populated with
the canonical indicator set before each test function runs.
"""

from __future__ import annotations

import importlib
import os

import pytest

from src.gri_framework import (
    ALL_CATEGORIES,
    CATEGORY_ENVIRONMENTAL,
    CATEGORY_GOVERNANCE,
    CATEGORY_SOCIAL,
    GRI_INDICATORS,
    GRIIndicator,
    get_category_weights,
    get_indicators_by_category,
    seed_gri_indicators,
)


# ---------------------------------------------------------------------------
# Static catalogue checks (no database required)
# ---------------------------------------------------------------------------


def test_gri_indicators_defined() -> None:
    """The GRI_INDICATORS catalogue must contain at least 15 entries."""
    assert len(GRI_INDICATORS) >= 15


def test_gri_categories_complete() -> None:
    """All three ESG categories must be represented in GRI_INDICATORS."""
    found_categories = {ind.category for ind in GRI_INDICATORS}

    assert CATEGORY_ENVIRONMENTAL in found_categories
    assert CATEGORY_SOCIAL in found_categories
    assert CATEGORY_GOVERNANCE in found_categories


def test_indicator_codes_unique() -> None:
    """Every GRI indicator code in the catalogue must be unique."""
    codes = [ind.code for ind in GRI_INDICATORS]
    assert len(codes) == len(set(codes))


def test_all_categories_constant() -> None:
    """ALL_CATEGORIES must contain exactly the three ESG category strings."""
    assert set(ALL_CATEGORIES) == {
        CATEGORY_ENVIRONMENTAL,
        CATEGORY_SOCIAL,
        CATEGORY_GOVERNANCE,
    }


def test_gri_indicator_is_frozen_dataclass() -> None:
    """GRIIndicator must be immutable — assignment to a field raises TypeError."""
    indicator = GRI_INDICATORS[0]

    with pytest.raises((AttributeError, TypeError)):
        indicator.code = "MODIFIED"  # type: ignore[misc]


def test_category_weights_sum_to_one() -> None:
    """ESG category weights must sum to 1.0 (within floating-point tolerance)."""
    weights = get_category_weights()
    total = sum(weights.values())

    assert abs(total - 1.0) < 1e-9


def test_category_weights_keys_match_categories() -> None:
    """Category weight keys must match ALL_CATEGORIES."""
    weights = get_category_weights()
    assert set(weights.keys()) == set(ALL_CATEGORIES)


# ---------------------------------------------------------------------------
# Database-backed tests
# ---------------------------------------------------------------------------


def test_seed_gri_indicators(seeded_db_path: str) -> None:
    """seed_gri_indicators populates the database with the full catalogue."""
    import src.database as db  # noqa: PLC0415

    importlib.reload(db)
    indicators = db.get_gri_indicators()
    assert len(indicators) == len(GRI_INDICATORS)


def test_seed_gri_indicators_idempotent(seeded_db_path: str) -> None:
    """Calling seed_gri_indicators twice does not create duplicate rows."""
    import src.database as db  # noqa: PLC0415

    importlib.reload(db)
    db.initialize_database()

    # Seed again — should be a no-op due to INSERT OR IGNORE.
    seed_gri_indicators()

    indicators = db.get_gri_indicators()
    codes = [i["code"] for i in indicators]
    assert len(codes) == len(set(codes))


def test_get_indicators_by_category_environmental(seeded_db_path: str) -> None:
    """get_indicators_by_category returns only Environmental indicators."""
    rows = get_indicators_by_category(CATEGORY_ENVIRONMENTAL)

    assert len(rows) > 0
    assert all(r["category"] == CATEGORY_ENVIRONMENTAL for r in rows)


def test_get_indicators_by_category_social(seeded_db_path: str) -> None:
    """get_indicators_by_category returns only Social indicators."""
    rows = get_indicators_by_category(CATEGORY_SOCIAL)

    assert len(rows) > 0
    assert all(r["category"] == CATEGORY_SOCIAL for r in rows)


def test_get_indicators_by_category_governance(seeded_db_path: str) -> None:
    """get_indicators_by_category returns only Governance indicators."""
    rows = get_indicators_by_category(CATEGORY_GOVERNANCE)

    assert len(rows) > 0
    assert all(r["category"] == CATEGORY_GOVERNANCE for r in rows)


def test_get_indicators_by_category_invalid_raises(seeded_db_path: str) -> None:
    """Passing an unknown category string must raise ValueError."""
    with pytest.raises(ValueError, match="Unknown category"):
        get_indicators_by_category("Finance")
