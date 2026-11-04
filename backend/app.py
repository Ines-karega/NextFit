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


# ---------------- FR2: seeker profile ----------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = current_user()
    if user is None or user["role"] != "SEEKER":
        return redirect(url_for("login"))
    errors = {}
    if request.method == "POST":
        form = request.form
        age = form["age"]
        if not age.isdigit() or not MIN_SEEKER_AGE <= int(age) <= MAX_SEEKER_AGE:
            errors["age"] = f"Please enter an age from {MIN_SEEKER_AGE} to {MAX_SEEKER_AGE}."
        if not valid_location(form["province"], form["district"]):
            errors["district"] = "Please choose your province, then your district."
        if form["education"] not in EDU_LABEL:
            errors["education"] = "Please choose your education level."
        if form["status"] not in STATUSES:
            errors["status"] = "Please choose your current situation."
        skills = matching.split_skills(form["skills"])
        if len(skills) == 0:
            errors["skills"] = "Please write at least one skill, separated by commas."
        if not errors:
            conn = db.connect()
            conn.execute("DELETE FROM profiles WHERE user_id = ?", (user["id"],))
            conn.execute("INSERT INTO profiles VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (user["id"], int(age), form["province"], form["district"],
                          form["education"], form["status"], ", ".join(skills)))
            conn.commit()
            conn.close()
            flash("Profile saved.", "success")
            return redirect(url_for("dashboard"))
        return render_template("profile.html", errors=errors, form=form)
    return render_template("profile.html", errors=errors, form=get_profile(user["id"]) or {})


# ---------------- FR4, FR5, FR6: dashboard ----------------
@app.route("/dashboard")
def dashboard():
    user = current_user()
    if user is None or user["role"] != "SEEKER":
        return redirect(url_for("login"))
    my_profile = get_profile(user["id"])
    if my_profile is None:
        flash("Please fill in your profile first so we can find your matches.", "info")
        return redirect(url_for("profile"))

    # NFR5: if matching fails, explain what happened instead of showing an empty page
    try:
        all_matches = matching.get_matches(my_profile, get_all_opportunities())
    except Exception:
        flash("Sorry, we could not work out your matches just now. Please refresh, or browse all opportunities.", "error")
        return redirect(url_for("browse"))
    shown = filter_results(all_matches)
    nearby = [m for m in shown if m["in_district"]]       # FR5.3: own district first
    elsewhere = [m for m in shown if not m["in_district"]]
    return render_template("dashboard.html", my_profile=my_profile, nearby=nearby, elsewhere=elsewhere,
                           total=len(all_matches), shown=len(shown),
                           saved=get_saved_ids(user["id"]), reminders=get_reminders(user["id"]),
                           args=request.args)


# ---------------- FR9: browse everything ----------------
@app.route("/browse")
def browse():
    user = current_user()
    if user is None or user["role"] != "SEEKER":
        return redirect(url_for("login"))
    my_profile = get_profile(user["id"])
    if my_profile is None:
        return redirect(url_for("profile"))
    results = [matching.check(my_profile, o) for o in get_all_opportunities() if matching.is_open(o)]
    results.sort(key=lambda r: r["opp"]["deadline"])
    return render_template("browse.html", items=filter_results(results),
                           saved=get_saved_ids(user["id"]), args=request.args)


# ---------------- FR7, FR8: saved opportunities ----------------
@app.route("/saved")
def saved_page():
    user = current_user()
    if user is None or user["role"] != "SEEKER":
        return redirect(url_for("login"))
    my_profile = get_profile(user["id"])
    if my_profile is None:
        return redirect(url_for("profile"))
    ids = get_saved_ids(user["id"])
    items = [matching.check(my_profile, o) for o in get_all_opportunities() if o["id"] in ids]
    for item in items:
        item["expired"] = not matching.is_open(item["opp"])
    items.sort(key=lambda r: r["opp"]["deadline"])
    return render_template("saved.html", items=items, saved=ids, reminders=get_reminders(user["id"]))


@app.route("/save/<int:opp_id>", methods=["POST"])
def save(opp_id):
    user = current_user()
    if user is None or user["role"] != "SEEKER":
        return redirect(url_for("login"))
    conn = db.connect()
    conn.execute("INSERT OR IGNORE INTO saved (user_id, opportunity_id) VALUES (?, ?)", (user["id"], opp_id))
    conn.commit()
    conn.close()
    flash("Saved to your shortlist.", "success")
    return redirect(request.form.get("next") or url_for("saved_page"))


@app.route("/unsave/<int:opp_id>", methods=["POST"])
def unsave(opp_id):
    user = current_user()
    if user is None or user["role"] != "SEEKER":
        return redirect(url_for("login"))
    conn = db.connect()
    conn.execute("DELETE FROM saved WHERE user_id = ? AND opportunity_id = ?", (user["id"], opp_id))
    conn.commit()
    conn.close()
    flash("Removed from your shortlist.", "info")
    return redirect(request.form.get("next") or url_for("saved_page"))


# ---------------- FR3, FR10: admin ----------------
def admin_only():
    """Returns the admin user, or None if the visitor is not an admin."""
    user = current_user()
    if user is None or user["role"] != "ADMIN":
        return None
    return user


def check_opportunity_form(form):
    """Returns a list of error messages (empty list = form is fine)."""
    errors = {}
    for field in ["title", "description", "apply_link"]:
        if form[field].strip() == "":
            errors[field] = "This field is required."
    if form["type"] not in TYPE_LABEL:
        errors["type"] = "Please choose a type."
    if form["work_mode"] not in MODE_LABEL:
        errors["work_mode"] = "Please choose a work mode."
    if not valid_location(form["province"], form["district"]):
        errors["district"] = "Please choose a province and a district."
    try:
        date.fromisoformat(form["deadline"])
    except ValueError:
        errors["deadline"] = "Please choose a deadline date."
    if not (form["min_age"].isdigit() and form["max_age"].isdigit()) or int(form["min_age"]) > int(form["max_age"]):
        errors["age"] = "Enter a minimum and maximum age (minimum cannot be bigger)."
    if len(form.getlist("education")) == 0:
        errors["education"] = "Choose at least one education level."
    return errors


def opportunity_values(form):
    """The form fields in the order of the database columns used below."""
    return (form["title"].strip(), form["description"].strip(), form["type"],
            ", ".join(matching.split_skills(form["required_skills"])), form["province"],
            form["district"], form["work_mode"], form["deadline"], form["apply_link"].strip(),
            int(form["min_age"]), int(form["max_age"]), ",".join(form.getlist("education")))


COLUMNS = ("title, description, type, required_skills, province, district, "
           "work_mode, deadline, apply_link, min_age, max_age, education")


@app.route("/admin/opportunities")
def admin_opportunities():
    if admin_only() is None:
        abort(403)
    conn = db.connect()
    rows = conn.execute("SELECT * FROM opportunities ORDER BY status, deadline").fetchall()
    conn.close()
    return render_template("admin_opps.html", opps=rows)


@app.route("/admin/opportunities/new", methods=["GET", "POST"])
def admin_add():
    if admin_only() is None:
        abort(403)
    errors = {}
    if request.method == "POST":
        errors = check_opportunity_form(request.form)
        if not errors:
            conn = db.connect()
            conn.execute(f"INSERT INTO opportunities ({COLUMNS}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                         opportunity_values(request.form))
            conn.commit()
            conn.close()
            flash("Opportunity added.", "success")
            return redirect(url_for("admin_opportunities"))
        return render_template("admin_form.html", errors=errors, o=request.form,
                               chosen=request.form.getlist("education"), title="Add opportunity")
    return render_template("admin_form.html", errors=errors, o={"min_age": 16, "max_age": 30},
                           chosen=[], title="Add opportunity")


@app.route("/admin/opportunities/<int:opp_id>/edit", methods=["GET", "POST"])
def admin_edit(opp_id):
    if admin_only() is None:
        abort(403)
    conn = db.connect()
    opp = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opp_id,)).fetchone()
    if opp is None:
        conn.close()
        abort(404)
    if request.method == "POST":
        errors = check_opportunity_form(request.form)
        if not errors:
            conn.execute(f"UPDATE opportunities SET ({COLUMNS}) = (?,?,?,?,?,?,?,?,?,?,?,?) WHERE id = ?",
                         opportunity_values(request.form) + (opp_id,))
            conn.commit()
            conn.close()
            flash("Opportunity updated.", "success")
            return redirect(url_for("admin_opportunities"))
        conn.close()
        return render_template("admin_form.html", errors=errors, o=request.form,
                               chosen=request.form.getlist("education"), title="Edit opportunity")
    conn.close()
    return render_template("admin_form.html", errors={}, o=opp,
                           chosen=opp["education"].split(","), title="Edit opportunity")


@app.route("/admin/opportunities/<int:opp_id>/close", methods=["POST"])
def admin_close(opp_id):
    if admin_only() is None:
        abort(403)
    conn = db.connect()
    conn.execute("UPDATE opportunities SET status = 'CLOSED' WHERE id = ?", (opp_id,))
    conn.commit()
    conn.close()
    flash("Opportunity closed. Seekers will no longer see it.", "info")
    return redirect(url_for("admin_opportunities"))


@app.route("/admin/opportunities/<int:opp_id>/delete", methods=["POST"])
def admin_delete(opp_id):
    if admin_only() is None:
        abort(403)
    conn = db.connect()
    conn.execute("DELETE FROM opportunities WHERE id = ?", (opp_id,))
    conn.execute("DELETE FROM saved WHERE opportunity_id = ?", (opp_id,))
    conn.commit()
    conn.close()
    flash("Opportunity removed.", "info")
    return redirect(url_for("admin_opportunities"))


@app.route("/admin/users", methods=["GET", "POST"])
def admin_users():
    if admin_only() is None:
        abort(403)
    errors = {}
    conn = db.connect()
    if request.method == "POST":  # create another admin account
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        if name == "":
            errors["name"] = "Please enter a name."
        if "@" not in email:
            errors["email"] = "Please enter a valid email."
        if len(request.form["password"]) < 8:
            errors["password"] = "At least 8 characters."
        if not errors:
            try:
                conn.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, 'ADMIN')",
                             (name, email, generate_password_hash(request.form["password"])))
                conn.commit()
                flash("Admin account created.", "success")
            except sqlite3.IntegrityError:
                errors["email"] = "That email is already used."
    people = conn.execute("SELECT id, name, email, role FROM users ORDER BY role, name").fetchall()
    conn.close()
    return render_template("admin_users.html", people=people, errors=errors, form=request.form)


@app.route("/admin/users/<int:person_id>/delete", methods=["POST"])
def admin_remove_user(person_id):
    admin = admin_only()
    if admin is None:
        abort(403)
    if person_id == admin["id"]:
        flash("You cannot remove your own account.", "error")
    else:
        conn = db.connect()
        conn.execute("DELETE FROM profiles WHERE user_id = ?", (person_id,))
        conn.execute("DELETE FROM saved WHERE user_id = ?", (person_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (person_id,))
        conn.commit()
        conn.close()
        flash("Account removed.", "info")
    return redirect(url_for("admin_users"))


# ---------------- friendly error pages (NFR5) ----------------
@app.errorhandler(403)
def error_403(e):
    return render_template("error.html", msg="You do not have permission to open this page."), 403


@app.errorhandler(404)
def error_404(e):
    return render_template("error.html", msg="We could not find that page."), 404


@app.errorhandler(500)
def error_500(e):
    return render_template("error.html", msg="Something went wrong on our side. Please try again in a moment."), 500


if __name__ == "__main__":
    app.run(debug=True)
