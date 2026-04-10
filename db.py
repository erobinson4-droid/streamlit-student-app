"""
db.py — Database layer for the Job Tracker app.

All database access goes through this file.
Tables are created automatically on first run, so the app works on a
fresh Streamlit Cloud deployment without any manual setup.

Tables
------
companies           — organisations you are applying to
contacts            — people at those companies (recruiters, hiring managers)
applications        — each role you have applied for
application_contacts — junction table linking applications ↔ contacts (many-to-many)
"""

import psycopg2
import streamlit as st


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def get_connection():
    """Return a new psycopg2 connection using the URL in st.secrets."""
    return psycopg2.connect(st.secrets["DB_URL"])


# ---------------------------------------------------------------------------
# Schema bootstrap  (call this once at app start-up)
# ---------------------------------------------------------------------------

def init_db():
    """
    Create all tables if they do not already exist, and add any columns that
    were introduced after the initial deployment.

    Uses CREATE TABLE IF NOT EXISTS + ALTER TABLE ADD COLUMN IF NOT EXISTS so
    it is always safe to call on startup — existing data is never touched.
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        # -- companies -------------------------------------------------------
        cur.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id          SERIAL PRIMARY KEY,
                name        VARCHAR(150) NOT NULL UNIQUE,
                industry    VARCHAR(100),
                location    VARCHAR(100),
                website     VARCHAR(255),
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Patch: add website if the table already existed without it
        cur.execute("""
            ALTER TABLE companies
                ADD COLUMN IF NOT EXISTS website VARCHAR(255);
        """)

        # -- contacts --------------------------------------------------------
        # One company can have many contacts (recruiters, hiring managers, etc.)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id          SERIAL PRIMARY KEY,
                company_id  INTEGER NOT NULL
                                REFERENCES companies(id) ON DELETE CASCADE,
                name        VARCHAR(150) NOT NULL,
                email       VARCHAR(150),
                phone       VARCHAR(30),
                role        VARCHAR(100),   -- e.g. "Recruiter", "Engineering Manager"
                notes       TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # -- applications ----------------------------------------------------
        # One company can have many applications (you applied for multiple roles).
        cur.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id            SERIAL PRIMARY KEY,
                company_id    INTEGER NOT NULL
                                  REFERENCES companies(id) ON DELETE CASCADE,
                job_title     VARCHAR(150) NOT NULL,
                status        VARCHAR(50)  NOT NULL DEFAULT 'Applied',
                applied_date  DATE         NOT NULL DEFAULT CURRENT_DATE,
                salary_range  VARCHAR(100),
                posting_url   TEXT,
                notes         TEXT,
                last_updated  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Patch: add columns introduced after the initial deployment.
        # ADD COLUMN IF NOT EXISTS is a no-op when the column already exists.
        cur.execute("""
            ALTER TABLE applications
                ADD COLUMN IF NOT EXISTS company_id   INTEGER REFERENCES companies(id) ON DELETE CASCADE,
                ADD COLUMN IF NOT EXISTS job_title    VARCHAR(150),
                ADD COLUMN IF NOT EXISTS status       VARCHAR(50) DEFAULT 'Applied',
                ADD COLUMN IF NOT EXISTS salary_range VARCHAR(100),
                ADD COLUMN IF NOT EXISTS posting_url  TEXT;
        """)

        # -- jobs ------------------------------------------------------------
        # One company can have many job postings.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          SERIAL PRIMARY KEY,
                company_id  INTEGER REFERENCES companies(id) ON DELETE CASCADE,
                title       VARCHAR(150) NOT NULL,
                salary      INTEGER,
                job_type    VARCHAR(50),
                posting_url TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # -- application_contacts (many-to-many junction) --------------------
        # One application can involve multiple contacts, and one contact can
        # appear on multiple applications (e.g. the same recruiter handles
        # several of your applications at the same company).
        cur.execute("""
            CREATE TABLE IF NOT EXISTS application_contacts (
                application_id  INTEGER NOT NULL
                                    REFERENCES applications(id) ON DELETE CASCADE,
                contact_id      INTEGER NOT NULL
                                    REFERENCES contacts(id)     ON DELETE CASCADE,
                PRIMARY KEY (application_id, contact_id)
            );
        """)

        conn.commit()
        cur.close()
    except Exception as e:
        st.error(f"Database initialisation failed: {e}")
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def get_dashboard_metrics():
    """
    Return summary counts for the home page dashboard.

    Returns a dict with zero values if anything goes wrong, so the UI
    never crashes just because the database is empty or unavailable.
    """
    defaults = {
        "total_companies": 0,
        "total_contacts": 0,
        "total_applications": 0,
        "status_counts": [],
        "recent_applications": [],
    }

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM companies;")
        defaults["total_companies"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM contacts;")
        defaults["total_contacts"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM applications;")
        defaults["total_applications"] = cur.fetchone()[0]

        # How many applications in each status bucket?
        cur.execute("""
            SELECT status, COUNT(*) AS total
            FROM applications
            GROUP BY status
            ORDER BY total DESC;
        """)
        defaults["status_counts"] = cur.fetchall()

        # Five most-recently submitted applications
        cur.execute("""
            SELECT a.job_title, c.name AS company, a.status, a.applied_date
            FROM   applications a
            JOIN   companies    c ON a.company_id = c.id
            ORDER  BY a.applied_date DESC
            LIMIT  5;
        """)
        defaults["recent_applications"] = cur.fetchall()

        cur.close()
    except Exception as e:
        st.error(f"Could not load dashboard data: {e}")
    finally:
        if conn:
            conn.close()

    return defaults


# ---------------------------------------------------------------------------
# Companies — CRUD
# ---------------------------------------------------------------------------

def get_companies(search_term=""):
    """Return all companies, optionally filtered by name (case-insensitive)."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        if search_term.strip():
            cur.execute("""
                SELECT id, name, industry, location, website, created_at
                FROM   companies
                WHERE  name ILIKE %s
                ORDER  BY name;
            """, (f"%{search_term.strip()}%",))
        else:
            cur.execute("""
                SELECT id, name, industry, location, website, created_at
                FROM   companies
                ORDER  BY name;
            """)

        rows = cur.fetchall()
        cur.close()
        return [
            {
                "id":         r[0],
                "name":       r[1],
                "industry":   r[2],
                "location":   r[3],
                "website":    r[4],
                "created_at": r[5],
            }
            for r in rows
        ]
    except Exception as e:
        st.error(f"Could not load companies: {e}")
        return []
    finally:
        if conn:
            conn.close()


def insert_company(name, industry, location, website):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO companies (name, industry, location, website)
            VALUES (%s, %s, %s, %s);
        """, (
            name.strip(),
            industry.strip() or None,
            location.strip() or None,
            website.strip()  or None,
        ))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def update_company(company_id, name, industry, location, website):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE companies
            SET    name = %s, industry = %s, location = %s, website = %s
            WHERE  id = %s;
        """, (
            name.strip(),
            industry.strip() or None,
            location.strip() or None,
            website.strip()  or None,
            company_id,
        ))
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
# Jobs — CRUD
# ---------------------------------------------------------------------------

JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship", "Freelance"]


def get_jobs(search_term=""):
    """Return all jobs with company name, optionally filtered by title or company."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        if search_term.strip():
            cur.execute("""
                SELECT j.id, j.company_id, c.name AS company_name,
                       j.title, j.salary, j.job_type, j.posting_url, j.created_at
                FROM   jobs j
                JOIN   companies c ON j.company_id = c.id
                WHERE  j.title ILIKE %s OR c.name ILIKE %s
                ORDER  BY c.name, j.title;
            """, (f"%{search_term.strip()}%", f"%{search_term.strip()}%"))
        else:
            cur.execute("""
                SELECT j.id, j.company_id, c.name AS company_name,
                       j.title, j.salary, j.job_type, j.posting_url, j.created_at
                FROM   jobs j
                JOIN   companies c ON j.company_id = c.id
                ORDER  BY c.name, j.title;
            """)

        rows = cur.fetchall()
        cur.close()
        return [
            {
                "id":           r[0],
                "company_id":   r[1],
                "company_name": r[2],
                "title":        r[3],
                "salary":       r[4],
                "job_type":     r[5],
                "posting_url":  r[6],
                "created_at":   r[7],
            }
            for r in rows
        ]
    except Exception as e:
        st.error(f"Could not load jobs: {e}")
        return []
    finally:
        if conn:
            conn.close()


def validate_job(title, company_id, valid_company_ids):
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
        cur.execute("""
            INSERT INTO jobs (company_id, title, salary, job_type, posting_url)
            VALUES (%s, %s, %s, %s, %s);
        """, (
            company_id,
            title.strip(),
            salary if salary else None,
            job_type or None,
            posting_url.strip() or None,
        ))
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
        cur.execute("""
            UPDATE jobs
            SET    company_id = %s, title = %s, salary = %s,
                   job_type = %s, posting_url = %s
            WHERE  id = %s;
        """, (
            company_id,
            title.strip(),
            salary if salary else None,
            job_type or None,
            posting_url.strip() or None,
            job_id,
        ))
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
# Contacts — CRUD
# ---------------------------------------------------------------------------

def get_contacts(search_term=""):
    """Return all contacts with their company name, optionally filtered."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        if search_term.strip():
            cur.execute("""
                SELECT ct.id, ct.company_id, co.name AS company_name,
                       ct.name, ct.email, ct.phone, ct.role, ct.notes, ct.created_at
                FROM   contacts ct
                JOIN   companies co ON ct.company_id = co.id
                WHERE  ct.name ILIKE %s OR co.name ILIKE %s
                ORDER  BY co.name, ct.name;
            """, (f"%{search_term.strip()}%", f"%{search_term.strip()}%"))
        else:
            cur.execute("""
                SELECT ct.id, ct.company_id, co.name AS company_name,
                       ct.name, ct.email, ct.phone, ct.role, ct.notes, ct.created_at
                FROM   contacts ct
                JOIN   companies co ON ct.company_id = co.id
                ORDER  BY co.name, ct.name;
            """)

        rows = cur.fetchall()
        cur.close()
        return [
            {
                "id":           r[0],
                "company_id":   r[1],
                "company_name": r[2],
                "name":         r[3],
                "email":        r[4],
                "phone":        r[5],
                "role":         r[6],
                "notes":        r[7],
                "created_at":   r[8],
            }
            for r in rows
        ]
    except Exception as e:
        st.error(f"Could not load contacts: {e}")
        return []
    finally:
        if conn:
            conn.close()


def insert_contact(company_id, name, email, phone, role, notes):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO contacts (company_id, name, email, phone, role, notes)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (
            company_id,
            name.strip(),
            email.strip() or None,
            phone.strip() or None,
            role.strip()  or None,
            notes.strip() or None,
        ))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def update_contact(contact_id, company_id, name, email, phone, role, notes):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE contacts
            SET    company_id = %s, name = %s, email = %s,
                   phone = %s, role = %s, notes = %s
            WHERE  id = %s;
        """, (
            company_id,
            name.strip(),
            email.strip() or None,
            phone.strip() or None,
            role.strip()  or None,
            notes.strip() or None,
            contact_id,
        ))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def delete_contact(contact_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM contacts WHERE id = %s;", (contact_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Applications — CRUD
# ---------------------------------------------------------------------------

# Valid status values shown in dropdowns
APPLICATION_STATUSES = [
    "Applied",
    "Phone Screen",
    "Interview",
    "Take-home / Assessment",
    "Final Round",
    "Offer",
    "Rejected",
    "Withdrawn",
]


def get_applications(search_term=""):
    """Return all applications with company name, optionally filtered."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        if search_term.strip():
            cur.execute("""
                SELECT a.id, a.company_id, c.name AS company_name,
                       a.job_title, a.status, a.applied_date,
                       a.salary_range, a.posting_url, a.notes, a.last_updated
                FROM   applications a
                JOIN   companies    c ON a.company_id = c.id
                WHERE  a.job_title ILIKE %s OR c.name ILIKE %s
                ORDER  BY a.applied_date DESC;
            """, (f"%{search_term.strip()}%", f"%{search_term.strip()}%"))
        else:
            cur.execute("""
                SELECT a.id, a.company_id, c.name AS company_name,
                       a.job_title, a.status, a.applied_date,
                       a.salary_range, a.posting_url, a.notes, a.last_updated
                FROM   applications a
                JOIN   companies    c ON a.company_id = c.id
                ORDER  BY a.applied_date DESC;
            """)

        rows = cur.fetchall()
        cur.close()
        return [
            {
                "id":           r[0],
                "company_id":   r[1],
                "company_name": r[2],
                "job_title":    r[3],
                "status":       r[4],
                "applied_date": r[5],
                "salary_range": r[6],
                "posting_url":  r[7],
                "notes":        r[8],
                "last_updated": r[9],
            }
            for r in rows
        ]
    except Exception as e:
        st.error(f"Could not load applications: {e}")
        return []
    finally:
        if conn:
            conn.close()


def insert_application(company_id, job_title, status, applied_date,
                       salary_range, posting_url, notes):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO applications
                (company_id, job_title, status, applied_date,
                 salary_range, posting_url, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (
            company_id,
            job_title.strip(),
            status,
            applied_date,
            salary_range.strip() or None,
            posting_url.strip()  or None,
            notes.strip()        or None,
        ))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


def update_application(application_id, company_id, job_title, status,
                       applied_date, salary_range, posting_url, notes):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE applications
            SET    company_id = %s, job_title = %s, status = %s,
                   applied_date = %s, salary_range = %s,
                   posting_url = %s, notes = %s
            WHERE  id = %s;
        """, (
            company_id,
            job_title.strip(),
            status,
            applied_date,
            salary_range.strip() or None,
            posting_url.strip()  or None,
            notes.strip()        or None,
            application_id,
        ))
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


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_company(name):
    errors = []
    if not name.strip():
        errors.append("**Company Name** is required.")
    return errors


def validate_contact(name, company_id, valid_company_ids):
    errors = []
    if not name.strip():
        errors.append("**Contact Name** is required.")
    if company_id not in valid_company_ids:
        errors.append("**Company** selection is invalid.")
    return errors


def validate_application(job_title, company_id, valid_company_ids, applied_date):
    errors = []
    if not job_title.strip():
        errors.append("**Job Title** is required.")
    if company_id not in valid_company_ids:
        errors.append("**Company** selection is invalid.")
    if applied_date is None:
        errors.append("**Applied Date** is required.")
    return errors
