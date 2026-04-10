"""
Home.py — Dashboard page for the Job Tracker app.

This page does two things every time it loads:
  1. Calls init_db() to create tables if they don't exist yet.
     This is what prevents the UndefinedTable crash on Streamlit Cloud.
  2. Shows live summary metrics pulled from the database.
"""

import streamlit as st
import pandas as pd
from db import init_db, get_dashboard_metrics

# ---------------------------------------------------------------------------
# Page config (must be the very first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Job Application Tracker",
    page_icon="📊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Bootstrap the database
# ---------------------------------------------------------------------------
# init_db() runs CREATE TABLE IF NOT EXISTS for every table.
# On a fresh Streamlit Cloud deployment the tables won't exist yet —
# this call creates them before any SELECT is attempted.

init_db()

# ---------------------------------------------------------------------------
# Page content
# ---------------------------------------------------------------------------

st.title("📊 Job Application Tracker")
st.caption("Track companies, contacts, and applications all in one place.")

metrics = get_dashboard_metrics()

# -- Top-level counts --------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Companies Tracked", metrics["total_companies"])

with col2:
    st.metric("Contacts Added", metrics["total_contacts"])

with col3:
    st.metric("Applications Submitted", metrics["total_applications"])

st.divider()

# -- Applications by status --------------------------------------------------

st.subheader("Applications by Status")

if metrics["status_counts"]:
    status_df = pd.DataFrame(
        metrics["status_counts"],
        columns=["Status", "Count"],
    )
    st.dataframe(status_df, use_container_width=True, hide_index=True)
else:
    st.info("No applications yet — add your first one on the Manage Applications page.")

# -- Recent activity ---------------------------------------------------------

st.subheader("Recent Applications")

if metrics["recent_applications"]:
    recent_df = pd.DataFrame(
        metrics["recent_applications"],
        columns=["Job Title", "Company", "Status", "Applied Date"],
    )
    st.dataframe(recent_df, use_container_width=True, hide_index=True)
else:
    st.info("Your most recently submitted applications will appear here.")
