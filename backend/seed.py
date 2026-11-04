"""Demo data so the prototype works on first run (hypothesis needs 20+ opportunities).
These are SAMPLE listings for demonstration only; an admin replaces them with real ones.
Deadlines are relative to today so the demo never goes stale."""
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


def add_demo_data(conn):
    if conn.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0] == 0:
        today = date.today()
        for (title, typ, skills, prov, dist, mode, days, lo, hi, edu, desc) in OPPS:
            conn.execute(
                "INSERT INTO opportunities (title,description,type,required_skills,province,"
                "district,work_mode,deadline,apply_link,min_age,max_age,education) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (title, desc, typ, skills, prov, dist, mode,
                 (today + timedelta(days=days)).isoformat(),
                 "https://example.org/apply", lo, hi, edu))
    if not conn.execute("SELECT 1 FROM users WHERE email='seeker@nextfit.rw'").fetchone():
        cur = conn.execute(
            "INSERT INTO users (name,email,password_hash,role) VALUES (?,?,?,'SEEKER')",
            ("Demo Seeker", "seeker@nextfit.rw", generate_password_hash("Seeker123!")))
        conn.execute(
            "INSERT INTO profiles (user_id,age,province,district,education,status,skills) "
            "VALUES (?,?,?,?,?,?,?)",
            (cur.lastrowid, 22, "Kigali City", "Gasabo", "BACHELORS", "Graduate",
             "Communication, Excel, English, Computer"))
