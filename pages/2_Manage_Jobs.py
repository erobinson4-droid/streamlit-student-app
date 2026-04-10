import streamlit as st
import pandas as pd
from db import (
    get_companies,
    get_jobs,
    validate_job_input,
    insert_job,
    update_job,
    delete_job,
)

st.set_page_config(page_title="Manage Jobs", page_icon="💼", layout="wide")

st.title("💼 Manage Jobs")
st.caption("Add and manage job listings at companies you are targeting.")

search_term = st.text_input(
    "Search by job title or company name",
    placeholder="Type a title or company...",
)

companies = get_companies()
jobs = get_jobs(search_term)
jobs_df = pd.DataFrame(jobs)

valid_company_ids = [c["id"] for c in companies]

company_options = {c["company_name"]: c["id"] for c in companies}

JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship", "Freelance"]

with st.expander("Add New Job", expanded=True):
    if not companies:
        st.warning("You need at least one company before adding a job.")
    else:
        with st.form("add_job_form", clear_on_submit=True):
            st.markdown("### New Job")

            col1, col2 = st.columns(2)

            with col1:
                selected_company_label = st.selectbox(
                    "Company *",
                    options=list(company_options.keys()),
                )
                title = st.text_input("Job Title *")
                job_type = st.selectbox("Job Type", options=[""] + JOB_TYPES)

            with col2:
                salary = st.number_input(
                    "Salary (annual)", min_value=0, step=1000, value=0
                )
                posting_url = st.text_input("Posting URL")

            submitted = st.form_submit_button("Add Job")

            if submitted:
                company_id = company_options[selected_company_label]
                errors = validate_job_input(title, company_id, valid_company_ids)
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    success, error = insert_job(
                        company_id, title, salary if salary > 0 else None,
                        job_type, posting_url
                    )
                    if success:
                        st.success("Job added successfully.")
                        st.rerun()
                    else:
                        st.error(f"Error adding job: {error}")

st.subheader("Jobs")

if not jobs_df.empty:
    st.dataframe(jobs_df, use_container_width=True, hide_index=True)
else:
    if search_term.strip():
        st.info("No jobs matched your search.")
    else:
        st.info("No jobs found. Add one above.")

st.markdown("### Edit Job")

if jobs and companies:
    job_options = {
        f"{j['company_name']} - {j['title']} (ID: {j['id']})": j["id"] for j in jobs
    }

    selected_job_label = st.selectbox(
        "Choose a job to edit",
        options=["Select a job"] + list(job_options.keys()),
    )

    if selected_job_label != "Select a job":
        selected_job_id = job_options[selected_job_label]
        selected_job = next(j for j in jobs if j["id"] == selected_job_id)

        with st.form("edit_job_form"):
            col1, col2 = st.columns(2)

            with col1:
                edit_company_label = st.selectbox(
                    "Company *",
                    options=list(company_options.keys()),
                    index=list(company_options.keys()).index(selected_job["company_name"])
                    if selected_job["company_name"] in company_options
                    else 0,
                )
                edit_title = st.text_input("Job Title *", value=selected_job["title"])
                edit_job_type = st.selectbox(
                    "Job Type",
                    options=[""] + JOB_TYPES,
                    index=([""] + JOB_TYPES).index(selected_job["job_type"])
                    if selected_job["job_type"] in JOB_TYPES
                    else 0,
                )

            with col2:
                edit_salary = st.number_input(
                    "Salary (annual)",
                    min_value=0,
                    step=1000,
                    value=int(selected_job["salary"]) if selected_job["salary"] else 0,
                )
                edit_posting_url = st.text_input(
                    "Posting URL", value=selected_job["posting_url"] or ""
                )

            update_submitted = st.form_submit_button("Update Job")

            if update_submitted:
                edit_company_id = company_options[edit_company_label]
                errors = validate_job_input(edit_title, edit_company_id, valid_company_ids)
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    success, error = update_job(
                        selected_job_id,
                        edit_company_id,
                        edit_title,
                        edit_salary if edit_salary > 0 else None,
                        edit_job_type,
                        edit_posting_url,
                    )
                    if success:
                        st.success("Job updated successfully.")
                        st.rerun()
                    else:
                        st.error(f"Error updating job: {error}")
else:
    st.info("Add companies and jobs before editing.")

st.markdown("### Delete Job")

if jobs:
    delete_job_options = {
        f"{j['company_name']} - {j['title']} (ID: {j['id']})": j["id"] for j in jobs
    }

    delete_label = st.selectbox(
        "Choose a job to delete",
        options=["Select a job to delete"] + list(delete_job_options.keys()),
        key="delete_job_select",
    )

    if delete_label != "Select a job to delete":
        delete_id = delete_job_options[delete_label]
        confirm_delete = st.checkbox(
            "I understand this will also delete all applications for this job."
        )

        if st.button("Delete Job", type="primary"):
            if not confirm_delete:
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
