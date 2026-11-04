"""NextFit web platform: all the pages (routes). See README.md for how to run it."""
import os
import secrets
import sqlite3
from datetime import date, datetime, timedelta

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import db
import emailer
import matching
from rwanda import (EDU_LABEL, EDUCATION_LEVELS, LOCATIONS, MAX_SEEKER_AGE, MIN_SEEKER_AGE,
                    MODE_LABEL, OPP_TYPES, STATUSES, TYPE_LABEL, WORK_MODES, valid_location)

# The HTML pages and the CSS/JavaScript live in the frontend folder.
app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.secret_key = os.environ.get("SECRET_KEY", "change-me-before-going-live")
db.setup()  # create tables and demo data when the server starts


@app.context_processor
def values_for_every_page():
    """Make these names available inside all templates."""
    return dict(LOCATIONS=LOCATIONS, EDUCATION_LEVELS=EDUCATION_LEVELS, EDU_LABEL=EDU_LABEL,
                OPP_TYPES=OPP_TYPES, TYPE_LABEL=TYPE_LABEL, WORK_MODES=WORK_MODES,
                MODE_LABEL=MODE_LABEL, STATUSES=STATUSES, user=current_user())


# ---------------- small helper functions ----------------
def current_user():
    """The logged-in user (a database row), or None."""
    if "user_id" not in session:
        return None
    conn = db.connect()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return row


def get_profile(user_id):
    conn = db.connect()
    row = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def get_all_opportunities():
    conn = db.connect()
    rows = conn.execute("SELECT * FROM opportunities").fetchall()
    conn.close()
    return rows


def get_saved_ids(user_id):
    conn = db.connect()
    rows = conn.execute("SELECT opportunity_id FROM saved WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return [r["opportunity_id"] for r in rows]


def get_reminders(user_id):
    """FR8: saved opportunities whose deadline is 14 days away or less."""
    reminders = []
    for opp in get_all_opportunities():
        if opp["id"] in get_saved_ids(user_id) and matching.is_open(opp):
            days = matching.days_until(opp["deadline"])
            if days <= 14:
                reminders.append({"opp": opp, "days_left": days})
    reminders.sort(key=lambda r: r["days_left"])
    return reminders


def filter_results(results):
    """FR6: keep only results that fit the search box and the type/district filters."""
    word = request.args.get("q", "").strip().lower()
    kind = request.args.get("type", "")
    province = request.args.get("province", "")
    district = request.args.get("district", "")
    kept = []
    for r in results:
        opp = r["opp"]
        text = (opp["title"] + " " + opp["description"] + " " + opp["required_skills"]).lower()
        if word and word not in text:
            continue
        if kind and opp["type"] != kind:
            continue
        if province and opp["province"] != province:
            continue
        if district and opp["district"] != district:
            continue
        kept.append(r)
    return kept


# ---------------- public pages ----------------
@app.route("/")
def home():
    user = current_user()
    if user is None:
        return render_template("home.html")
    if user["role"] == "ADMIN":
        return redirect(url_for("admin_opportunities"))
    return redirect(url_for("dashboard"))


@app.route("/help")
def help_page():
    return render_template("help.html")


# ---------------- FR1: sign up, log in, reset password ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    errors = {}
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if name == "":
            errors["name"] = "Please enter your name."
        if "@" not in email:
            errors["email"] = "Please enter a valid email address."
        if len(password) < 8:
            errors["password"] = "Your password needs at least 8 characters."
        if not errors:
            conn = db.connect()
            try:
                cursor = conn.execute(
                    "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'SEEKER')",
                    (name, email, generate_password_hash(password)))
                conn.commit()
                session["user_id"] = cursor.lastrowid
                return redirect(url_for("profile"))
            except sqlite3.IntegrityError:
                errors["email"] = "This email already has an account. Try logging in."
            finally:
                conn.close()
    return render_template("signup.html", errors=errors, form=request.form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        conn = db.connect()
        found = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if found and check_password_hash(found["password_hash"], request.form["password"]):
            session["user_id"] = found["id"]
            return redirect(url_for("home"))
        flash("That email or password is not correct.", "error")
    return render_template("login.html", form=request.form)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    link = None
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        conn = db.connect()
        found = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if found:
            token = secrets.token_urlsafe(24)
            expires = (datetime.now() + timedelta(hours=1)).isoformat()
            conn.execute("INSERT INTO reset_tokens (token, user_id, expires) VALUES (?, ?, ?)",
                         (token, found["id"], expires))
            conn.commit()
            reset_link = url_for("reset", token=token, _external=True)
            sent = emailer.send_reset_email(email, reset_link)
            if not sent and not emailer.email_is_set_up():
                link = reset_link  # demo mode: no email service set up, so show the link here
        conn.close()
        if emailer.email_is_set_up():
            flash("If that email has an account, we have sent a reset link to it. Please check your inbox.", "info")
        else:
            flash("If that email has an account, a reset link is ready below.", "info")
    return render_template("forgot.html", link=link)


@app.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    conn = db.connect()
    row = conn.execute("SELECT * FROM reset_tokens WHERE token = ?", (token,)).fetchone()
    if row is None or datetime.fromisoformat(row["expires"]) < datetime.now():
        conn.close()
        flash("This reset link is not valid or has expired. Please ask for a new one.", "error")
        return redirect(url_for("forgot"))
    if request.method == "POST":
        if len(request.form["password"]) < 8:
            flash("Your password needs at least 8 characters.", "error")
        else:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                         (generate_password_hash(request.form["password"]), row["user_id"]))
            conn.execute("DELETE FROM reset_tokens WHERE token = ?", (token,))
            conn.commit()
            conn.close()
            flash("Password changed. Please log in.", "success")
            return redirect(url_for("login"))
    conn.close()
    return render_template("reset.html")


if __name__ == "__main__":
    app.run(debug=True)
