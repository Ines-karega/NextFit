"""Demo data so the prototype works on first run (hypothesis needs 20+ opportunities).
These are SAMPLE listings for demonstration only; an admin replaces them with real ones.
Deadlines are relative to today so the demo never goes stale."""
import csv
import os
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

ALL = "SECONDARY,TVET,BACHELORS,MASTERS,PHD"
POST = "TVET,BACHELORS,MASTERS,PHD"
UNI = "BACHELORS,MASTERS,PHD"

# title, type, skills, province, district, mode, days, min_age, max_age, education, description
OPPS = [
    ("Sample: Digital Skills Bootcamp", "TRAINING", "computer, communication", "Kigali City", "Gasabo", "ON_SITE", 6, 16, 30, ALL, "Four-week introduction to computers, email and online safety."),
    ("Sample: Web Development Training", "TRAINING", "html, css, javascript", "Kigali City", "Kicukiro", "HYBRID", 12, 18, 30, POST, "Hands-on training building simple websites."),
    ("Sample: Junior Accountant Internship", "INTERNSHIP", "excel, bookkeeping", "Kigali City", "Nyarugenge", "ON_SITE", 20, 20, 30, UNI, "Six-month internship in a finance team."),
    ("Sample: Customer Care Agent", "JOB", "communication, english", "Kigali City", "Gasabo", "ON_SITE", 9, 18, 30, "SECONDARY,TVET,BACHELORS", "Answer customer calls and messages for a local company."),
    ("Sample: Data Entry Clerk", "JOB", "typing, excel", "Kigali City", "Kicukiro", "REMOTE", 30, 18, 30, ALL, "Remote data entry for a survey project."),
    ("Sample: Solar Technician Apprenticeship", "TRAINING", "electrical, mechanics", "Southern", "Huye", "ON_SITE", 15, 18, 30, "SECONDARY,TVET", "Learn to install and maintain household solar systems."),
    ("Sample: Agribusiness Youth Program", "TRAINING", "farming", "Southern", "Muhanga", "ON_SITE", 25, 16, 30, ALL, "Practical training in modern farming and selling produce."),
    ("Sample: Primary School Teaching Assistant", "INTERNSHIP", "teaching, communication", "Southern", "Nyanza", "ON_SITE", 11, 20, 30, "TVET,BACHELORS", "Support teachers in a primary school for six months."),
    ("Sample: Hotel Front Desk Trainee", "INTERNSHIP", "english, communication", "Western", "Rubavu", "ON_SITE", 18, 18, 28, "SECONDARY,TVET,BACHELORS", "Hospitality internship at a lakeside hotel."),
    ("Sample: Tour Guide Training", "TRAINING", "english, tourism", "Western", "Rusizi", "ON_SITE", 40, 18, 30, "SECONDARY,TVET,BACHELORS", "Become a certified local guide."),
    ("Sample: Community Health Worker Assistant", "JOB", "first aid, communication", "Western", "Karongi", "ON_SITE", 13, 21, 30, "SECONDARY,TVET", "Support community health outreach."),
    ("Sample: Software Engineering Internship", "INTERNSHIP", "python, javascript, sql", "Kigali City", "Nyarugenge", "HYBRID", 5, 20, 30, UNI, "Work with a product team on real software."),
    ("Sample: Graphic Design Training", "TRAINING", "design, photoshop", "Northern", "Musanze", "ON_SITE", 22, 16, 30, ALL, "Learn design tools and build a portfolio."),
    ("Sample: Mobile Money Agent Program", "JOB", "mathematics, communication", "Northern", "Gicumbi", "ON_SITE", 28, 18, 30, "SECONDARY,TVET,BACHELORS", "Run a mobile money kiosk with a starter kit."),
    ("Sample: Construction Safety Training", "TRAINING", "", "Northern", "Rulindo", "ON_SITE", 8, 18, 30, "SECONDARY,TVET", "No skills needed; short safety certification."),
    ("Sample: Research Assistant", "INTERNSHIP", "research, excel, english", "Eastern", "Rwamagana", "HYBRID", 16, 21, 30, "BACHELORS,MASTERS,PHD", "Assist a field research team on youth livelihoods."),
    ("Sample: Tailoring and Fashion Training", "TRAINING", "sewing", "Eastern", "Nyagatare", "ON_SITE", 35, 16, 30, ALL, "Learn tailoring and start your own workshop."),
    ("Sample: Irrigation Technician", "JOB", "mechanics, farming", "Eastern", "Bugesera", "ON_SITE", 21, 20, 30, "TVET,BACHELORS", "Install and repair irrigation equipment."),
    ("Sample: Youth Entrepreneurship Bootcamp", "TRAINING", "", "Kigali City", "Gasabo", "HYBRID", 10, 18, 30, ALL, "Business planning basics. Open to everyone."),
    ("Sample: Graduate Trainee Programme", "JOB", "communication, excel", "Kigali City", "Nyarugenge", "ON_SITE", 45, 21, 30, "BACHELORS,MASTERS", "Twelve-month rotation for recent graduates."),
    ("Sample: Radio Production Internship", "INTERNSHIP", "writing, audio editing", "Southern", "Huye", "ON_SITE", 14, 18, 30, "TVET,BACHELORS", "Help produce youth radio shows."),
    ("Sample: Remote Customer Support", "JOB", "english, computer", "Kigali City", "Kicukiro", "REMOTE", 3, 18, 30, "SECONDARY,TVET,BACHELORS,MASTERS", "Chat support for an online service. Closing very soon."),
    ("Sample: Expired Example (hidden)", "TRAINING", "", "Kigali City", "Gasabo", "ON_SITE", -5, 16, 30, ALL, "Deadline already passed, so it never appears in matches."),
]


def add_real_opportunities(conn):
    """Load the real listings from real_opportunities.csv (filled in by the admin).
    Columns: title,type,province,district,work_mode,deadline(YYYY-MM-DD),apply_link,
    min_age,max_age,education(e.g. TVET,BACHELORS in quotes),required_skills,description,source
    Returns how many rows were added."""
    path = os.path.join(os.path.dirname(__file__), "real_opportunities.csv")
    if not os.path.exists(path):
        return 0
    added = 0
    with open(path, newline="", encoding="utf-8-sig") as f:  # utf-8-sig: Excel adds a hidden mark
        for row in csv.DictReader(f):
            if not (row.get("title") or "").strip():
                continue
            try:
                date.fromisoformat(row["deadline"].strip())
                conn.execute(
                    "INSERT INTO opportunities (title,description,type,required_skills,province,"
                    "district,work_mode,deadline,apply_link,min_age,max_age,education) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (row["title"].strip(), row["description"].strip(), row["type"].strip().upper(),
                     row["required_skills"].strip(), row["province"].strip(), row["district"].strip(),
                     row["work_mode"].strip().upper(), row["deadline"].strip(),
                     row["apply_link"].strip(), int(row["min_age"]), int(row["max_age"]),
                     row["education"].strip().upper()))
                added += 1
            except (ValueError, KeyError, AttributeError):
                print("Skipped a bad row in real_opportunities.csv:", row.get("title"))
    return added


def add_starting_data(conn, with_samples=True):
    """Fill an empty database. Real listings win: when the CSV has rows, the sample
    listings are not added. On the live site (with_samples=False) only the real
    listings are loaded: no sample listings and no demo account with a known password."""
    if conn.execute("SELECT COUNT(*) AS n FROM opportunities").fetchone()["n"] == 0:
        if add_real_opportunities(conn) == 0 and with_samples:
            today = date.today()
            for (title, typ, skills, prov, dist, mode, days, lo, hi, edu, desc) in OPPS:
                conn.execute(
                    "INSERT INTO opportunities (title,description,type,required_skills,province,"
                    "district,work_mode,deadline,apply_link,min_age,max_age,education) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (title, desc, typ, skills, prov, dist, mode,
                     (today + timedelta(days=days)).isoformat(),
                     "https://example.org/apply", lo, hi, edu))
    if with_samples:
        _add_demo_seeker(conn)


def _add_demo_seeker(conn):
    if not conn.execute("SELECT id FROM users WHERE email='seeker@nextfit.rw'").fetchone():
        new_user = conn.execute(
            "INSERT INTO users (name,email,password_hash,role) VALUES (?,?,?,'SEEKER') RETURNING id",
            ("Demo Seeker", "seeker@nextfit.rw", generate_password_hash("Seeker123!"))).fetchone()
        conn.execute(
            "INSERT INTO profiles (user_id,age,province,district,education,status,skills) "
            "VALUES (?,?,?,?,?,?,?)",
            (new_user["id"], 22, "Kigali City", "Gasabo", "BACHELORS", "Graduate",
             "Communication, Excel, English, Computer"))
