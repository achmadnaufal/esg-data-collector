"""
Database module for ESG Data Collector.
Manages SQLite connection, schema creation, and all CRUD operations.
All queries are parameterized to prevent SQL injection.
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional
import os

DB_PATH = os.environ.get("ESG_DB_PATH", "esg_data.db")


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite connections with automatic cleanup."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    """Create all tables if they do not exist."""
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
    with get_connection() as conn:
        conn.executescript(schema)


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------

def create_supplier(name: str, location: str, sector: str) -> int:
    """Insert a new supplier and return its new ID."""
    sql = "INSERT INTO suppliers (name, location, sector) VALUES (?, ?, ?)"
    with get_connection() as conn:
        cursor = conn.execute(sql, (name, location, sector))
        return cursor.lastrowid  # type: ignore[return-value]


def get_suppliers() -> list[dict]:
    """Return all suppliers as a list of dicts."""
    sql = "SELECT id, name, location, sector, created_at FROM suppliers ORDER BY name"
    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
        return [dict(row) for row in rows]


def get_supplier_by_id(supplier_id: int) -> Optional[dict]:
    """Return a single supplier dict or None."""
    sql = "SELECT id, name, location, sector, created_at FROM suppliers WHERE id = ?"
    with get_connection() as conn:
        row = conn.execute(sql, (supplier_id,)).fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------------------------
# GRI Indicators
# ---------------------------------------------------------------------------

def upsert_gri_indicator(code: str, name: str, category: str, description: str) -> None:
    """Insert or ignore a GRI indicator (idempotent seed operation)."""
    sql = (
        "INSERT OR IGNORE INTO gri_indicators (code, name, category, description) "
        "VALUES (?, ?, ?, ?)"
    )
    with get_connection() as conn:
        conn.execute(sql, (code, name, category, description))


def get_gri_indicators() -> list[dict]:
    """Return all GRI indicators."""
    sql = "SELECT id, code, name, category, description FROM gri_indicators ORDER BY code"
    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
        return [dict(row) for row in rows]


def get_gri_indicators_by_category(category: str) -> list[dict]:
    """Return GRI indicators filtered by category."""
    sql = (
        "SELECT id, code, name, category, description "
        "FROM gri_indicators WHERE category = ? ORDER BY code"
    )
    with get_connection() as conn:
        rows = conn.execute(sql, (category,)).fetchall()
        return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Assessments
# ---------------------------------------------------------------------------

def create_assessment(
    supplier_id: int,
    indicator_id: int,
    score: float,
    evidence_notes: str,
    assessed_date: str,
    assessor: str,
) -> int:
    """Insert a new assessment and return its new ID."""
    sql = (
        "INSERT INTO esg_assessments "
        "(supplier_id, indicator_id, score, evidence_notes, assessed_date, assessor) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    )
    with get_connection() as conn:
        cursor = conn.execute(
            sql, (supplier_id, indicator_id, score, evidence_notes, assessed_date, assessor)
        )
        return cursor.lastrowid  # type: ignore[return-value]


def get_assessments() -> list[dict]:
    """Return all assessments joined with supplier and indicator info."""
    sql = """
        SELECT
            a.id,
            s.name AS supplier_name,
            g.code AS indicator_code,
            g.name AS indicator_name,
            g.category,
            a.score,
            a.evidence_notes,
            a.assessed_date,
            a.assessor,
            a.supplier_id,
            a.indicator_id
        FROM esg_assessments a
        JOIN suppliers s ON s.id = a.supplier_id
        JOIN gri_indicators g ON g.id = a.indicator_id
        ORDER BY a.id DESC
    """
    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
        return [dict(row) for row in rows]


def get_assessments_by_supplier(supplier_id: int) -> list[dict]:
    """Return assessments for a specific supplier."""
    sql = """
        SELECT
            a.id,
            g.code AS indicator_code,
            g.name AS indicator_name,
            g.category,
            a.score,
            a.evidence_notes,
            a.assessed_date,
            a.assessor
        FROM esg_assessments a
        JOIN gri_indicators g ON g.id = a.indicator_id
        WHERE a.supplier_id = ?
        ORDER BY g.category, g.code
    """
    with get_connection() as conn:
        rows = conn.execute(sql, (supplier_id,)).fetchall()
        return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Evidence Files
# ---------------------------------------------------------------------------

def create_evidence_file(
    assessment_id: int, filename: str, file_data: bytes
) -> int:
    """Store an evidence file linked to an assessment."""
    sql = (
        "INSERT INTO evidence_files (assessment_id, filename, file_data) "
        "VALUES (?, ?, ?)"
    )
    with get_connection() as conn:
        cursor = conn.execute(sql, (assessment_id, filename, file_data))
        return cursor.lastrowid  # type: ignore[return-value]


def get_evidence_files() -> list[dict]:
    """Return all evidence file metadata (no binary data)."""
    sql = (
        "SELECT ef.id, ef.assessment_id, ef.filename, ef.uploaded_at, "
        "s.name AS supplier_name "
        "FROM evidence_files ef "
        "LEFT JOIN esg_assessments a ON a.id = ef.assessment_id "
        "LEFT JOIN suppliers s ON s.id = a.supplier_id "
        "ORDER BY ef.uploaded_at DESC"
    )
    with get_connection() as conn:
        rows = conn.execute(sql).fetchall()
        return [dict(row) for row in rows]


def get_evidence_file_data(file_id: int) -> Optional[tuple[str, bytes]]:
    """Return (filename, binary_data) for a specific evidence file."""
    sql = "SELECT filename, file_data FROM evidence_files WHERE id = ?"
    with get_connection() as conn:
        row = conn.execute(sql, (file_id,)).fetchone()
        if row is None:
            return None
        return (row["filename"], bytes(row["file_data"]))
