"""
Tests for src/export.py — CSV export and report summary generation.

All tests construct fresh DataFrames inline or via fixtures so there is no
shared mutable state between test functions.
"""

from __future__ import annotations

import io

import pandas as pd
import pytest

from src.export import export_to_csv, generate_report_summary
from src.scoring import RISK_CRITICAL, RISK_EXCELLENT, RISK_GOOD, RISK_HIGH, RISK_MEDIUM


# ---------------------------------------------------------------------------
# export_to_csv
# ---------------------------------------------------------------------------


def test_export_to_csv_returns_bytes(sample_assessments_df: pd.DataFrame) -> None:
    """export_to_csv must return a bytes object."""
    result = export_to_csv(sample_assessments_df)

    assert isinstance(result, bytes)


def test_export_to_csv_content_is_valid_csv(
    sample_assessments_df: pd.DataFrame,
) -> None:
    """The exported bytes must be parseable back into a DataFrame."""
    raw_bytes = export_to_csv(sample_assessments_df)
    recovered = pd.read_csv(io.BytesIO(raw_bytes))

    assert len(recovered) == len(sample_assessments_df)


def test_export_csv_headers(sample_assessments_df: pd.DataFrame) -> None:
    """Exported CSV must preserve the original column names as headers."""
    raw_bytes = export_to_csv(sample_assessments_df)
    header_line = raw_bytes.decode("utf-8").splitlines()[0]
    csv_columns = header_line.split(",")

    for col in sample_assessments_df.columns:
        assert col in csv_columns


def test_export_csv_row_count(sample_assessments_df: pd.DataFrame) -> None:
    """Number of data rows in the CSV must match the source DataFrame."""
    raw_bytes = export_to_csv(sample_assessments_df)
    recovered = pd.read_csv(io.BytesIO(raw_bytes))

    assert len(recovered) == len(sample_assessments_df)


def test_export_empty_dataframe() -> None:
    """Exporting an empty DataFrame must return bytes (header-only CSV or empty)."""
    empty_df = pd.DataFrame(columns=["supplier_name", "score", "category"])
    result = export_to_csv(empty_df)

    assert isinstance(result, bytes)
    # Must contain at least the header row.
    text = result.decode("utf-8")
    assert "supplier_name" in text


def test_export_to_csv_does_not_mutate_input(
    sample_assessments_df: pd.DataFrame,
) -> None:
    """export_to_csv must not alter the input DataFrame."""
    original_shape = sample_assessments_df.shape
    original_columns = list(sample_assessments_df.columns)

    export_to_csv(sample_assessments_df)

    assert sample_assessments_df.shape == original_shape
    assert list(sample_assessments_df.columns) == original_columns


def test_export_csv_encoding_is_utf8(sample_assessments_df: pd.DataFrame) -> None:
    """The CSV bytes must be valid UTF-8."""
    raw_bytes = export_to_csv(sample_assessments_df)

    decoded = raw_bytes.decode("utf-8")
    assert isinstance(decoded, str)


# ---------------------------------------------------------------------------
# generate_report_summary
# ---------------------------------------------------------------------------


def test_generate_report_summary_returns_string(
    sample_overall_scores_df: pd.DataFrame,
) -> None:
    """generate_report_summary must return a non-empty string."""
    result = generate_report_summary(sample_overall_scores_df)

    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_report_summary_contains_supplier_count(
    sample_overall_scores_df: pd.DataFrame,
) -> None:
    """Report summary must mention the total number of suppliers assessed."""
    result = generate_report_summary(sample_overall_scores_df)

    assert "2" in result  # two suppliers in the fixture


def test_generate_report_summary_contains_top_performer(
    sample_overall_scores_df: pd.DataFrame,
) -> None:
    """Report summary must name the highest-scoring supplier."""
    result = generate_report_summary(sample_overall_scores_df)

    # Green Energy Corp has score 81.25 — the highest in the fixture.
    assert "Green Energy Corp" in result


def test_generate_report_summary_contains_risk_levels(
    sample_overall_scores_df: pd.DataFrame,
) -> None:
    """Report summary must reference each risk level label."""
    result = generate_report_summary(sample_overall_scores_df)

    for level in [RISK_CRITICAL, RISK_HIGH, RISK_MEDIUM, RISK_GOOD, RISK_EXCELLENT]:
        assert level in result


def test_generate_report_summary_empty_dataframe() -> None:
    """An empty scores DataFrame must produce a 'no data' message, not raise."""
    empty_df = pd.DataFrame(
        columns=["supplier_name", "overall_score", "risk_level"]
    )
    result = generate_report_summary(empty_df)

    assert isinstance(result, str)
    assert len(result) > 0
    assert "no" in result.lower() or "empty" in result.lower() or "available" in result.lower()


def test_generate_report_summary_missing_column_raises() -> None:
    """Passing a DataFrame that lacks required columns must raise ValueError."""
    bad_df = pd.DataFrame({"supplier_name": ["A"], "overall_score": [60.0]})

    with pytest.raises(ValueError, match="missing columns"):
        generate_report_summary(bad_df)


def test_generate_report_summary_does_not_mutate_input(
    sample_overall_scores_df: pd.DataFrame,
) -> None:
    """generate_report_summary must not alter the input DataFrame."""
    original_shape = sample_overall_scores_df.shape

    generate_report_summary(sample_overall_scores_df)

    assert sample_overall_scores_df.shape == original_shape
