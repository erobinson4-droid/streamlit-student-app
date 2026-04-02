import streamlit as st
import psycopg2
from psycopg2.errors import UniqueViolation

st.set_page_config(page_title="Enroll Student")
st.title("Enroll Student in Course")


def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])


try:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM students10 ORDER BY name")
        students = cur.fetchall()
        cur.execute("SELECT id, name FROM courses10 ORDER BY name")
        courses = cur.fetchall()
    conn.close()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if not students:
    st.warning("No students found. Please add students first.")
    st.stop()

if not courses:
    st.warning("No courses found. Please add courses first.")
    st.stop()

student_options = {name: sid for sid, name in students}
course_options = {name: cid for cid, name in courses}

with st.form("enroll_form"):
    selected_student = st.selectbox("Select Student", list(student_options.keys()))
    selected_course = st.selectbox("Select Course", list(course_options.keys()))
    submitted = st.form_submit_button("Enroll")

if submitted:
    student_id = student_options[selected_student]
    course_id = course_options[selected_course]
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO student_courses10 (student_id, course_id) VALUES (%s, %s)",
                (student_id, course_id),
            )
        conn.commit()
        conn.close()
        st.success(f"'{selected_student}' enrolled in '{selected_course}'.")
    except UniqueViolation:
        st.error(f"'{selected_student}' is already enrolled in '{selected_course}'.")
    except Exception as e:
        st.error(f"Error: {e}")
