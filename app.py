"""
ESG Data Collector — Main Streamlit Application Entry Point.

Run with:
    streamlit run app.py

Environment variables:
    ESG_DB_PATH  (optional) — path to the SQLite database file.
                 Defaults to 'esg_data.db' in the current working directory.
"""

from __future__ import annotations

import sys

import streamlit as st

# ---------------------------------------------------------------------------
# Page configuration — must be the very first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ESG Data Collector",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Initialise database and seed GRI indicators (runs once per session)
# ---------------------------------------------------------------------------
try:
    from src.database import initialize_database
    from src.gri_framework import seed_gri_indicators
except ImportError as exc:
    st.error(f"Failed to import application modules: {exc}")
    st.stop()


@st.cache_resource
def _bootstrap_database() -> None:
    """Create tables and seed GRI indicator data — called once per process."""
    initialize_database()
    seed_gri_indicators()


_bootstrap_database()

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "Dashboard"

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
PAGE_ICONS: dict[str, str] = {
    "Dashboard": "📊",
    "Data Entry": "📝",
    "Evidence Upload": "📎",
    "Scoring": "🏆",
    "Export": "📥",
}

with st.sidebar:
    st.title("ESG Data Collector")
    st.markdown("**GRI Framework Aligned**")
    st.divider()

    for page_name, icon in PAGE_ICONS.items():
        is_active = st.session_state["active_page"] == page_name
        button_type: str = "primary" if is_active else "secondary"
        if st.button(
            f"{icon}  {page_name}",
            key=f"nav_{page_name}",
            use_container_width=True,
            type=button_type,  # type: ignore[arg-type]
        ):
            st.session_state["active_page"] = page_name
            st.rerun()

    st.divider()
    st.markdown(
        "<small>Categories: Environmental · Social · Governance<br/>"
        "Weights: E 40% · S 35% · G 25%</small>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------
active = st.session_state["active_page"]

try:
    if active == "Dashboard":
        from src.pages.dashboard import render
        render()

    elif active == "Data Entry":
        from src.pages.data_entry import render
        render()

    elif active == "Evidence Upload":
        from src.pages.evidence import render
        render()

    elif active == "Scoring":
        from src.pages.scoring import render
        render()

    elif active == "Export":
        from src.pages.export_page import render
        render()

    else:
        st.error(f"Unknown page: '{active}'. Please select a page from the sidebar.")

except Exception as exc:
    st.error(f"An unexpected error occurred while rendering '{active}': {exc}")
    st.exception(exc)
    sys.exit(1)
