import streamlit as st
import psycopg2
from psycopg2.errors import UniqueViolation

st.set_page_config(page_title="Add Course")
st.title("Add Course")


def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])


with st.form("add_course_form"):
    name = st.text_input("Course Name")
    submitted = st.form_submit_button("Add Course")

if submitted:
    if not name.strip():
        st.error("Course name is required.")
    else:
        try:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO courses10 (name) VALUES (%s)",
                    (name.strip(),),
                )
            conn.commit()
            conn.close()
            st.success(f"Course '{name.strip()}' added successfully.")
        except UniqueViolation:
            st.error("A course with that name already exists.")
        except Exception as e:
            st.error(f"Error: {e}")

st.subheader("Current Courses")
try:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM courses10 ORDER BY name")
        rows = cur.fetchall()
    conn.close()

    if rows:
        st.table([{"ID": r[0], "Course": r[1]} for r in rows])
    else:
        st.info("No courses yet.")
except Exception as e:
    st.error(f"Error loading courses: {e}")
