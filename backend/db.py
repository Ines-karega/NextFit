"""Data access layer (SRS Appendix B.4): the only file that talks to the database.

On your computer the data is kept in a SQLite file (nextfit.db).
On the live site, set DATABASE_URL and the same code uses PostgreSQL instead,
because free hosting deletes local files every time the site restarts.
The questions (SQL) are the same for both.
"""
import os
import sqlite3
from datetime import date, timedelta

from flask import g, has_app_context
from werkzeug.security import generate_password_hash

# The SQLite file is kept in the main project folder (one level above backend).
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.environ.get("NEXTFIT_DB", os.path.join(PROJECT_FOLDER, "nextfit.db"))

# The address of the PostgreSQL database. Only set on the live site.
DATABASE_URL = os.environ.get("DATABASE_URL", "")
ON_LIVE_SITE = DATABASE_URL != ""

# Vercel (the hosting company) cannot keep a SQLite file, so stop with a clear message
# instead of failing later in a confusing way. Vercel sets VERCEL=1 by itself.
if os.environ.get("VERCEL") and not ON_LIVE_SITE:
    raise RuntimeError("Set DATABASE_URL (the PostgreSQL address from Neon) in the Vercel project settings.")

if ON_LIVE_SITE:
    import psycopg
    from psycopg.rows import dict_row
    DuplicateError = psycopg.errors.UniqueViolation   # e.g. the email is already used
else:
    DuplicateError = sqlite3.IntegrityError

TABLES = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL            -- 'SEEKER' or 'ADMIN'
);
CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY,
    age INTEGER, province TEXT, district TEXT,
    education TEXT, status TEXT, skills TEXT
);
CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT, description TEXT, type TEXT, required_skills TEXT,
    province TEXT, district TEXT, work_mode TEXT, deadline TEXT,
    apply_link TEXT, min_age INTEGER, max_age INTEGER,
    education TEXT,               -- accepted levels, e.g. 'TVET,BACHELORS'
    status TEXT DEFAULT 'OPEN',   -- 'OPEN' or 'CLOSED'
    added_by INTEGER              -- the id of the admin who added it
);
CREATE TABLE IF NOT EXISTS saved (
    user_id INTEGER, opportunity_id INTEGER,
    PRIMARY KEY (user_id, opportunity_id)
);
CREATE TABLE IF NOT EXISTS reset_tokens (
    token TEXT PRIMARY KEY, user_id INTEGER,
    expires TEXT                  -- the link works for 1 hour
);
"""

# The opportunity columns, in the order the admin form sends them.
OPPORTUNITY_COLUMNS = ("title, description, type, required_skills, province, district, "
                       "work_mode, deadline, apply_link, min_age, max_age, education")


# ---------------- opening and closing the database ----------------
class Connection:
    """A small wrapper so the rest of this file works the same with SQLite and PostgreSQL.
    Rows can be used like dictionaries: row['title']."""

    def __init__(self):
        if ON_LIVE_SITE:
            self.raw = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        else:
            self.raw = sqlite3.connect(DB_FILE)
            self.raw.row_factory = sqlite3.Row

    def execute(self, sql, values=()):
        if ON_LIVE_SITE:
            sql = sql.replace("?", "%s")   # PostgreSQL writes its placeholders as %s
        try:
            return self.raw.execute(sql, values)
        except Exception:
            self.raw.rollback()            # leave the connection usable after a mistake
            raise

    def run_script(self, script):
        """Run several statements at once (used to create the tables)."""
        if ON_LIVE_SITE:
            self.raw.execute(script.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY"))
        else:
            self.raw.executescript(script)

    def add_column_if_missing(self, table, column, kind):
        """Add a column to a table made by an older version of NextFit."""
        if ON_LIVE_SITE:
            self.raw.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {kind}")
        else:
            existing = [row["name"] for row in self.raw.execute(f"PRAGMA table_info({table})")]
            if column not in existing:
                self.raw.execute(f"ALTER TABLE {table} ADD COLUMN {column} {kind}")

    def commit(self):
        self.raw.commit()

    def close(self):
        self.raw.close()


def connect():
    """The connection for the page being built. It is opened the first time it is
    needed and closed by close_connection() when the page is finished."""
    if not has_app_context():
        return Connection()   # outside a page request (e.g. when the server starts)
    if "db" not in g:
        g.db = Connection()
    return g.db


def close_connection(error=None):
    """app.py asks Flask to call this at the end of every page request."""
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def setup():
    """Create the tables, the first admin account, and the starting data."""
    conn = Connection()
    if ON_LIVE_SITE:
        # If two copies of the server start together, the second one waits here for the first.
        conn.execute("SELECT pg_advisory_xact_lock(20260917)")
    conn.run_script(TABLES)
    conn.add_column_if_missing("opportunities", "added_by", "INTEGER")

    # The first admin is created here, once (SRS FR1.1).
    admin = conn.execute("SELECT id FROM users WHERE role = 'ADMIN'").fetchone()
    if admin is None:
        email = os.environ.get("ADMIN_EMAIL", "admin@nextfit.rw")
        # The name shown in the menu greeting and in the "Added by" column of the admin's list.
        admin_name = os.environ.get("ADMIN_NAME", "").strip() or "NextFit Admin"
        password = os.environ.get("ADMIN_PASSWORD", "")
        if password == "":
            if ON_LIVE_SITE:
                raise RuntimeError("Set ADMIN_EMAIL and ADMIN_PASSWORD before starting the live site.")
            password = "Admin123!"   # demo password, only ever used on your own computer
        conn.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'ADMIN')",
                     (admin_name, email.strip().lower(), generate_password_hash(password)))

    if os.environ.get("NEXTFIT_SEED", "1") == "1":
        import seed
        # The starting listings were prepared by the admin, so they are recorded under the first admin account.
        first_admin = conn.execute("SELECT id FROM users WHERE role = 'ADMIN' ORDER BY id").fetchone()
        seed.add_starting_data(conn, added_by=first_admin["id"], with_samples=not ON_LIVE_SITE)

    conn.commit()
    conn.close()


# ---------------- users (FR1, FR10.1) ----------------
def get_user(user_id):
    return connect().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_by_email(email):
    return connect().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def add_user(name, email, password_hash, role):
    """Returns the new user's id. Raises DuplicateError if the email is already used."""
    conn = connect()
    row = conn.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?) RETURNING id",
                       (name, email, password_hash, role)).fetchone()
    conn.commit()
    return row["id"]


def set_password(user_id, password_hash):
    conn = connect()
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    conn.commit()


def get_all_users():
    return connect().execute("SELECT id, name, email, role FROM users ORDER BY role, name").fetchall()


def count_seekers():
    return connect().execute("SELECT COUNT(*) AS n FROM users WHERE role = 'SEEKER'").fetchone()["n"]


def delete_user(user_id):
    """Remove an account and everything that belongs to it."""
    conn = connect()
    conn.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM saved WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM reset_tokens WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()


# ---------------- password reset links (FR1.3) ----------------
def add_reset_token(token, user_id, expires):
    conn = connect()
    conn.execute("INSERT INTO reset_tokens (token, user_id, expires) VALUES (?, ?, ?)", (token, user_id, expires))
    conn.commit()


def get_reset_token(token):
    return connect().execute("SELECT * FROM reset_tokens WHERE token = ?", (token,)).fetchone()


def delete_reset_tokens(user_id):
    """Once a password is changed, every reset link for that account stops working."""
    conn = connect()
    conn.execute("DELETE FROM reset_tokens WHERE user_id = ?", (user_id,))
    conn.commit()


# ---------------- seeker profiles (FR2) ----------------
def get_profile(user_id):
    return connect().execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()


def save_profile(user_id, age, province, district, education, status, skills):
    """Create the profile, or replace it if the seeker already has one."""
    conn = connect()
    conn.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
    conn.execute("INSERT INTO profiles (user_id, age, province, district, education, status, skills) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (user_id, age, province, district, education, status, skills))
    conn.commit()


# ---------------- opportunities (FR3, FR10.2) ----------------
def get_open_opportunities(today):
    """Opportunities the admin has not closed and whose deadline has not passed (FR4.2).
    today is a 'YYYY-MM-DD' text, the same form deadlines are stored in."""
    return connect().execute("SELECT * FROM opportunities WHERE status = 'OPEN' AND deadline >= ? "
                             "ORDER BY deadline", (today,)).fetchall()


def get_all_opportunities():
    """Every opportunity, for the admin's list, with the name of the admin who added it."""
    return connect().execute(
        "SELECT o.*, u.name AS added_by_name FROM opportunities o "
        "LEFT JOIN users u ON u.id = o.added_by ORDER BY o.status DESC, o.deadline").fetchall()


def get_opportunity(opp_id):
    return connect().execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()


def count_opportunities(status):
    return connect().execute("SELECT COUNT(*) AS n FROM opportunities WHERE status = ?", (status,)).fetchone()["n"]


def add_opportunity(values, admin_id):
    """values: the 12 fields in the order of OPPORTUNITY_COLUMNS.
    admin_id: the admin who is adding it, so the admin's list can show who added what."""
    conn = connect()
    conn.execute(f"INSERT INTO opportunities ({OPPORTUNITY_COLUMNS}, added_by) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                 tuple(values) + (admin_id,))
    conn.commit()


def update_opportunity(opp_id, values):
    conn = connect()
    conn.execute(f"UPDATE opportunities SET ({OPPORTUNITY_COLUMNS}) = (?,?,?,?,?,?,?,?,?,?,?,?) WHERE id = ?",
                 tuple(values) + (opp_id,))
    conn.commit()


def close_opportunity(opp_id):
    conn = connect()
    conn.execute("UPDATE opportunities SET status = 'CLOSED' WHERE id = ?", (opp_id,))
    conn.commit()


def delete_opportunity(opp_id):
    conn = connect()
    conn.execute("DELETE FROM opportunities WHERE id = ?", (opp_id,))
    conn.execute("DELETE FROM saved WHERE opportunity_id = ?", (opp_id,))
    conn.commit()


# ---------------- saved opportunities and reminders (FR7, FR8) ----------------
def get_saved_ids(user_id):
    rows = connect().execute("SELECT opportunity_id FROM saved WHERE user_id = ?", (user_id,)).fetchall()
    return [row["opportunity_id"] for row in rows]


def get_saved_opportunities(user_id):
    """Everything on the seeker's shortlist, including ones that have since closed."""
    return connect().execute(
        "SELECT o.* FROM opportunities o JOIN saved s ON s.opportunity_id = o.id "
        "WHERE s.user_id = ? ORDER BY o.deadline", (user_id,)).fetchall()


def get_due_saved_items(user_id, days=14):
    """FR8.1: saved opportunities that are still open and close in 14 days or less."""
    today = date.today()
    return connect().execute(
        "SELECT o.* FROM opportunities o JOIN saved s ON s.opportunity_id = o.id "
        "WHERE s.user_id = ? AND o.status = 'OPEN' AND o.deadline >= ? AND o.deadline <= ? "
        "ORDER BY o.deadline",
        (user_id, today.isoformat(), (today + timedelta(days=days)).isoformat())).fetchall()


def save_opportunity(user_id, opp_id):
    conn = connect()
    conn.execute("INSERT INTO saved (user_id, opportunity_id) VALUES (?, ?) ON CONFLICT DO NOTHING",
                 (user_id, opp_id))
    conn.commit()


def remove_saved(user_id, opp_id):
    conn = connect()
    conn.execute("DELETE FROM saved WHERE user_id = ? AND opportunity_id = ?", (user_id, opp_id))
    conn.commit()
