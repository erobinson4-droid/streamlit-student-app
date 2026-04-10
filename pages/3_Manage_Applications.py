import streamlit as st
import pandas as pd
from db import (
    get_jobs,
    get_statuses,
    get_applications,
    validate_application_input,
    insert_application,
    update_application,
    delete_application,
)

st.set_page_config(page_title="Manage Applications", page_icon="📄", layout="wide")

st.title("📄 Manage Applications")
st.caption("Track application status, dates, and notes for every role.")

search_term = st.text_input(
    "Search by company name or job title",
    placeholder="Type a company or job title...",
)

jobs = get_jobs()
statuses = get_statuses()
applications = get_applications(search_term)

applications_df = pd.DataFrame(applications)

valid_job_ids = [job["id"] for job in jobs]
valid_status_ids = [status["id"] for status in statuses]

job_select_options = {
    f"{job['company_name']} - {job['title']} (ID: {job['id']})": job["id"]
    for job in jobs
}

status_select_options = {
    status["status_name"]: status["id"]
    for status in statuses
}

with st.expander("Add New Application", expanded=True):
    if not jobs:
        st.warning("You need at least one job before adding an application.")
    elif not statuses:
        st.warning("You need status records in the database before adding an application.")
    else:
        with st.form("add_application_form", clear_on_submit=True):
            st.markdown("### New Application")

            col1, col2 = st.columns(2)

            with col1:
                selected_job_label = st.selectbox(
                    "Job *",
                    options=list(job_select_options.keys()),
                )
                selected_status_label = st.selectbox(
                    "Status *",
                    options=list(status_select_options.keys()),
                )

            with col2:
                applied_date = st.date_input("Applied Date *")
                notes = st.text_area("Notes")

            submitted = st.form_submit_button("Add Application")

            if submitted:
                job_id = job_select_options[selected_job_label]
                status_id = status_select_options[selected_status_label]

                errors = validate_application_input(
                    job_id,
                    status_id,
                    applied_date,
                    valid_job_ids,
                    valid_status_ids,
                )

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    success, error = insert_application(
                        job_id,
                        status_id,
                        applied_date,
                        notes,
                    )
                    if success:
                        st.success("Application added successfully.")
                        st.rerun()
                    else:
                        st.error(error)

st.subheader("Applications")

if not applications_df.empty:
    st.dataframe(applications_df, use_container_width=True, hide_index=True)
else:
    if search_term.strip():
        st.info("No applications matched your search.")
    else:
        st.info("No applications found.")

st.markdown("### Edit Application")

if applications and jobs and statuses:
    application_options = {
        f"{app['company_name']} - {app['job_title']} - {app['status_name']} (ID: {app['id']})": app["id"]
        for app in applications
    }

    selected_application_label = st.selectbox(
        "Choose an application to edit",
        options=["Select an application"] + list(application_options.keys()),
    )

    if selected_application_label != "Select an application":
        selected_application_id = application_options[selected_application_label]
        selected_application = next(a for a in applications if a["id"] == selected_application_id)

        reverse_job_lookup = {
            job["id"]: f"{job['company_name']} - {job['title']} (ID: {job['id']})"
            for job in jobs
        }
        reverse_status_lookup = {
            status["id"]: status["status_name"]
            for status in statuses
        }

        with st.form("edit_application_form"):
            edit_job_label = st.selectbox(
                "Job *",
                options=list(job_select_options.keys()),
                index=list(job_select_options.keys()).index(
                    reverse_job_lookup[selected_application["job_id"]]
                ),
            )

            edit_status_label = st.selectbox(
                "Status *",
                options=list(status_select_options.keys()),
                index=list(status_select_options.keys()).index(
                    reverse_status_lookup[selected_application["status_id"]]
                ),
            )

            edit_applied_date = st.date_input(
                "Applied Date *",
                value=selected_application["applied_date"],
            )

            edit_notes = st.text_area(
                "Notes",
                value=selected_application["notes"] or "",
            )

            update_submitted = st.form_submit_button("Update Application")

            if update_submitted:
                edit_job_id = job_select_options[edit_job_label]
                edit_status_id = status_select_options[edit_status_label]

                errors = validate_application_input(
                    edit_job_id,
                    edit_status_id,
                    edit_applied_date,
                    valid_job_ids,
                    valid_status_ids,
                )

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    success, error = update_application(
                        selected_application_id,
                        edit_job_id,
                        edit_status_id,
                        edit_applied_date,
                        edit_notes,
                    )
                    if success:
                        st.success("Application updated successfully.")
                        st.rerun()
                    else:
                        st.error(error)
else:
    st.info("Add jobs, statuses, and applications before editing.")

st.markdown("### Delete Application")

if applications:
    delete_application_label = st.selectbox(
        "Choose an application to delete",
        options=["Select an application to delete"] + list(application_options.keys()),
        key="delete_application_select",
    )

    if delete_application_label != "Select an application to delete":
        delete_application_id_value = application_options[delete_application_label]

        confirm_delete = st.checkbox("I understand and want to delete this application.")

        if st.button("Delete Application", type="primary"):
            if not confirm_delete:
                st.warning("Please confirm deletion before continuing.")
            else:
                success, error = delete_application(delete_application_id_value)
                if success:
                    st.success("Application deleted successfully.")
                    st.rerun()
                else:
                    st.error(error)
else:
    st.info("No applications available to delete.")