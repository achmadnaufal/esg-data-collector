"""
Shared pytest fixtures for the ESG Data Collector test suite.

Design decisions:
- Each database fixture creates an isolated temporary file so tests are
  fully independent (no shared mutable state).
- The ESG_DB_PATH environment variable is patched so src.database picks up
  the temporary path without any code changes.
- All sample DataFrames are built fresh per test via factory functions
  returned by fixtures, or as immutable constants — never mutated in place.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Generator

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Database isolation helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_path(tmp_path: Path) -> Generator[str, None, None]:
    """Yield a path to an isolated, initialised SQLite database.

    Sets the ESG_DB_PATH environment variable so that all src.database
    functions transparently use this temporary file instead of the
    production database.  The variable is restored (or removed) after
    the test completes.
    """
    path = str(tmp_path / "test_esg.db")

    # Re-import here so the module re-reads the patched env var.
    original = os.environ.get("ESG_DB_PATH")
    os.environ["ESG_DB_PATH"] = path

    # Import after env is set so the module-level DB_PATH is correct.
    import importlib
    import src.database as db_module  # noqa: PLC0415

    importlib.reload(db_module)
    db_module.initialize_database()

    yield path

    # Tear down: restore environment.
    if original is None:
        os.environ.pop("ESG_DB_PATH", None)
    else:
        os.environ["ESG_DB_PATH"] = original

    # Reload module back to default state.
    importlib.reload(db_module)


@pytest.fixture()
def seeded_db_path(db_path: str) -> str:
    """Return a db_path that already has GRI indicators seeded."""
    import importlib
    import src.database as db_module  # noqa: PLC0415

    importlib.reload(db_module)
    db_module.initialize_database()

    from src.gri_framework import GRI_INDICATORS

    conn = sqlite3.connect(db_path)
    sql = (
        "INSERT OR IGNORE INTO gri_indicators (code, name, category, description) "
        "VALUES (?, ?, ?, ?)"
    )
    with conn:
        conn.executemany(
            sql,
            [(i.code, i.name, i.category, i.description) for i in GRI_INDICATORS],
        )
    conn.close()
    return db_path


# ---------------------------------------------------------------------------
# Raw connection fixture (for tests that bypass the module-level DB_PATH)
# ---------------------------------------------------------------------------


@pytest.fixture()
def raw_conn(tmp_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Yield a raw in-memory sqlite3 connection with the full schema applied.

    Useful for low-level schema tests that do not go through the module API.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    schema = """
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            sector TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS gri_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT
        );
        CREATE TABLE IF NOT EXISTS esg_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            indicator_id INTEGER NOT NULL,
            score REAL,
            evidence_notes TEXT,
            assessed_date TEXT,
            assessor TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (indicator_id) REFERENCES gri_indicators(id)
        );
        CREATE TABLE IF NOT EXISTS evidence_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER,
            filename TEXT NOT NULL,
            file_data BLOB,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assessment_id) REFERENCES esg_assessments(id)
        );
    """
    conn.executescript(schema)
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_supplier_data() -> dict[str, str]:
    """Return a single supplier record as a plain dict (immutable snapshot)."""
    return {
        "name": "Green Energy Corp",
        "location": "Oslo, Norway",
        "sector": "Energy",
    }


@pytest.fixture()
def sample_suppliers_df() -> pd.DataFrame:
    """Return a fresh DataFrame of two supplier rows."""
    return pd.DataFrame(
        {
            "id": [1, 2],
            "name": ["Green Energy Corp", "CleanTech Ltd"],
            "location": ["Oslo, Norway", "Berlin, Germany"],
            "sector": ["Energy", "Technology"],
        }
    )


@pytest.fixture()
def sample_assessments_df() -> pd.DataFrame:
    """Return a fresh DataFrame of assessments covering all three ESG categories."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5, 6],
            "supplier_name": [
                "Green Energy Corp",
                "Green Energy Corp",
                "Green Energy Corp",
                "CleanTech Ltd",
                "CleanTech Ltd",
                "CleanTech Ltd",
            ],
            "indicator_code": [
                "GRI 302-1",
                "GRI 401-1",
                "GRI 205-1",
                "GRI 303-1",
                "GRI 403-1",
                "GRI 206-1",
            ],
            "category": [
                "Environmental",
                "Social",
                "Governance",
                "Environmental",
                "Social",
                "Governance",
            ],
            "score": [80.0, 75.0, 90.0, 40.0, 35.0, 20.0],
            "evidence_notes": ["Note A", "Note B", "Note C", "Note D", "Note E", "Note F"],
            "assessed_date": [
                "2024-01-15",
                "2024-01-15",
                "2024-01-15",
                "2024-02-10",
                "2024-02-10",
                "2024-02-10",
            ],
            "assessor": ["Alice"] * 3 + ["Bob"] * 3,
        }
    )


@pytest.fixture()
def sample_category_scores_df() -> pd.DataFrame:
    """Return a pre-computed category scores DataFrame."""
    return pd.DataFrame(
        {
            "supplier_name": [
                "Green Energy Corp",
                "Green Energy Corp",
                "Green Energy Corp",
                "CleanTech Ltd",
                "CleanTech Ltd",
                "CleanTech Ltd",
            ],
            "category": [
                "Environmental",
                "Social",
                "Governance",
                "Environmental",
                "Social",
                "Governance",
            ],
            "avg_score": [80.0, 75.0, 90.0, 40.0, 35.0, 20.0],
            "risk_level": ["Good", "Good", "Excellent", "High", "High", "Critical"],
        }
    )


@pytest.fixture()
def sample_overall_scores_df() -> pd.DataFrame:
    """Return a pre-computed overall scores DataFrame."""
    return pd.DataFrame(
        {
            "supplier_name": ["Green Energy Corp", "CleanTech Ltd"],
            "environmental_score": [80.0, 40.0],
            "social_score": [75.0, 35.0],
            "governance_score": [90.0, 20.0],
            "overall_score": [81.25, 33.75],
            "risk_level": ["Good", "High"],
        }
    )


@pytest.fixture()
def sample_gri_indicators() -> list[dict[str, str]]:
    """Return a list of representative GRI indicator dicts."""
    return [
        {
            "code": "GRI 302-1",
            "name": "Energy Consumption Within the Organization",
            "category": "Environmental",
            "description": "Total fuel consumption.",
        },
        {
            "code": "GRI 401-1",
            "name": "New Employee Hires and Employee Turnover",
            "category": "Social",
            "description": "Total number and rate of new employee hires.",
        },
        {
            "code": "GRI 205-1",
            "name": "Operations Assessed for Corruption Risks",
            "category": "Governance",
            "description": "Total number of operations assessed.",
        },
    ]
