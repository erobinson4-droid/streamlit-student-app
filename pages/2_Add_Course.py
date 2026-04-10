import streamlit as st
import psycopg2

st.set_page_config(page_title="Add Course", page_icon="📚")

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("📚 Add a New Course")

with st.form("add_course_form"):
    course_name = st.text_input("Course Name")
    submitted = st.form_submit_button("Add Course")

    if submitted:
        if course_name:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO courses10 (course_name) VALUES (%s);",
                    (course_name,)
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ Course '{course_name}' added successfully!")
            except psycopg2.errors.UniqueViolation:
                st.error("⚠️ A course with that name already exists.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please enter a course name.")

st.markdown("---")
st.subheader("Current Courses")

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, course_name FROM courses10 ORDER BY course_name;")
    courses = cur.fetchall()
    cur.close()
    conn.close()

    if courses:
        st.table([{"ID": c[0], "Course Name": c[1]} for c in courses])
    else:
        st.info("No courses yet.")
except Exception as e:
    st.error(f"Error: {e}")
