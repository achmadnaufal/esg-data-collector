"""
Tests for src/database.py — SQLite CRUD operations.

All tests use isolated temporary databases via the db_path and raw_conn
fixtures so they never share mutable state.
"""

from __future__ import annotations

import importlib
import os
import sqlite3
from pathlib import Path

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reload_db(db_path: str):
    """Reload src.database after ESG_DB_PATH has been set, return the module."""
    os.environ["ESG_DB_PATH"] = db_path
    import src.database as m  # noqa: PLC0415

    importlib.reload(m)
    return m


# ---------------------------------------------------------------------------
# Schema / initialisation
# ---------------------------------------------------------------------------


def test_create_tables(db_path: str) -> None:
    """initialize_database creates all required tables."""
    db = _reload_db(db_path)
    db.initialize_database()

    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    assert "suppliers" in tables
    assert "gri_indicators" in tables
    assert "esg_assessments" in tables
    assert "evidence_files" in tables


def test_create_tables_idempotent(db_path: str) -> None:
    """Calling initialize_database twice does not raise or duplicate tables."""
    db = _reload_db(db_path)
    db.initialize_database()
    db.initialize_database()  # second call must be safe

    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
    )
    count = cursor.fetchone()[0]
    conn.close()

    assert count >= 4


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------


def test_create_supplier(db_path: str) -> None:
    """create_supplier inserts a row and returns a positive integer ID."""
    db = _reload_db(db_path)
    supplier_id = db.create_supplier("Acme Corp", "London, UK", "Manufacturing")

    assert isinstance(supplier_id, int)
    assert supplier_id > 0


def test_get_suppliers_empty(db_path: str) -> None:
    """get_suppliers returns an empty list when no rows exist."""
    db = _reload_db(db_path)
    result = db.get_suppliers()

    assert isinstance(result, list)
    assert result == []


def test_get_suppliers_with_data(db_path: str) -> None:
    """get_suppliers returns all inserted supplier rows."""
    db = _reload_db(db_path)
    db.create_supplier("Alpha Inc", "Paris, France", "Finance")
    db.create_supplier("Beta Ltd", "Tokyo, Japan", "Retail")

    result = db.get_suppliers()

    assert len(result) == 2
    names = {row["name"] for row in result}
    assert names == {"Alpha Inc", "Beta Ltd"}


def test_create_supplier_returns_unique_ids(db_path: str) -> None:
    """Each call to create_supplier returns a distinct ID."""
    db = _reload_db(db_path)
    id_1 = db.create_supplier("Supplier A", "City A", "Sector A")
    id_2 = db.create_supplier("Supplier B", "City B", "Sector B")

    assert id_1 != id_2


# ---------------------------------------------------------------------------
# Assessments
# ---------------------------------------------------------------------------


def _seed_indicator(db_path: str, code: str = "GRI 302-1") -> int:
    """Insert one GRI indicator and return its ID."""
    conn = sqlite3.connect(db_path)
    with conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO gri_indicators (code, name, category, description) "
            "VALUES (?, ?, ?, ?)",
            (code, "Test Indicator", "Environmental", "Desc"),
        )
        if cursor.lastrowid:
            return cursor.lastrowid
        row = conn.execute(
            "SELECT id FROM gri_indicators WHERE code = ?", (code,)
        ).fetchone()
    conn.close()
    return row[0]


def test_create_assessment(db_path: str) -> None:
    """create_assessment inserts a row and returns a positive integer ID."""
    db = _reload_db(db_path)
    supplier_id = db.create_supplier("Eco Corp", "Berlin", "Energy")
    indicator_id = _seed_indicator(db_path)

    assessment_id = db.create_assessment(
        supplier_id=supplier_id,
        indicator_id=indicator_id,
        score=72.5,
        evidence_notes="Annual report reviewed",
        assessed_date="2024-03-01",
        assessor="Alice",
    )

    assert isinstance(assessment_id, int)
    assert assessment_id > 0


def test_get_assessments(db_path: str) -> None:
    """get_assessments returns all inserted assessment rows."""
    db = _reload_db(db_path)
    supplier_id = db.create_supplier("Eco Corp", "Berlin", "Energy")
    indicator_id = _seed_indicator(db_path)

    db.create_assessment(supplier_id, indicator_id, 60.0, "Note", "2024-04-01", "Bob")
    db.create_assessment(supplier_id, indicator_id, 80.0, "Note2", "2024-04-02", "Bob")

    rows = db.get_assessments()

    assert len(rows) == 2


def test_get_assessments_by_supplier(db_path: str) -> None:
    """get_assessments_by_supplier filters correctly by supplier_id."""
    db = _reload_db(db_path)
    sid_a = db.create_supplier("Supplier A", "City A", "Sector A")
    sid_b = db.create_supplier("Supplier B", "City B", "Sector B")
    ind_id = _seed_indicator(db_path)

    db.create_assessment(sid_a, ind_id, 55.0, "", "2024-01-01", "Alice")
    db.create_assessment(sid_b, ind_id, 75.0, "", "2024-01-02", "Alice")

    rows_a = db.get_assessments_by_supplier(sid_a)
    rows_b = db.get_assessments_by_supplier(sid_b)

    assert len(rows_a) == 1
    assert len(rows_b) == 1
    assert rows_a[0]["score"] == 55.0
    assert rows_b[0]["score"] == 75.0


# ---------------------------------------------------------------------------
# GRI indicators
# ---------------------------------------------------------------------------


def test_duplicate_gri_indicator_code(db_path: str) -> None:
    """Inserting a GRI indicator with a duplicate code is silently ignored."""
    db = _reload_db(db_path)
    db.upsert_gri_indicator("GRI 302-1", "Energy Consumption", "Environmental", "Desc")
    db.upsert_gri_indicator("GRI 302-1", "Duplicate Name", "Environmental", "Different desc")

    indicators = db.get_gri_indicators()
    matching = [i for i in indicators if i["code"] == "GRI 302-1"]

    assert len(matching) == 1
    assert matching[0]["name"] == "Energy Consumption"


def test_get_gri_indicators_by_category(db_path: str) -> None:
    """get_gri_indicators_by_category returns only the requested category."""
    db = _reload_db(db_path)
    db.upsert_gri_indicator("GRI 302-1", "Energy", "Environmental", "")
    db.upsert_gri_indicator("GRI 401-1", "Hires", "Social", "")
    db.upsert_gri_indicator("GRI 205-1", "Corruption", "Governance", "")

    env_rows = db.get_gri_indicators_by_category("Environmental")

    assert len(env_rows) == 1
    assert env_rows[0]["category"] == "Environmental"
