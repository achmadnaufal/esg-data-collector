"""
Data Entry page for ESG Data Collector.
Forms for adding suppliers and creating ESG assessments.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from src.database import (
    create_assessment,
    create_supplier,
    get_assessments,
    get_gri_indicators,
    get_suppliers,
)

INDONESIAN_LOCATIONS: list[str] = [
    "Jakarta",
    "Surabaya",
    "Bandung",
    "Medan",
    "Semarang",
    "Makassar",
    "Palembang",
    "Tangerang",
    "Depok",
    "Bekasi",
    "Balikpapan",
    "Batam",
]

SECTORS: list[str] = [
    "Mining",
    "Palm Oil",
    "Textiles",
    "Manufacturing",
    "Construction",
    "Energy",
    "Agriculture",
    "Forestry",
    "Fisheries",
    "Transportation",
]


def _render_add_supplier_form() -> None:
    """Render and handle the Add Supplier form."""
    st.subheader("Add New Supplier")
    with st.form("add_supplier_form", clear_on_submit=True):
        name = st.text_input("Company Name", placeholder="e.g. PT Maju Bersama Tbk")
        location = st.selectbox("Location", options=INDONESIAN_LOCATIONS)
        sector = st.selectbox("Sector", options=SECTORS)
        submitted = st.form_submit_button("Add Supplier", type="primary")

    if submitted:
        name_stripped = name.strip()
        if not name_stripped:
            st.error("Company name is required.")
            return
        try:
            new_id = create_supplier(name_stripped, location, sector)
            st.success(f"Supplier '{name_stripped}' added successfully (ID: {new_id}).")
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to add supplier: {exc}")


def _render_supplier_table() -> None:
    """Display the current list of suppliers."""
    st.subheader("Registered Suppliers")
    suppliers = get_suppliers()
    if not suppliers:
        st.info("No suppliers yet. Add one using the form above.")
        return
    df = pd.DataFrame(suppliers).drop(columns=["created_at"], errors="ignore")
    df.columns = [c.replace("_", " ").title() for c in df.columns]
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_add_assessment_form() -> None:
    """Render and handle the Add Assessment form."""
    st.subheader("Create ESG Assessment")

    suppliers = get_suppliers()
    indicators = get_gri_indicators()

    if not suppliers:
        st.warning("Please add at least one supplier before creating an assessment.")
        return
    if not indicators:
        st.warning("GRI indicators not loaded. Restart the application.")
        return

    supplier_options = {f"{s['name']} ({s['location']})": s["id"] for s in suppliers}
    indicator_options = {
        f"{i['code']} — {i['name']} [{i['category']}]": i["id"] for i in indicators
    }

    with st.form("add_assessment_form", clear_on_submit=True):
        selected_supplier_label = st.selectbox("Supplier", options=list(supplier_options.keys()))
        selected_indicator_label = st.selectbox(
            "GRI Indicator", options=list(indicator_options.keys())
        )
        score = st.slider("Score (0 – 100)", min_value=0, max_value=100, value=50, step=1)
        assessor = st.text_input("Assessor Name", placeholder="e.g. Budi Santoso")
        assessed_date = st.date_input("Assessment Date", value=date.today())
        evidence_notes = st.text_area(
            "Evidence Notes",
            placeholder="Describe the evidence supporting this score…",
            height=100,
        )
        submitted = st.form_submit_button("Submit Assessment", type="primary")

    if submitted:
        if not assessor.strip():
            st.error("Assessor name is required.")
            return
        try:
            supplier_id = supplier_options[selected_supplier_label]
            indicator_id = indicator_options[selected_indicator_label]
            new_id = create_assessment(
                supplier_id=supplier_id,
                indicator_id=indicator_id,
                score=float(score),
                evidence_notes=evidence_notes.strip(),
                assessed_date=str(assessed_date),
                assessor=assessor.strip(),
            )
            st.success(f"Assessment recorded successfully (ID: {new_id}).")
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to save assessment: {exc}")


def _render_recent_assessments() -> None:
    """Show a table of the most recent assessments."""
    st.subheader("Recent Assessments")
    assessments = get_assessments()
    if not assessments:
        st.info("No assessments yet.")
        return

    display_cols = [
        "supplier_name",
        "indicator_code",
        "indicator_name",
        "category",
        "score",
        "assessor",
        "assessed_date",
    ]
    df = pd.DataFrame(assessments)
    available_cols = [c for c in display_cols if c in df.columns]
    df = df[available_cols].head(50)
    df.columns = [c.replace("_", " ").title() for c in df.columns]
    st.dataframe(df, use_container_width=True, hide_index=True)


def render() -> None:
    """Entry point called by app.py to render the Data Entry page."""
    st.title("Data Entry")
    st.markdown("Add suppliers and record ESG assessments aligned with the GRI framework.")

    tab_supplier, tab_assessment = st.tabs(["Suppliers", "Assessments"])

    with tab_supplier:
        _render_add_supplier_form()
        st.divider()
        _render_supplier_table()

    with tab_assessment:
        _render_add_assessment_form()
        st.divider()
        _render_recent_assessments()
