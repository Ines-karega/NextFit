"""Tests that walk through the main journeys of the website, page by page.

Run from the main project folder with:
    python -m unittest discover tests
Each run uses a new, empty practice database in a temporary folder, so your own
nextfit.db and the live site are never touched. No emails are really sent.
"""
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

# Use a throwaway database with only the first admin in it (no starting listings).
TEMP_FOLDER = tempfile.mkdtemp()
os.environ["NEXTFIT_DB"] = os.path.join(TEMP_FOLDER, "test.db")
os.environ["NEXTFIT_SEED"] = "0"
os.environ.pop("DATABASE_URL", None)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

import app as nextfit  # noqa: E402  (must come after the settings above)
import db  # noqa: E402
import emailer  # noqa: E402

ADMIN_EMAIL, ADMIN_PASSWORD = "admin@nextfit.rw", "Admin123!"   # created on first start on a computer


def days_from_today(n):
    return (date.today() + timedelta(days=n)).isoformat()


class Journeys(unittest.TestCase):

    def setUp(self):
        self.admin = nextfit.app.test_client()
        self.admin.post("/login", data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})

    # ---------- helpers ----------
    def new_seeker(self, email, **profile):
        """Sign up a seeker and fill in a profile. Returns the logged-in browser."""
        browser = nextfit.app.test_client()
        browser.post("/signup", data={"name": "Test Seeker", "email": email, "password": "password1"})
        details = {"age": "22", "province": "Kigali City", "district": "Gasabo",
                   "education": "BACHELORS", "status": "Graduate", "skills": "Excel, Communication"}
        details.update(profile)
        browser.post("/profile", data=details)
        return browser

    def add_opportunity(self, title, **changes):
        form = {"title": title, "description": "A test opportunity.", "type": "JOB",
                "province": "Kigali City", "district": "Gasabo", "work_mode": "ON_SITE",
                "deadline": days_from_today(10), "apply_link": "https://example.org/apply",
                "advert_link": "", "min_age": "18", "max_age": "30",
                "required_skills": "Excel", "education": ["BACHELORS"]}
        form.update(changes)
        return self.admin.post("/admin/opportunities/new", data=form)

    def opportunity_id(self, title):
        with nextfit.app.app_context():
            return next(o["id"] for o in db.get_all_opportunities() if o["title"] == title)

    def page(self, browser, address):
        return browser.get(address).get_data(as_text=True)

    # ---------- FR1: accounts ----------
    def test_sign_up_always_makes_a_seeker(self):
        browser = nextfit.app.test_client()
        browser.post("/signup", data={"name": "A", "email": "role@example.com", "password": "password1", "role": "ADMIN"})
        with nextfit.app.app_context():
            self.assertEqual(db.get_user_by_email("role@example.com")["role"], "SEEKER")

    def test_passwords_are_not_stored_as_typed(self):
        nextfit.app.test_client().post("/signup", data={"name": "A", "email": "hash@example.com", "password": "password1"})
        with nextfit.app.app_context():
            self.assertNotEqual(db.get_user_by_email("hash@example.com")["password_hash"], "password1")

    def test_incomplete_email_is_refused_with_a_message(self):
        for wrong in ["aline", "aline@", "aline@gmail", "aline @gmail.com"]:
            page = nextfit.app.test_client().post("/signup", data={"name": "A", "email": wrong, "password": "password1"}).get_data(as_text=True)
            self.assertIn("Please enter a full email address", page, wrong)

    def test_weak_password_is_refused_with_a_message(self):
        short = nextfit.app.test_client().post("/signup", data={"name": "A", "email": "weak1@example.com", "password": "abc1"}).get_data(as_text=True)
        self.assertIn("at least 8 characters", short)
        no_number = nextfit.app.test_client().post("/signup", data={"name": "A", "email": "weak2@example.com", "password": "password"}).get_data(as_text=True)
        self.assertIn("at least one letter and one number", no_number)
        with nextfit.app.app_context():
            self.assertIsNone(db.get_user_by_email("weak2@example.com"))

    def test_wrong_password_is_refused(self):
        page = nextfit.app.test_client().post("/login", data={"email": ADMIN_EMAIL, "password": "wrong"}).get_data(as_text=True)
        self.assertIn("That email or password is not correct", page)

    def test_password_reset_link_works_once(self):
        self.new_seeker("reset@example.com")
        sent = {}
        original = (emailer.email_is_set_up, emailer.send_reset_email)
        emailer.email_is_set_up = lambda: True
        emailer.send_reset_email = lambda to, link: sent.update(to=to, link=link) or True
        try:
            browser = nextfit.app.test_client()
            browser.post("/forgot", data={"email": "reset@example.com"})
            self.assertEqual(sent["to"], "reset@example.com")
            reset_page = "/" + sent["link"].split("/", 3)[3]
            self.assertEqual(browser.post(reset_page, data={"password": "newpassword9"}).status_code, 302)
            self.assertEqual(browser.get(reset_page).status_code, 302)   # the link no longer works
            login = nextfit.app.test_client().post("/login", data={"email": "reset@example.com", "password": "newpassword9"})
            self.assertEqual(login.status_code, 302)
        finally:
            emailer.email_is_set_up, emailer.send_reset_email = original

    def test_reset_link_is_never_shown_on_the_page(self):
        self.new_seeker("nolink@example.com")
        page = nextfit.app.test_client().post("/forgot", data={"email": "nolink@example.com"}).get_data(as_text=True)
        self.assertNotIn("/reset/", page)
        self.assertIn("If that email has an account, we have sent a reset link", page)

    def test_reset_page_gives_the_same_answer_for_unknown_emails(self):
        page = nextfit.app.test_client().post("/forgot", data={"email": "nobody@example.com"}).get_data(as_text=True)
        self.assertIn("If that email has an account, we have sent a reset link", page)

    # ---------- FR2: profile ----------
    def test_profile_refuses_an_age_outside_16_to_30(self):
        browser = self.new_seeker("age@example.com")
        page = browser.post("/profile", data={"age": "40", "province": "Kigali City", "district": "Gasabo",
                                              "education": "BACHELORS", "status": "Graduate",
                                              "skills": "Excel"}).get_data(as_text=True)
        self.assertIn("Please enter an age from 16 to 30", page)

    # ---------- FR3, FR4, FR5: opportunities and matching ----------
    def test_new_opportunity_reaches_the_right_seeker(self):
        self.add_opportunity("Journey match")
        self.add_opportunity("Journey wrong education", education=["TVET"])
        dashboard = self.page(self.new_seeker("match@example.com"), "/dashboard")
        self.assertIn("Journey match", dashboard)
        self.assertNotIn("Journey wrong education", dashboard)

    def test_expired_and_closed_opportunities_are_hidden(self):
        self.add_opportunity("Journey expired", deadline=days_from_today(-1))
        self.add_opportunity("Journey closed")
        self.admin.post(f"/admin/opportunities/{self.opportunity_id('Journey closed')}/close")
        dashboard = self.page(self.new_seeker("hidden@example.com"), "/dashboard")
        self.assertNotIn("Journey expired", dashboard)
        self.assertNotIn("Journey closed", dashboard)

    def test_admin_list_records_who_added_and_marks_expired(self):
        self.add_opportunity("Journey added by", deadline=days_from_today(-2))
        page = self.page(self.admin, "/admin/opportunities")
        row = page[page.index("Journey added by"):]
        self.assertIn("NextFit Admin", row[:800])
        self.assertIn("Deadline passed", row[:800])

    def test_opportunity_needs_its_eligibility_rules(self):
        page = self.add_opportunity("", deadline="", min_age="", education=[]).get_data(as_text=True)
        self.assertIn("This field is required", page)
        self.assertIn("Choose at least one education level", page)



    # ---------- FR6, FR9: search and browse ----------
    def test_search_and_browse_all(self):
        self.add_opportunity("Journey searchable")
        self.add_opportunity("Journey too old", min_age="28", max_age="30")
        seeker = self.new_seeker("search@example.com")
        self.assertIn("Journey searchable", self.page(seeker, "/dashboard?q=searchable"))
        self.assertNotIn("Journey searchable", self.page(seeker, "/dashboard?type=TRAINING"))
        self.assertIn("Journey too old", self.page(seeker, "/browse"))

    # ---------- FR7, FR8: save and reminders ----------
    def test_saving_shows_a_reminder_when_14_days_or_less_are_left(self):
        self.add_opportunity("Journey soon", deadline=days_from_today(5))
        seeker = self.new_seeker("save@example.com")
        seeker.post(f"/save/{self.opportunity_id('Journey soon')}")
        saved = self.page(seeker, "/saved")
        self.assertIn("Journey soon", saved)
        self.assertIn("Deadline reminder", saved)
        seeker.post(f"/unsave/{self.opportunity_id('Journey soon')}")
        self.assertNotIn("Journey soon", self.page(seeker, "/saved"))

    # ---------- NFR12: who can do what ----------
    def test_seekers_and_visitors_cannot_open_admin_pages(self):
        seeker = self.new_seeker("roles@example.com")
        self.assertEqual(seeker.get("/admin/opportunities").status_code, 403)
        self.assertEqual(nextfit.app.test_client().get("/admin/users").status_code, 403)

    def test_only_an_admin_can_create_another_admin(self):
        self.admin.post("/admin/users", data={"name": "Second Admin", "email": "second@example.com", "password": "password9"})
        with nextfit.app.app_context():
            self.assertEqual(db.get_user_by_email("second@example.com")["role"], "ADMIN")


if __name__ == "__main__":
    unittest.main()
