import streamlit as st
import pandas as pd
from db import get_dashboard_metrics

st.set_page_config(
    page_title="Job Application Tracker",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Job Application Tracker")
st.caption("Track companies, jobs, applications, and your recruiting progress in one place.")

metrics = get_dashboard_metrics()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Companies", metrics["total_companies"])

with col2:
    st.metric("Total Jobs", metrics["total_jobs"])

with col3:
    st.metric("Total Applications", metrics["total_applications"])

st.subheader("Applications by Status")

status_df = pd.DataFrame(metrics["status_counts"])
if not status_df.empty:
    st.dataframe(status_df, use_container_width=True, hide_index=True)
else:
    st.info("No status data available yet.")

st.subheader("Recent Applications")

recent_df = pd.DataFrame(metrics["recent_applications"])
if not recent_df.empty:
    st.dataframe(recent_df, use_container_width=True, hide_index=True)
else:
    st.info("No applications have been added yet.")