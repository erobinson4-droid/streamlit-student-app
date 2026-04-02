import streamlit as st
import psycopg2

st.set_page_config(page_title="Student Enrollment", layout="wide")
st.title("Student Enrollment Dashboard")


def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])


def init_db(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students10 (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS courses10 (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS student_courses10 (
                student_id INTEGER REFERENCES students10(id),
                course_id INTEGER REFERENCES courses10(id),
                PRIMARY KEY (student_id, course_id)
            )
        """)
        conn.commit()


try:
    conn = get_connection()
    init_db(conn)

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM students10")
        student_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM courses10")
        course_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM student_courses10")
        enrollment_count = cur.fetchone()[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Students", student_count)
    col2.metric("Courses", course_count)
    col3.metric("Enrollments", enrollment_count)

    st.subheader("All Enrollments")
    with conn.cursor() as cur:
        cur.execute("""
            SELECT s.name AS student, c.name AS course
            FROM student_courses10 sc
            JOIN students10 s ON sc.student_id = s.id
            JOIN courses10 c ON sc.course_id = c.id
            ORDER BY s.name, c.name
        """)
        rows = cur.fetchall()

    if rows:
        st.table([{"Student": r[0], "Course": r[1]} for r in rows])
    else:
        st.info("No enrollments yet.")

    conn.close()

except Exception as e:
    st.error(f"Database connection error: {e}")
