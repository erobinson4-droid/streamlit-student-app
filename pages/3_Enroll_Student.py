import streamlit as st
import psycopg2

st.set_page_config(page_title="Enroll Student", page_icon="📝")

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("📝 Enroll a Student in a Course")

try:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM students10 ORDER BY name;")
    students = cur.fetchall()

    cur.execute("SELECT id, course_name FROM courses10 ORDER BY course_name;")
    courses = cur.fetchall()

    cur.close()
    conn.close()

    if not students:
        st.warning("No students found. Please add a student first.")
    elif not courses:
        st.warning("No courses found. Please add a course first.")
    else:
        student_options = {s[1]: s[0] for s in students}
        course_options = {c[1]: c[0] for c in courses}

        with st.form("enroll_form"):
            selected_student = st.selectbox("Select Student", options=student_options.keys())
            selected_course = st.selectbox("Select Course", options=course_options.keys())
            submitted = st.form_submit_button("Enroll")

            if submitted:
                student_id = student_options[selected_student]
                course_id = course_options[selected_course]
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO student_courses10 (student_id, course_id) VALUES (%s, %s);",
                        (student_id, course_id)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success(f"✅ '{selected_student}' enrolled in '{selected_course}'!")
                except psycopg2.errors.UniqueViolation:
                    st.error("⚠️ This student is already enrolled in that course.")
                except Exception as e:
                    st.error(f"Error: {e}")

except Exception as e:
    st.error(f"Error: {e}")
