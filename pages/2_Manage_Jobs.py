import streamlit as st
import pandas as pd
from db import (
    get_companies,
    get_jobs,
    validate_job,
    insert_job,
    update_job,
    delete_job,
    JOB_TYPES,
    validate_company,
    insert_company,
)

st.set_page_config(page_title="Manage Jobs", page_icon="💼", layout="wide")

st.title("💼 Manage Jobs")
st.caption("Track individual job postings at companies you are targeting.")

search_term = st.text_input(
    "Search by job title or company",
    placeholder="Type a title or company...",
)

companies = get_companies()
jobs      = get_jobs(search_term)
jobs_df   = pd.DataFrame(jobs)

valid_company_ids = [c["id"] for c in companies]
company_options   = {c["name"]: c["id"] for c in companies}

# ---------------------------------------------------------------------------
# Quick-add company
# ---------------------------------------------------------------------------

with st.expander("Add New Company"):
    with st.form("quick_add_company_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_company_name     = st.text_input("Company Name *")
            new_company_industry = st.text_input("Industry")
        with col2:
            new_company_location = st.text_input("Location")
            new_company_website  = st.text_input("Website", placeholder="https://...")

        if st.form_submit_button("Add Company"):
            errors = validate_company(new_company_name)
            if errors:
                for err in errors:
                    st.error(err)
            else:
                success, error = insert_company(
                    new_company_name, new_company_industry,
                    new_company_location, new_company_website,
                )
                if success:
                    st.success(f'"{new_company_name}" added. You can now select it in the job form below.')
                    st.rerun()
                else:
                    st.error(f"Error adding company: {error}")

# ---------------------------------------------------------------------------
# Add
# ---------------------------------------------------------------------------

with st.expander("Add New Job", expanded=True):
    if not companies:
        st.warning("Add at least one company before adding a job.")
    else:
        with st.form("add_job_form", clear_on_submit=True):
            st.markdown("### New Job")

            col1, col2 = st.columns(2)

            with col1:
                selected_company = st.selectbox(
                    "Company *", options=list(company_options.keys())
                )
                title    = st.text_input("Job Title *")
                job_type = st.selectbox("Job Type", options=[""] + JOB_TYPES)

            with col2:
                salary      = st.number_input(
                    "Salary (annual $)", min_value=0, step=1000, value=0
                )
                posting_url = st.text_input("Posting URL", placeholder="https://...")

            if st.form_submit_button("Add Job"):
                company_id = company_options[selected_company]
                errors = validate_job(title, company_id, valid_company_ids)
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    success, error = insert_job(
                        company_id, title,
                        salary if salary > 0 else None,
                        job_type, posting_url,
                    )
                    if success:
                        st.success("Job added successfully.")
                        st.rerun()
                    else:
                        st.error(f"Error adding job: {error}")

# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

st.subheader("Jobs")

if not jobs_df.empty:
    st.dataframe(jobs_df, use_container_width=True, hide_index=True)
else:
    if search_term.strip():
        st.info("No jobs matched your search.")
    else:
        st.info("No jobs found. Add one above.")

# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------

st.markdown("### Edit Job")

if jobs and companies:
    job_options = {
        f"{j['company_name']} — {j['title']} (ID: {j['id']})": j["id"]
        for j in jobs
    }

    selected_label = st.selectbox(
        "Choose a job to edit",
        options=["Select a job"] + list(job_options.keys()),
    )

    if selected_label != "Select a job":
        sel_id  = job_options[selected_label]
        sel_job = next(j for j in jobs if j["id"] == sel_id)

        with st.form("edit_job_form"):
            col1, col2 = st.columns(2)

            with col1:
                edit_company = st.selectbox(
                    "Company *",
                    options=list(company_options.keys()),
                    index=list(company_options.keys()).index(sel_job["company_name"])
                    if sel_job["company_name"] in company_options else 0,
                )
                edit_title    = st.text_input("Job Title *", value=sel_job["title"])
                edit_job_type = st.selectbox(
                    "Job Type",
                    options=[""] + JOB_TYPES,
                    index=([""] + JOB_TYPES).index(sel_job["job_type"])
                    if sel_job["job_type"] in JOB_TYPES else 0,
                )

            with col2:
                edit_salary = st.number_input(
                    "Salary (annual $)",
                    min_value=0,
                    step=1000,
                    value=int(sel_job["salary"]) if sel_job["salary"] else 0,
                )
                edit_posting_url = st.text_input(
                    "Posting URL", value=sel_job["posting_url"] or ""
                )

            if st.form_submit_button("Update Job"):
                edit_company_id = company_options[edit_company]
                errors = validate_job(edit_title, edit_company_id, valid_company_ids)
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    success, error = update_job(
                        sel_id, edit_company_id, edit_title,
                        edit_salary if edit_salary > 0 else None,
                        edit_job_type, edit_posting_url,
                    )
                    if success:
                        st.success("Job updated successfully.")
                        st.rerun()
                    else:
                        st.error(f"Error updating job: {error}")
else:
    st.info("Add companies and jobs before editing.")

# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

st.markdown("### Delete Job")

if jobs:
    delete_options = {
        f"{j['company_name']} — {j['title']} (ID: {j['id']})": j["id"]
        for j in jobs
    }

    delete_label = st.selectbox(
        "Choose a job to delete",
        options=["Select a job to delete"] + list(delete_options.keys()),
        key="delete_job_select",
    )

    if delete_label != "Select a job to delete":
        delete_id = delete_options[delete_label]
        confirmed = st.checkbox(
            "I understand this will also delete any applications linked to this job."
        )

        if st.button("Delete Job", type="primary"):
            if not confirmed:
                st.warning("Please confirm deletion before continuing.")
            else:
                success, error = delete_job(delete_id)
                if success:
                    st.success("Job deleted successfully.")
                    st.rerun()
                else:
                    st.error(f"Error deleting job: {error}")
else:
    st.info("No jobs available to delete.")
