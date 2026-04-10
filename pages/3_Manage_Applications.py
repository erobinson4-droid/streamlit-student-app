import streamlit as st
import pandas as pd
from db import (
    get_companies,
    get_applications,
    validate_application,
    insert_application,
    update_application,
    delete_application,
    APPLICATION_STATUSES,
)

st.set_page_config(page_title="Manage Applications", page_icon="📄", layout="wide")

st.title("📄 Manage Applications")
st.caption("Track every role you have applied for, including status and notes.")

search_term = st.text_input(
    "Search by job title or company",
    placeholder="Type a title or company...",
)

companies    = get_companies()
applications = get_applications(search_term)
applications_df = pd.DataFrame(applications)

valid_company_ids = [c["id"] for c in companies]
company_options   = {c["name"]: c["id"] for c in companies}

# ---------------------------------------------------------------------------
# Add
# ---------------------------------------------------------------------------

with st.expander("Add New Application", expanded=True):
    if not companies:
        st.warning("Add at least one company before logging an application.")
    else:
        with st.form("add_application_form", clear_on_submit=True):
            st.markdown("### New Application")

            col1, col2 = st.columns(2)

            with col1:
                selected_company_label = st.selectbox(
                    "Company *", options=list(company_options.keys())
                )
                job_title    = st.text_input("Job Title *")
                status       = st.selectbox("Status *", options=APPLICATION_STATUSES)

            with col2:
                applied_date = st.date_input("Applied Date *")
                salary_range = st.text_input("Salary Range", placeholder="e.g. $90k – $110k")
                posting_url  = st.text_input("Posting URL")

            notes = st.text_area("Notes")

            if st.form_submit_button("Add Application"):
                company_id = company_options[selected_company_label]
                errors = validate_application(job_title, company_id, valid_company_ids, applied_date)
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    success, error = insert_application(
                        company_id, job_title, status, applied_date,
                        salary_range, posting_url, notes,
                    )
                    if success:
                        st.success("Application added successfully.")
                        st.rerun()
                    else:
                        st.error(f"Error adding application: {error}")

# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

st.subheader("Applications")

if not applications_df.empty:
    st.dataframe(applications_df, use_container_width=True, hide_index=True)
else:
    if search_term.strip():
        st.info("No applications matched your search.")
    else:
        st.info("No applications found. Add one above.")

# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------

st.markdown("### Edit Application")

if applications and companies:
    app_options = {
        f"{a['company_name']} — {a['job_title']} ({a['status']}) ID:{a['id']}": a["id"]
        for a in applications
    }

    selected_label = st.selectbox(
        "Choose an application to edit",
        options=["Select an application"] + list(app_options.keys()),
    )

    if selected_label != "Select an application":
        sel_id  = app_options[selected_label]
        sel_app = next(a for a in applications if a["id"] == sel_id)

        with st.form("edit_application_form"):
            col1, col2 = st.columns(2)

            with col1:
                edit_company_label = st.selectbox(
                    "Company *",
                    options=list(company_options.keys()),
                    index=list(company_options.keys()).index(sel_app["company_name"])
                    if sel_app["company_name"] in company_options else 0,
                )
                edit_title = st.text_input("Job Title *", value=sel_app["job_title"])
                edit_status = st.selectbox(
                    "Status *",
                    options=APPLICATION_STATUSES,
                    index=APPLICATION_STATUSES.index(sel_app["status"])
                    if sel_app["status"] in APPLICATION_STATUSES else 0,
                )

            with col2:
                edit_date        = st.date_input("Applied Date *", value=sel_app["applied_date"])
                edit_salary      = st.text_input("Salary Range",   value=sel_app["salary_range"] or "")
                edit_posting_url = st.text_input("Posting URL",    value=sel_app["posting_url"]  or "")

            edit_notes = st.text_area("Notes", value=sel_app["notes"] or "")

            if st.form_submit_button("Update Application"):
                edit_company_id = company_options[edit_company_label]
                errors = validate_application(
                    edit_title, edit_company_id, valid_company_ids, edit_date
                )
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    success, error = update_application(
                        sel_id, edit_company_id, edit_title, edit_status,
                        edit_date, edit_salary, edit_posting_url, edit_notes,
                    )
                    if success:
                        st.success("Application updated successfully.")
                        st.rerun()
                    else:
                        st.error(f"Error updating application: {error}")
else:
    st.info("Add companies and applications before editing.")

# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

st.markdown("### Delete Application")

if applications:
    delete_options = {
        f"{a['company_name']} — {a['job_title']} ID:{a['id']}": a["id"]
        for a in applications
    }

    delete_label = st.selectbox(
        "Choose an application to delete",
        options=["Select an application to delete"] + list(delete_options.keys()),
        key="delete_application_select",
    )

    if delete_label != "Select an application to delete":
        delete_id = delete_options[delete_label]
        confirmed = st.checkbox("I confirm I want to permanently delete this application.")

        if st.button("Delete Application", type="primary"):
            if not confirmed:
                st.warning("Please confirm deletion before continuing.")
            else:
                success, error = delete_application(delete_id)
                if success:
                    st.success("Application deleted successfully.")
                    st.rerun()
                else:
                    st.error(f"Error deleting application: {error}")
else:
    st.info("No applications available to delete.")
