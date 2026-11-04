"""Database helpers (SQLite). The tables are created here."""
import os
import sqlite3

from werkzeug.security import generate_password_hash

# The database file is kept in the main project folder (one level above backend).
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.environ.get("NEXTFIT_DB", os.path.join(PROJECT_FOLDER, "nextfit.db"))

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
    status TEXT DEFAULT 'OPEN'    -- 'OPEN' or 'CLOSED'
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


def connect():
    """Open the database. Rows can be used like dictionaries: row['title']."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def setup():
    """Create tables, the first admin account, and the demo data."""
    conn = connect()
    conn.executescript(TABLES)

    # The first admin is created here, once (SRS FR1.1).
    admin = conn.execute("SELECT id FROM users WHERE role = 'ADMIN'").fetchone()
    if admin is None:
        email = os.environ.get("ADMIN_EMAIL", "admin@nextfit.rw")
        password = os.environ.get("ADMIN_PASSWORD", "Admin123!")
        conn.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'ADMIN')",
                     ("NextFit Admin", email, generate_password_hash(password)))

    if os.environ.get("NEXTFIT_SEED", "1") == "1":
        import seed
        seed.add_demo_data(conn)

    conn.commit()
    conn.close()
