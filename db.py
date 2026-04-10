import psycopg2
import streamlit as st


def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def get_dashboard_metrics():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM companies;")
    total_companies = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM jobs;")
    total_jobs = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM applications;")
    total_applications = cur.fetchone()[0]

    cur.execute("""
        SELECT s.status_name, COUNT(*)
        FROM applications a
        JOIN statuses s ON a.status_id = s.id
        GROUP BY s.status_name
    """)
    status_counts = cur.fetchall()

    cur.execute("""
        SELECT j.title, s.status_name, a.applied_date
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN statuses s ON a.status_id = s.id
        ORDER BY a.applied_date DESC
        LIMIT 5
    """)
    recent_applications = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "total_companies": total_companies,
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "status_counts": status_counts,
        "recent_applications": recent_applications,
    }


# ---------------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------------

def get_companies(search_term=""):
    conn = get_connection()
    cur = conn.cursor()
    if search_term.strip():
        cur.execute(
            """
            SELECT id, name, industry, location, created_at
            FROM companies
            WHERE name ILIKE %s
            ORDER BY name;
            """,
            (f"%{search_term.strip()}%",),
        )
    else:
        cur.execute(
            """
            SELECT id, name, industry, location, created_at
            FROM companies
            ORDER BY name;
            """
        )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "id": r[0],
            "company_name": r[1],
            "industry": r[2],
            "location": r[3],
            "created_at": r[4],
        }
        for r in rows
    ]


def validate_company_input(company_name):
    errors = []
    if not company_name.strip():
        errors.append("**Company Name** is required.")
    return errors


def insert_company(company_name, industry, location):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO companies (name, industry, location)
            VALUES (%s, %s, %s);
            """,
            (company_name.strip(), industry.strip() or None, location.strip() or None),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def update_company(company_id, company_name, industry, location):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE companies
            SET name = %s, industry = %s, location = %s
            WHERE id = %s;
            """,
            (company_name.strip(), industry.strip() or None,
             location.strip() or None, company_id),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def delete_company(company_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM companies WHERE id = %s;", (company_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

def get_jobs(search_term=""):
    conn = get_connection()
    cur = conn.cursor()
    if search_term.strip():
        cur.execute(
            """
            SELECT j.id, j.company_id, c.name AS company_name, j.title,
                   j.salary, j.job_type, j.posting_url, j.created_at
            FROM jobs j
            JOIN companies c ON j.company_id = c.id
            WHERE j.title ILIKE %s OR c.name ILIKE %s
            ORDER BY c.name, j.title;
            """,
            (f"%{search_term.strip()}%", f"%{search_term.strip()}%"),
        )
    else:
        cur.execute(
            """
            SELECT j.id, j.company_id, c.name AS company_name, j.title,
                   j.salary, j.job_type, j.posting_url, j.created_at
            FROM jobs j
            JOIN companies c ON j.company_id = c.id
            ORDER BY c.name, j.title;
            """
        )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "id": r[0],
            "company_id": r[1],
            "company_name": r[2],
            "title": r[3],
            "salary": r[4],
            "job_type": r[5],
            "posting_url": r[6],
            "created_at": r[7],
        }
        for r in rows
    ]


def validate_job_input(title, company_id, valid_company_ids):
    errors = []
    if not title.strip():
        errors.append("**Job Title** is required.")
    if company_id not in valid_company_ids:
        errors.append("**Company** selection is invalid.")
    return errors


def insert_job(company_id, title, salary, job_type, posting_url):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO jobs (company_id, title, salary, job_type, posting_url)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (company_id, title.strip(), salary or None,
             job_type.strip() or None, posting_url.strip() or None),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def update_job(job_id, company_id, title, salary, job_type, posting_url):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE jobs
            SET company_id = %s, title = %s, salary = %s,
                job_type = %s, posting_url = %s
            WHERE id = %s;
            """,
            (company_id, title.strip(), salary or None,
             job_type.strip() or None, posting_url.strip() or None, job_id),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def delete_job(job_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM jobs WHERE id = %s;", (job_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Statuses
# ---------------------------------------------------------------------------

def get_statuses():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, status_name FROM statuses ORDER BY status_name;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "status_name": r[1]} for r in rows]


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

def get_applications(search_term=""):
    conn = get_connection()
    cur = conn.cursor()
    if search_term.strip():
        cur.execute(
            """
            SELECT a.id, a.job_id, a.status_id, a.applied_date, a.notes,
                   c.name AS company_name, j.title AS job_title, s.status_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            JOIN statuses s ON a.status_id = s.id
            WHERE c.name ILIKE %s OR j.title ILIKE %s
            ORDER BY a.applied_date DESC;
            """,
            (f"%{search_term.strip()}%", f"%{search_term.strip()}%"),
        )
    else:
        cur.execute(
            """
            SELECT a.id, a.job_id, a.status_id, a.applied_date, a.notes,
                   c.name AS company_name, j.title AS job_title, s.status_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            JOIN companies c ON j.company_id = c.id
            JOIN statuses s ON a.status_id = s.id
            ORDER BY a.applied_date DESC;
            """
        )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "id": r[0],
            "job_id": r[1],
            "status_id": r[2],
            "applied_date": r[3],
            "notes": r[4],
            "company_name": r[5],
            "job_title": r[6],
            "status_name": r[7],
        }
        for r in rows
    ]


def validate_application_input(job_id, status_id, applied_date, valid_job_ids, valid_status_ids):
    errors = []
    if job_id not in valid_job_ids:
        errors.append("**Job** selection is invalid.")
    if status_id not in valid_status_ids:
        errors.append("**Status** selection is invalid.")
    if applied_date is None:
        errors.append("**Applied Date** is required.")
    return errors


def insert_application(job_id, status_id, applied_date, notes):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO applications (job_id, status_id, applied_date, notes)
            VALUES (%s, %s, %s, %s);
            """,
            (job_id, status_id, applied_date, notes.strip() or None),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def update_application(application_id, job_id, status_id, applied_date, notes):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE applications
            SET job_id = %s, status_id = %s, applied_date = %s, notes = %s
            WHERE id = %s;
            """,
            (job_id, status_id, applied_date, notes.strip() or None, application_id),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def delete_application(application_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM applications WHERE id = %s;", (application_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)
