"""
Extended database tests covering helper functions not exercised in the main
test_database.py suite: get_supplier_by_id, evidence file CRUD, and the
rollback path in the connection context manager.
"""

from __future__ import annotations

import importlib
import os
import sqlite3

import pytest


# ---------------------------------------------------------------------------
# Re-usable reload helper (mirrors test_database.py)
# ---------------------------------------------------------------------------


def _reload_db(db_path: str):
    os.environ["ESG_DB_PATH"] = db_path
    import src.database as m  # noqa: PLC0415

    importlib.reload(m)
    return m


def _seed_indicator(db_path: str, code: str = "GRI 302-1") -> int:
    conn = sqlite3.connect(db_path)
    with conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO gri_indicators (code, name, category, description) "
            "VALUES (?, ?, ?, ?)",
            (code, "Test Indicator", "Environmental", "Desc"),
        )
        if cursor.lastrowid:
            return int(cursor.lastrowid)
        row = conn.execute(
            "SELECT id FROM gri_indicators WHERE code = ?", (code,)
        ).fetchone()
    conn.close()
    return int(row[0])


# ---------------------------------------------------------------------------
# get_supplier_by_id
# ---------------------------------------------------------------------------


def test_get_supplier_by_id_existing(db_path: str) -> None:
    """get_supplier_by_id returns a dict for an existing supplier ID."""
    db = _reload_db(db_path)
    new_id = db.create_supplier("Widget Co", "Sydney, AU", "Manufacturing")

    result = db.get_supplier_by_id(new_id)

    assert result is not None
    assert result["name"] == "Widget Co"
    assert result["id"] == new_id


def test_get_supplier_by_id_missing_returns_none(db_path: str) -> None:
    """get_supplier_by_id returns None when the ID does not exist."""
    db = _reload_db(db_path)

    result = db.get_supplier_by_id(99999)

    assert result is None


def test_get_supplier_by_id_preserves_all_fields(db_path: str) -> None:
    """The returned dict contains name, location, and sector fields."""
    db = _reload_db(db_path)
    new_id = db.create_supplier("TechFirm", "Toronto, CA", "Technology")

    result = db.get_supplier_by_id(new_id)

    assert result is not None
    assert result["location"] == "Toronto, CA"
    assert result["sector"] == "Technology"


# ---------------------------------------------------------------------------
# Evidence file CRUD
# ---------------------------------------------------------------------------


def test_create_evidence_file_returns_id(db_path: str) -> None:
    """create_evidence_file returns a positive integer row ID."""
    db = _reload_db(db_path)
    supplier_id = db.create_supplier("Eco Corp", "Berlin", "Energy")
    indicator_id = _seed_indicator(db_path)
    assessment_id = db.create_assessment(
        supplier_id, indicator_id, 70.0, "", "2024-01-01", "Alice"
    )

    file_id = db.create_evidence_file(assessment_id, "report.pdf", b"PDF content here")

    assert isinstance(file_id, int)
    assert file_id > 0


def test_get_evidence_files_returns_uploaded_file(db_path: str) -> None:
    """get_evidence_files returns metadata for every uploaded file."""
    db = _reload_db(db_path)
    supplier_id = db.create_supplier("Eco Corp", "Berlin", "Energy")
    indicator_id = _seed_indicator(db_path)
    assessment_id = db.create_assessment(
        supplier_id, indicator_id, 65.0, "", "2024-02-01", "Bob"
    )
    db.create_evidence_file(assessment_id, "evidence.xlsx", b"\x00binary\x00")

    files = db.get_evidence_files()

    assert len(files) == 1
    assert files[0]["filename"] == "evidence.xlsx"


def test_get_evidence_file_data_returns_correct_bytes(db_path: str) -> None:
    """get_evidence_file_data returns the exact bytes that were stored."""
    db = _reload_db(db_path)
    supplier_id = db.create_supplier("DataCo", "New York", "Finance")
    indicator_id = _seed_indicator(db_path)
    assessment_id = db.create_assessment(
        supplier_id, indicator_id, 50.0, "", "2024-03-15", "Carol"
    )
    payload = b"ESG Report 2024"
    file_id = db.create_evidence_file(assessment_id, "report.txt", payload)

    result = db.get_evidence_file_data(file_id)

    assert result is not None
    filename, data = result
    assert filename == "report.txt"
    assert data == payload


def test_get_evidence_file_data_missing_returns_none(db_path: str) -> None:
    """get_evidence_file_data returns None for a non-existent file ID."""
    db = _reload_db(db_path)

    result = db.get_evidence_file_data(99999)

    assert result is None


# ---------------------------------------------------------------------------
# Context manager rollback path
# ---------------------------------------------------------------------------


def test_rollback_on_integrity_error(db_path: str) -> None:
    """A constraint violation inside get_connection rolls back and re-raises."""
    db = _reload_db(db_path)

    # Seed an indicator with code "GRI-UNIQUE" once.
    with db.get_connection() as conn:
        conn.execute(
            "INSERT INTO gri_indicators (code, name, category) VALUES (?, ?, ?)",
            ("GRI-UNIQUE", "First Insert", "Environmental"),
        )

    # A second insert of the same UNIQUE code must raise and rollback.
    with pytest.raises(sqlite3.IntegrityError):
        with db.get_connection() as conn:
            conn.execute(
                "INSERT INTO gri_indicators (code, name, category) VALUES (?, ?, ?)",
                ("GRI-UNIQUE", "Duplicate Code", "Environmental"),
            )

    # The table should still have exactly one row with that code.
    with db.get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM gri_indicators WHERE code = 'GRI-UNIQUE'"
        ).fetchone()[0]
    assert count == 1
