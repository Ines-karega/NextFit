"""NextFit web platform: all the pages (routes). See README.md for how to run it.

This file is the "route controller" of SRS Appendix B.4: it receives each request,
asks matching.py and db.py for what it needs, and sends back the page.
"""
import os
import secrets
from datetime import date, datetime, timedelta

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

import db
import emailer
import matching
from rwanda import (EDU_LABEL, EDUCATION_LEVELS, LOCATIONS, MAX_SEEKER_AGE, MIN_SEEKER_AGE,
                    MODE_LABEL, OPP_TYPES, STATUSES, TYPE_LABEL, WORK_MODES, valid_location)

# The HTML pages and the CSS/JavaScript live in the frontend folder.
app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
app.secret_key = os.environ.get("SECRET_KEY", "change-me-before-going-live")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"   # other websites cannot submit our forms for a logged-in user

if db.ON_LIVE_SITE:
    if "SECRET_KEY" not in os.environ:
        raise RuntimeError("Set a private SECRET_KEY before starting the live site.")
    app.config["SESSION_COOKIE_SECURE"] = True   # NFR2: the login cookie only travels over HTTPS
    # The hosting company receives the HTTPS request and passes it on to us; this lets
    # Flask see the real address, so the links we email start with https://.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.teardown_appcontext(db.close_connection)   # close the database after every page
db.setup()                                     # create tables and starting data when the server starts


@app.context_processor
def values_for_every_page():
    """Make these names available inside all templates."""
    return dict(LOCATIONS=LOCATIONS, EDUCATION_LEVELS=EDUCATION_LEVELS, EDU_LABEL=EDU_LABEL,
                OPP_TYPES=OPP_TYPES, TYPE_LABEL=TYPE_LABEL, WORK_MODES=WORK_MODES,
                MODE_LABEL=MODE_LABEL, STATUSES=STATUSES, user=current_user())


@app.template_filter("days_text")
def days_text(days):
    """FR5.2: 0 -> 'last day today', 1 -> '1 day left', 9 -> '9 days left'."""
    if days == 0:
        return "last day today"
    if days == 1:
        return "1 day left"
    return f"{days} days left"


# ---------------- small helper functions ----------------
def current_user():
    """The logged-in user (a database row), or None. Looked up once per page."""
    if "user_id" not in session:
        return None
    if "user" not in g:
        g.user = db.get_user(session["user_id"])
    return g.user


def seeker_only():
    """Returns the seeker user, or None if the visitor is not a logged-in seeker."""
    user = current_user()
    if user is None or user["role"] != "SEEKER":
        return None
    return user


def get_reminders(user_id):
    """FR8: saved opportunities whose deadline is 14 days away or less."""
    return [{"opp": opp, "days_left": matching.days_until(opp["deadline"])}
            for opp in db.get_due_saved_items(user_id)]


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


def go_back(default_page):
    """After Save / Remove, return to the page the seeker was on.
    Only addresses inside NextFit are accepted, never a link to another website."""
    target = request.form.get("next", "")
    if target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return redirect(target)
    return redirect(url_for(default_page))


# ---------------- public pages ----------------
@app.route("/")
def home():
    user = current_user()
    if user is None:
        return render_template("home.html")
    if user["role"] == "ADMIN":
        counts = db.count_opportunities(date.today().isoformat())   # open, expired, closed
        counts["seekers"] = db.count_seekers()
        return render_template("home_admin.html", counts=counts)

    # Seeker home: a short summary of what is waiting for them
    my_profile = db.get_profile(user["id"])
    match_count = 0
    top_pick = None
    demand = []
    if my_profile is not None:
        open_opps = db.get_open_opportunities(date.today().isoformat())
        matches = matching.match_all(my_profile, open_opps)
        match_count = len(matches)
        if matches:
            top_pick = matches[0]  # in your district first, then closest deadline
        demand = matching.skills_in_demand(my_profile, open_opps)
    return render_template("home_seeker.html", my_profile=my_profile, match_count=match_count,
                           top_pick=top_pick, demand=demand,
                           saved_count=len(db.get_saved_ids(user["id"])),
                           reminders=get_reminders(user["id"])[:3])


@app.route("/help")
def help_page():
    return render_template("help.html")


@app.route("/health")
def health():
    """A tiny page that answers "ok" when the site is running. It does not use the
    database, so it is a quick way to check that the live site is up."""
    return "ok"


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
            try:
                # The role is always SEEKER here: admins cannot sign up publicly (FR1.1).
                session["user_id"] = db.add_user(name, email, generate_password_hash(password), "SEEKER")
                return redirect(url_for("profile"))
            except db.DuplicateError:
                errors["email"] = "This email already has an account. Try logging in."
    return render_template("signup.html", errors=errors, form=request.form)


@app.route("/login", methods=["GET", "POST"])
def login():
    errors = {}
    if request.method == "POST":
        found = db.get_user_by_email(request.form["email"].strip().lower())
        if found and check_password_hash(found["password_hash"], request.form["password"]):
            session["user_id"] = found["id"]
            return redirect(url_for("home"))
        errors["password"] = "That email or password is not correct."
    return render_template("login.html", errors=errors, form=request.form)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    link = None
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        found = db.get_user_by_email(email)
        if found:
            token = secrets.token_urlsafe(24)
            expires = (datetime.now() + timedelta(hours=1)).isoformat()
            db.add_reset_token(token, found["id"], expires)
            reset_link = url_for("reset", token=token, _external=True)
            sent = emailer.send_reset_email(email, reset_link)
            if not sent and not emailer.email_is_set_up():
                link = reset_link  # demo mode: no email service set up, so show the link here
        # The same message is shown whether or not the account exists, so nobody can
        # use this page to find out who has an account (NFR9).
        if emailer.email_is_set_up():
            flash("If that email has an account, we have sent a reset link to it. "
                  "Please check your inbox, and your spam folder too.", "info")
        else:
            flash("If that email has an account, a reset link is ready below.", "info")
    return render_template("forgot.html", link=link)


@app.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    row = db.get_reset_token(token)
    if row is None or datetime.fromisoformat(row["expires"]) < datetime.now():
        flash("This reset link is not valid or has expired. Please ask for a new one.", "error")
        return redirect(url_for("forgot"))
    errors = {}
    if request.method == "POST":
        if len(request.form["password"]) < 8:
            errors["password"] = "Your password needs at least 8 characters."
        else:
            db.set_password(row["user_id"], generate_password_hash(request.form["password"]))
            db.delete_reset_tokens(row["user_id"])
            flash("Password changed. Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("reset.html", errors=errors)


# ---------------- FR2: seeker profile ----------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = seeker_only()
    if user is None:
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
            db.save_profile(user["id"], int(age), form["province"], form["district"],
                            form["education"], form["status"], ", ".join(skills))
            flash("Profile saved.", "success")
            return redirect(url_for("dashboard"))
        return render_template("profile.html", errors=errors, form=form)
    return render_template("profile.html", errors=errors, form=db.get_profile(user["id"]) or {})


# ---------------- FR4, FR5, FR6: dashboard ----------------
@app.route("/dashboard")
def dashboard():
    user = seeker_only()
    if user is None:
        return redirect(url_for("login"))
    my_profile = db.get_profile(user["id"])
    if my_profile is None:
        flash("Please fill in your profile first so we can find your matches.", "info")
        return redirect(url_for("profile"))

    # NFR5: if matching fails, explain what happened instead of showing an empty page
    try:
        all_matches = matching.get_matches(user["id"])
    except Exception:
        flash("Sorry, we could not work out your matches just now. Please refresh, or browse all opportunities.", "error")
        return redirect(url_for("browse"))
    shown = filter_results(all_matches)
    nearby = [m for m in shown if m["in_district"]]       # FR5.3: own district first
    elsewhere = [m for m in shown if not m["in_district"]]
    return render_template("dashboard.html", my_profile=my_profile, nearby=nearby, elsewhere=elsewhere,
                           total=len(all_matches), shown=len(shown),
                           saved=db.get_saved_ids(user["id"]), reminders=get_reminders(user["id"]),
                           args=request.args)


@app.route("/api/dashboard")
def api_dashboard():
    """The same dashboard information as JSON (SRS 3.4 and B.4 steps 20 to 23):
    the matched list with reasons, the reminders, or a no-match message."""
    user = seeker_only()
    if user is None:
        return jsonify(error="Please log in as a seeker first."), 401
    if db.get_profile(user["id"]) is None:
        return jsonify(error="Please fill in your profile first."), 400
    matches = []
    for m in matching.get_matches(user["id"]):
        opp = m["opp"]
        matches.append({
            "id": opp["id"], "title": opp["title"], "type": opp["type"],
            "province": opp["province"], "district": opp["district"], "work_mode": opp["work_mode"],
            "deadline": opp["deadline"], "days_left": m["days_left"], "apply_link": opp["apply_link"],
            "in_seeker_district": m["in_district"], "skill_match": m["skill_match"],
            "reasons": [{"met": passed, "text": sentence} for passed, sentence in m["reasons"]],
        })
    reminders = [{"id": r["opp"]["id"], "title": r["opp"]["title"], "deadline": r["opp"]["deadline"],
                  "days_left": r["days_left"]} for r in get_reminders(user["id"])]
    message = None
    if len(matches) == 0:
        message = "No matches yet. You can browse all open opportunities at " + url_for("browse")
    return jsonify(matches=matches, reminders=reminders, message=message)


# ---------------- FR9: browse everything ----------------
@app.route("/browse")
def browse():
    user = seeker_only()
    if user is None:
        return redirect(url_for("login"))
    my_profile = db.get_profile(user["id"])
    if my_profile is None:
        return redirect(url_for("profile"))
    open_opps = db.get_open_opportunities(date.today().isoformat())   # already closest deadline first
    results = [matching.check(my_profile, opp) for opp in open_opps]
    return render_template("browse.html", items=filter_results(results),
                           saved=db.get_saved_ids(user["id"]), args=request.args)


# ---------------- FR7, FR8: saved opportunities ----------------
@app.route("/saved")
def saved_page():
    user = seeker_only()
    if user is None:
        return redirect(url_for("login"))
    my_profile = db.get_profile(user["id"])
    if my_profile is None:
        return redirect(url_for("profile"))
    items = [matching.check(my_profile, opp) for opp in db.get_saved_opportunities(user["id"])]
    for item in items:
        item["expired"] = not matching.is_open(item["opp"])
    return render_template("saved.html", items=items, saved=db.get_saved_ids(user["id"]),
                           reminders=get_reminders(user["id"]))


@app.route("/save/<int:opp_id>", methods=["POST"])
def save(opp_id):
    user = seeker_only()
    if user is None:
        return redirect(url_for("login"))
    if db.get_opportunity(opp_id) is None:
        abort(404)
    db.save_opportunity(user["id"], opp_id)
    flash("Saved to your shortlist.", "success")
    return go_back("saved_page")


@app.route("/unsave/<int:opp_id>", methods=["POST"])
def unsave(opp_id):
    user = seeker_only()
    if user is None:
        return redirect(url_for("login"))
    db.remove_saved(user["id"], opp_id)
    flash("Removed from your shortlist.", "info")
    return go_back("saved_page")


# ---------------- FR3, FR10: admin ----------------
def admin_only():
    """Returns the admin user, or None if the visitor is not an admin."""
    user = current_user()
    if user is None or user["role"] != "ADMIN":
        return None
    return user


def check_opportunity_form(form):
    """Returns the error messages by field (empty = the form is fine). FR3.1."""
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
    chosen = form.getlist("education")
    if len(chosen) == 0 or any(level not in EDU_LABEL for level in chosen):
        errors["education"] = "Choose at least one education level."
    return errors


def opportunity_values(form):
    """The form fields in the order of db.OPPORTUNITY_COLUMNS."""
    return (form["title"].strip(), form["description"].strip(), form["type"],
            ", ".join(matching.split_skills(form["required_skills"])), form["province"],
            form["district"], form["work_mode"], form["deadline"], form["apply_link"].strip(),
            int(form["min_age"]), int(form["max_age"]), ",".join(form.getlist("education")))


@app.route("/admin/opportunities")
def admin_opportunities():
    if admin_only() is None:
        abort(403)
    # today is passed in so the page can mark listings whose deadline has passed
    return render_template("admin_opps.html", opps=db.get_all_opportunities(), today=date.today().isoformat())


@app.route("/admin/opportunities/new", methods=["GET", "POST"])
def admin_add():
    admin = admin_only()
    if admin is None:
        abort(403)
    errors = {}
    if request.method == "POST":
        errors = check_opportunity_form(request.form)
        if not errors:
            db.add_opportunity(opportunity_values(request.form), admin["id"])   # remember who added it
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
    opp = db.get_opportunity(opp_id)
    if opp is None:
        abort(404)
    if request.method == "POST":
        errors = check_opportunity_form(request.form)
        if not errors:
            db.update_opportunity(opp_id, opportunity_values(request.form))
            flash("Opportunity updated.", "success")
            return redirect(url_for("admin_opportunities"))
        return render_template("admin_form.html", errors=errors, o=request.form,
                               chosen=request.form.getlist("education"), title="Edit opportunity")
    return render_template("admin_form.html", errors={}, o=opp,
                           chosen=opp["education"].split(","), title="Edit opportunity")


@app.route("/admin/opportunities/<int:opp_id>/close", methods=["POST"])
def admin_close(opp_id):
    if admin_only() is None:
        abort(403)
    db.close_opportunity(opp_id)
    flash("Opportunity closed. Seekers will no longer see it.", "info")
    return redirect(url_for("admin_opportunities"))


@app.route("/admin/opportunities/<int:opp_id>/delete", methods=["POST"])
def admin_delete(opp_id):
    if admin_only() is None:
        abort(403)
    db.delete_opportunity(opp_id)
    flash("Opportunity removed.", "info")
    return redirect(url_for("admin_opportunities"))


@app.route("/admin/users", methods=["GET", "POST"])
def admin_users():
    if admin_only() is None:
        abort(403)
    errors = {}
    if request.method == "POST":  # create another admin account (FR1.1)
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
                db.add_user(name, email, generate_password_hash(request.form["password"]), "ADMIN")
                flash("Admin account created.", "success")
                return redirect(url_for("admin_users"))
            except db.DuplicateError:
                errors["email"] = "That email is already used."
    return render_template("admin_users.html", people=db.get_all_users(), errors=errors, form=request.form)


@app.route("/admin/users/<int:person_id>/delete", methods=["POST"])
def admin_remove_user(person_id):
    admin = admin_only()
    if admin is None:
        abort(403)
    if person_id == admin["id"]:
        flash("You cannot remove your own account.", "error")
    else:
        db.delete_user(person_id)
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
