import re
import streamlit as st
import psycopg2
from psycopg2.errors import UniqueViolation

st.set_page_config(page_title="Add Student")
st.title("Add Student")

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])


with st.form("add_student_form"):
    name = st.text_input("Student Name")
    email = st.text_input("Email")
    submitted = st.form_submit_button("Add Student")

if submitted:
    if not name.strip():
        st.error("Name is required.")
    elif not EMAIL_REGEX.match(email.strip()):
        st.error("Please enter a valid email address.")
    else:
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO students10 (name, email) VALUES (%s, %s)",
                    (name.strip(), email.strip()),
                )
            conn.commit()
            conn.close()
            st.success(f"Student '{name.strip()}' added successfully.")
        except UniqueViolation:
            st.error("A student with that email already exists.")
        except Exception as e:
            st.error(f"Error: {e}")

st.subheader("Current Students")
try:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, email FROM students10 ORDER BY name")
        rows = cur.fetchall()
    conn.close()

    if rows:
        st.table([{"ID": r[0], "Name": r[1], "Email": r[2]} for r in rows])
    else:
        st.info("No students yet.")
except Exception as e:
    st.error(f"Error loading students: {e}")
