import streamlit as st
import pandas as pd
from db import (
    get_companies,
    validate_company,
    insert_company,
    update_company,
    delete_company,
)

st.set_page_config(page_title="Manage Companies", page_icon="🏢", layout="wide")

st.title("🏢 Manage Companies")
st.caption("Add and manage the companies you are tracking for job applications.")

search_term = st.text_input(
    "Search by company name",
    placeholder="Type a company name...",
)

companies = get_companies(search_term)
companies_df = pd.DataFrame(companies)

# ---------------------------------------------------------------------------
# Add
# ---------------------------------------------------------------------------

with st.expander("Add New Company", expanded=True):
    with st.form("add_company_form", clear_on_submit=True):
        st.markdown("### New Company")

        col1, col2 = st.columns(2)

        with col1:
            company_name = st.text_input("Company Name *")
            industry     = st.text_input("Industry")

        with col2:
            location = st.text_input("Location")
            website  = st.text_input("Website", placeholder="https://...")

        submitted = st.form_submit_button("Add Company")

        if submitted:
            errors = validate_company(company_name)
            if errors:
                for err in errors:
                    st.error(err)
            else:
                success, error = insert_company(company_name, industry, location, website)
                if success:
                    st.success("Company added successfully.")
                    st.rerun()
                else:
                    st.error(f"Error adding company: {error}")

# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

st.subheader("Companies")

if not companies_df.empty:
    st.dataframe(companies_df, use_container_width=True, hide_index=True)
else:
    if search_term.strip():
        st.info("No companies matched your search.")
    else:
        st.info("No companies found. Add one above.")

# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------

st.markdown("### Edit Company")

if companies:
    company_options = {f"{c['name']} (ID: {c['id']})": c["id"] for c in companies}

    selected_label = st.selectbox(
        "Choose a company to edit",
        options=["Select a company"] + list(company_options.keys()),
    )

    if selected_label != "Select a company":
        sel_id      = company_options[selected_label]
        sel_company = next(c for c in companies if c["id"] == sel_id)

        with st.form("edit_company_form"):
            col1, col2 = st.columns(2)

            with col1:
                edit_name     = st.text_input("Company Name *", value=sel_company["name"])
                edit_industry = st.text_input("Industry",       value=sel_company["industry"] or "")

            with col2:
                edit_location = st.text_input("Location", value=sel_company["location"] or "")
                edit_website  = st.text_input("Website",  value=sel_company["website"]  or "")

            if st.form_submit_button("Update Company"):
                errors = validate_company(edit_name)
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    success, error = update_company(
                        sel_id, edit_name, edit_industry, edit_location, edit_website
                    )
                    if success:
                        st.success("Company updated successfully.")
                        st.rerun()
                    else:
                        st.error(f"Error updating company: {error}")
else:
    st.info("No companies available to edit.")

# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

st.markdown("### Delete Company")

if companies:
    delete_options = {f"{c['name']} (ID: {c['id']})": c["id"] for c in companies}

    delete_label = st.selectbox(
        "Choose a company to delete",
        options=["Select a company to delete"] + list(delete_options.keys()),
        key="delete_company_select",
    )

    if delete_label != "Select a company to delete":
        delete_id = delete_options[delete_label]
        confirmed = st.checkbox(
            "I understand this will also delete all related contacts and applications."
        )

        if st.button("Delete Company", type="primary"):
            if not confirmed:
                st.warning("Please confirm deletion before continuing.")
            else:
                success, error = delete_company(delete_id)
                if success:
                    st.success("Company deleted successfully.")
                    st.rerun()
                else:
                    st.error(f"Error deleting company: {error}")
else:
    st.info("No companies available to delete.")
