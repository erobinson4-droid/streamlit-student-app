import streamlit as st
import pandas as pd
from db import (
    get_companies,
    get_contacts,
    validate_contact,
    insert_contact,
    update_contact,
    delete_contact,
)

st.set_page_config(page_title="Manage Contacts", page_icon="👤", layout="wide")

st.title("👤 Manage Contacts")
st.caption("Track recruiters and hiring managers at the companies you are targeting.")

search_term = st.text_input(
    "Search by contact name or company",
    placeholder="Type a name or company...",
)

companies = get_companies()
contacts  = get_contacts(search_term)
contacts_df = pd.DataFrame(contacts)

valid_company_ids = [c["id"] for c in companies]
company_options   = {c["name"]: c["id"] for c in companies}

# ---------------------------------------------------------------------------
# Add
# ---------------------------------------------------------------------------

with st.expander("Add New Contact", expanded=True):
    if not companies:
        st.warning("Add at least one company before adding a contact.")
    else:
        with st.form("add_contact_form", clear_on_submit=True):
            st.markdown("### New Contact")

            col1, col2 = st.columns(2)

            with col1:
                selected_company_label = st.selectbox(
                    "Company *", options=list(company_options.keys())
                )
                contact_name = st.text_input("Full Name *")
                contact_role = st.text_input("Role", placeholder="e.g. Recruiter")

            with col2:
                contact_email = st.text_input("Email")
                contact_phone = st.text_input("Phone")
                contact_notes = st.text_area("Notes")

            if st.form_submit_button("Add Contact"):
                company_id = company_options[selected_company_label]
                errors = validate_contact(contact_name, company_id, valid_company_ids)
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    success, error = insert_contact(
                        company_id, contact_name, contact_email,
                        contact_phone, contact_role, contact_notes,
                    )
                    if success:
                        st.success("Contact added successfully.")
                        st.rerun()
                    else:
                        st.error(f"Error adding contact: {error}")

# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

st.subheader("Contacts")

if not contacts_df.empty:
    st.dataframe(contacts_df, use_container_width=True, hide_index=True)
else:
    if search_term.strip():
        st.info("No contacts matched your search.")
    else:
        st.info("No contacts found. Add one above.")

# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------

st.markdown("### Edit Contact")

if contacts and companies:
    contact_options = {
        f"{c['name']} — {c['company_name']} (ID: {c['id']})": c["id"]
        for c in contacts
    }

    selected_label = st.selectbox(
        "Choose a contact to edit",
        options=["Select a contact"] + list(contact_options.keys()),
    )

    if selected_label != "Select a contact":
        sel_id      = contact_options[selected_label]
        sel_contact = next(c for c in contacts if c["id"] == sel_id)

        with st.form("edit_contact_form"):
            col1, col2 = st.columns(2)

            with col1:
                edit_company_label = st.selectbox(
                    "Company *",
                    options=list(company_options.keys()),
                    index=list(company_options.keys()).index(sel_contact["company_name"])
                    if sel_contact["company_name"] in company_options else 0,
                )
                edit_name = st.text_input("Full Name *", value=sel_contact["name"])
                edit_role = st.text_input("Role",        value=sel_contact["role"] or "")

            with col2:
                edit_email = st.text_input("Email", value=sel_contact["email"] or "")
                edit_phone = st.text_input("Phone", value=sel_contact["phone"] or "")
                edit_notes = st.text_area("Notes", value=sel_contact["notes"] or "")

            if st.form_submit_button("Update Contact"):
                edit_company_id = company_options[edit_company_label]
                errors = validate_contact(edit_name, edit_company_id, valid_company_ids)
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    success, error = update_contact(
                        sel_id, edit_company_id, edit_name,
                        edit_email, edit_phone, edit_role, edit_notes,
                    )
                    if success:
                        st.success("Contact updated successfully.")
                        st.rerun()
                    else:
                        st.error(f"Error updating contact: {error}")
else:
    st.info("Add companies and contacts before editing.")

# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

st.markdown("### Delete Contact")

if contacts:
    delete_options = {
        f"{c['name']} — {c['company_name']} (ID: {c['id']})": c["id"]
        for c in contacts
    }

    delete_label = st.selectbox(
        "Choose a contact to delete",
        options=["Select a contact to delete"] + list(delete_options.keys()),
        key="delete_contact_select",
    )

    if delete_label != "Select a contact to delete":
        delete_id = delete_options[delete_label]
        confirmed = st.checkbox("I confirm I want to permanently delete this contact.")

        if st.button("Delete Contact", type="primary"):
            if not confirmed:
                st.warning("Please confirm deletion before continuing.")
            else:
                success, error = delete_contact(delete_id)
                if success:
                    st.success("Contact deleted successfully.")
                    st.rerun()
                else:
                    st.error(f"Error deleting contact: {error}")
else:
    st.info("No contacts available to delete.")
