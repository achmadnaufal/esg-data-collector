"""
Evidence Upload page for ESG Data Collector.
Handles file uploads (PDF, images, DOCX) linked to existing assessments.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.database import (
    create_evidence_file,
    get_assessments,
    get_evidence_file_data,
    get_evidence_files,
)

ALLOWED_TYPES: list[str] = ["pdf", "png", "jpg", "jpeg", "docx"]
MAX_FILE_SIZE_MB: int = 10


def _build_assessment_label(assessment: dict) -> str:
    """Format a human-readable label for an assessment dropdown option."""
    return (
        f"[ID {assessment['id']}] {assessment['supplier_name']} — "
        f"{assessment['indicator_code']} ({assessment['assessed_date']})"
    )


def _render_upload_form() -> None:
    """Render the evidence file upload form."""
    st.subheader("Upload Evidence File")

    assessments = get_assessments()
    if not assessments:
        st.warning("No assessments available. Create an assessment first in Data Entry.")
        return

    assessment_options: dict[str, int] = {
        _build_assessment_label(a): a["id"] for a in assessments
    }

    with st.form("evidence_upload_form", clear_on_submit=True):
        selected_label = st.selectbox(
            "Link to Assessment", options=list(assessment_options.keys())
        )
        uploaded_file = st.file_uploader(
            "Select File",
            type=ALLOWED_TYPES,
            help=f"Accepted formats: {', '.join(ALLOWED_TYPES).upper()} — max {MAX_FILE_SIZE_MB} MB",
        )
        submitted = st.form_submit_button("Upload File", type="primary")

    if submitted:
        if uploaded_file is None:
            st.error("Please select a file to upload.")
            return

        file_bytes = uploaded_file.read()
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            st.error(
                f"File size ({size_mb:.1f} MB) exceeds the {MAX_FILE_SIZE_MB} MB limit."
            )
            return

        try:
            assessment_id = assessment_options[selected_label]
            new_id = create_evidence_file(
                assessment_id=assessment_id,
                filename=uploaded_file.name,
                file_data=file_bytes,
            )
            st.success(
                f"File '{uploaded_file.name}' uploaded successfully (Evidence ID: {new_id})."
            )
            st.rerun()
        except Exception as exc:
            st.error(f"Upload failed: {exc}")


def _render_evidence_list() -> None:
    """Display the list of uploaded evidence files with download buttons."""
    st.subheader("Uploaded Evidence Files")

    files = get_evidence_files()
    if not files:
        st.info("No evidence files uploaded yet.")
        return

    df = pd.DataFrame(files)
    display_df = df[["id", "filename", "supplier_name", "assessment_id", "uploaded_at"]].copy()
    display_df.columns = ["File ID", "Filename", "Supplier", "Assessment ID", "Uploaded At"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("**Download a file:**")
    file_options: dict[str, int] = {
        f"[ID {f['id']}] {f['filename']} — {f['supplier_name']}": f["id"] for f in files
    }
    selected_file_label = st.selectbox(
        "Choose file to download", options=list(file_options.keys()), key="download_select"
    )

    if st.button("Prepare Download", key="prepare_download_btn"):
        file_id = file_options[selected_file_label]
        result = get_evidence_file_data(file_id)
        if result is None:
            st.error("File data not found.")
            return
        filename, file_data = result
        st.download_button(
            label=f"Download '{filename}'",
            data=file_data,
            file_name=filename,
            mime="application/octet-stream",
            key=f"download_btn_{file_id}",
        )


def render() -> None:
    """Entry point called by app.py to render the Evidence Upload page."""
    st.title("Evidence Upload")
    st.markdown(
        "Attach supporting documents (policies, certifications, audit reports) "
        "to ESG assessments."
    )

    _render_upload_form()
    st.divider()
    _render_evidence_list()
