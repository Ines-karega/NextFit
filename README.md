# NextFit

NextFit is a website that helps young Rwandans (aged 16 to 30) find the trainings, internships and jobs they
already qualify for. A seeker fills in a short profile, and NextFit shows a personal list of opportunities that
match their age, education level and skills, with the closest deadlines first, opportunities in their own
district first, and a clear explanation of why each one matched.

## Links

| What | Link |
|------|------|
| Live website | https://nextfit.karega.tech |
| Demo video | _add link_ |
| Code | https://github.com/Ines-karega/NextFit |

## Contents

1. [What NextFit does](#1-what-nextfit-does)
2. [How the matching works](#2-how-the-matching-works)
3. [Use the live website, step by step](#3-use-the-live-website-step-by-step)
4. [Run NextFit on your own computer, step by step](#4-run-nextfit-on-your-own-computer-step-by-step)
5. [Run the automated tests](#5-run-the-automated-tests)
6. [Where each SRS requirement is in the app](#6-where-each-srs-requirement-is-in-the-app)
7. [How the live website is hosted](#7-how-the-live-website-is-hosted)
8. [Password reset emails](#8-password-reset-emails)
9. [Troubleshooting](#9-troubleshooting)
10. [Project files](#10-project-files)
11. [Scope and design choices](#11-scope-and-design-choices)
12. [Planned for later](#12-planned-for-later)

---

## 1. What NextFit does

The problem. Many trainings, internships and youth employment programmes already exist in Rwanda, but young
people often hear about them too late, or have to search long lists and guess which ones they qualify for.

The solution. NextFit does the checking for them. There are two kinds of users:

| User | What they can do |
|------|------------------|
| Seeker | Sign up, fill in a profile, see their matches with the reasons, search and filter them, browse every open opportunity, save opportunities, get a reminder when a saved deadline is close, and reset a forgotten password. |
| Admin | Add, edit, close and remove opportunities, see who added each one, view and remove user accounts, and create other admin accounts. Admins cannot sign up on the website: only an existing admin can create another. |

Built with: Python and Flask for the server, HTML, CSS and JavaScript for the pages, and SQL for the data
(SQLite on your own computer, PostgreSQL on the live website).

## 2. How the matching works

An opportunity appears in a seeker's My matches list only when all three of these are true:

1. Age: the seeker's age is inside the opportunity's age range.
2. Education: the seeker's education level is one the opportunity accepts.
3. Skills: the seeker has at least one of the required skills, or the opportunity needs none.

Then:

- Expired or closed opportunities are never shown to seekers.
- Matches in the seeker's own district come first, then other districts. District never hides a match.
- Inside each group, the closest deadline comes first, and each card shows how many days are left.
- Each card explains why it matched: the age and education rules met, the skills the seeker has, and the
  skills they are missing. It is labelled a Full skill match (has every required skill) or a
  Partial skill match (has some).

Skills are typed with a comma between each one, for example `Excel, Accounting, Customer service`.

## 3. Use the live website, step by step

Open https://nextfit.karega.tech. It works on a computer and on a phone (on a phone, tap Menu at the top).

Who can use what on the live website:

- Anyone can use it as a seeker: just sign up with your own email (step 1 below). No demo account is needed.
- The admin pages are only for the website's admins, because an admin can change the listings. Admin accounts
  for the live website are given privately to the people who need them. To try the admin side yourself, run
  NextFit on your own computer (section 4), which comes with a demo admin account.

### As a seeker

1. Press Create my free profile, then enter your name, email and a password (at least 8 characters, with at
   least one letter and one number).
2. Fill in your profile: age, province, district, education level, your current situation and your skills.
   Press Save profile.
3. My matches opens. Read why each opportunity matched, the days left, and whether it is in your district.
4. Use the search box and the type, province and district filters to narrow the list.
5. Press Read the full advert to see the employer's original advert, and Apply (or
   Copy email address when the opportunity is applied for by email).
6. Press Save to keep an opportunity in Saved. When its deadline is 14 days away or less, a
   deadline reminder appears on your pages.
7. Open Browse all to see every open opportunity, including ones you do not fully qualify for, with what is
   missing.
8. Change your details any time in Profile; your matches update straight away.
9. Forgot your password? On the Log in page, press Forgot your password? and enter your email. A reset
   link arrives by email (check spam too) and works for 1 hour.

### As an admin

1. Log in with an admin account. The menu shows Opportunities and Users.
2. Add an opportunity: open Opportunities, press Add opportunity, and fill in the details, including
   who it is for (age range, accepted education levels and required skills) and, if the opportunity is applied for
   by email or phone, a link to the full advert. Press Save. It reaches every seeker who qualifies.
3. Keep the list up to date: the list shows who added each opportunity. Listings whose deadline has passed are
   marked Deadline passed (seekers no longer see them). Use Edit, Close or Remove on any row.
4. Manage users: open Users to see every account and remove one, or to create another admin.

To test password reset yourself: sign up as a seeker with your own email address, then use
Forgot your password? on the login page.

## 4. Run NextFit on your own computer, step by step

Requirements: Python 3.10 or newer, and Git.

1. Clone the repository:
   ```
   git clone https://github.com/Ines-karega/NextFit.git
   cd NextFit
   ```
2. Create and activate a virtual environment:

   Windows (PowerShell):
   ```
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```
   If script execution is blocked, run `Set-ExecutionPolicy -Scope Process Bypass` first.

   Mac or Linux:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Start the server:
   ```
   python backend/app.py
   ```
5. Open http://127.0.0.1:5000 in your browser and use the website. Keep the terminal open while you do.
6. When you have finished, stop the server by pressing Ctrl + C in the terminal.

No configuration is needed. On first start, NextFit creates a SQLite database (`nextfit.db`), a demo admin, a
demo seeker, and loads the listings from `backend/real_opportunities.csv`.

To run NextFit again later, you don't need to repeat every step. Open a terminal in the `NextFit` folder,
activate the virtual environment (the second line of step 2), then start the server (step 4).

### Demo accounts on your computer

These accounts work only on a copy running on your own computer. They do not work on the live website.
On the live website, sign up as a seeker with your own email instead (see section 3).

| Role | Email | Password | What to try |
|------|-------|----------|-------------|
| Seeker | `seeker@nextfit.rw` | `Seeker123!` | My matches, the reasons, search, saving and reminders |
| Admin | `admin@nextfit.rw` | `Admin123!` | Adding, editing and closing opportunities, and Users |

You can also press Sign up to make your own seeker account.

### Try a whole journey

1. Log in as the admin and add an opportunity in Kigali City, Gasabo (the demo seeker's district), for
   Bachelor's graduates aged 18 to 30 needing `Excel`.
2. Log out and log in as the seeker (or sign up a new one with Bachelor's and `Excel`).
3. Open My matches: the new opportunity is there, with the reasons it matched.
4. Press Save, then open Saved. If the deadline is 14 days away or less, you see a deadline reminder.

Password reset on your computer: no email is sent. After Forgot your password?, the reset link is printed in
the terminal where the server is running, so you can still try it (see section 8).

To start again with a fresh database: stop the website, delete `nextfit.db`, and start it again.

## 5. Run the automated tests

The tests check the matching rules and walk through the main pages: sign up, login, password reset, profile,
matches, search, browse, saving, reminders and the admin pages. They use a temporary practice database, so your
own `nextfit.db` and the live website are never touched, and no emails are sent.

With the virtual environment activated, from the project folder, run:
```
python -m unittest discover tests
```
The last line should say `OK`.

## 6. Where each SRS requirement is in the app

| SRS requirement | Where to find it |
|-----------------|------------------|
| FR 1.1 Sign up | Create my free profile on the home page |
| FR 1.2 Log in | Log in in the menu |
| FR 1.3 Reset password | Log in, then Forgot your password? |
| FR 2.1, 2.2 Create and edit profile | Profile in the menu |
| FR 3.1 Add opportunity | Admin: Opportunities, then Add opportunity |
| FR 3.2, 3.3 Edit and close opportunity | Admin: Edit and Close on each row of Opportunities |
| FR 4.1 to 4.4 Matching, explanation, full or partial skill match | My matches: each card's "Why this matched you" |
| FR 4.2 Hide expired opportunities | Automatic; the admin's list marks them Deadline passed |
| FR 5.1 to 5.3 Deadline order, days left, own district first | My matches |
| FR 6.1 to 6.3 Search and filters | The search box and filters on My matches |
| FR 7.1, 7.2 Save and remove | Save on a card, and Saved in the menu |
| FR 8.1 Deadline reminder | On My matches, Saved and the home page |
| FR 9.1 Browse all | Browse all in the menu |
| FR 10.1 Manage users | Admin: Users |
| FR 10.2 Manage opportunities | Admin: Opportunities (edit, close, remove) |
| NFR 1 Safety reminder | The "Stay safe" note on every opportunity |
| NFR 2 Security | Passwords are stored scrambled (hashed), the live site uses HTTPS, and each role only sees its own pages |
| NFR 4 Phone friendly | The Menu button on phones; no page needs sideways scrolling |
| NFR 5 Clear messages | Messages under each field, friendly error pages, and "No matches yet" with a link to Browse all |
| NFR 9 Privacy | The profile page explains why each detail is asked for |

## 7. How the live website is hosted

The live website is already set up and running at https://nextfit.karega.tech. You don't need to do anything to
use it. For reference, it uses three free services:

| Service | What it does for NextFit |
|---------|--------------------------|
| Vercel | Runs the website. Every change merged into the `main` branch on GitHub goes live automatically. |
| Neon | Stores the live data in a PostgreSQL database. Free hosting does not keep files, so the live website cannot use `nextfit.db`; the same code uses PostgreSQL when the `DATABASE_URL` setting exists. |
| Brevo | Sends the password reset emails from `noreply@karega.tech`. |

Private settings such as the database address and the email key are stored in Vercel, never in the code.

## 8. Password reset emails

On the live website, when someone presses Forgot your password?, NextFit emails them a link to choose a new
password. The link works for 1 hour.

On a copy running on your own computer, no email is sent. Instead, the link is printed in the terminal where the
server is running, so a developer can still try the whole reset. The link is never shown on the website itself,
so on the live website only the owner of the email address can reset the password.

## 9. Troubleshooting

| Problem | What to do |
|---------|------------|
| Windows refuses to turn on the virtual environment (a red message about running scripts) | Run `Set-ExecutionPolicy -Scope Process Bypass`, then activate it again (step 2) |
| `python` is not recognised | Use `py` (Windows) or `python3` (Mac or Linux), or reinstall Python with "Add python.exe to PATH" ticked |
| The browser says "This site can't be reached" on 127.0.0.1:5000 | The server is not running: start it again (step 4) and keep the terminal open |
| The page looks old after an update | Press Ctrl + F5 to reload it fully |
| "This email already has an account" | Log in instead, or use Forgot your password? |
| The reset email did not arrive | Check the spam folder. On your own computer no email is sent: the link is printed in the terminal instead |
| You want to start again | Stop the website, delete `nextfit.db`, and start it again |

## 10. Project files

```
NextFit/
  backend/                  Python code that runs on the server
    app.py                  All the pages: sign up, log in, profile, matches, saved, admin
    matching.py             The three matching rules and the "why this matched you" explanation
    db.py                   The only file that talks to the database (SQLite or PostgreSQL)
    emailer.py              Sends the password reset email
    seed.py                 Loads the starting listings and, on your computer, the demo accounts
    rwanda.py               Provinces, districts, education levels and other fixed lists
    real_opportunities.csv  The starting list of real opportunities, with the source of each one
  frontend/
    templates/              The HTML pages
    static/style.css        The look of the website
    static/app.js           The district list, the phone Menu button, Show password and Copy email address
  tests/
    test_matching.py        Tests for the matching rules
    test_journeys.py        Tests that walk through the main pages
  requirements.txt          The libraries to install
  wsgi.py                   The starting point Vercel uses for the live website
```

## 11. Scope and design choices

- Matching uses three rules. Only age, education and skills decide whether an opportunity is shown, as set in
  the SRS (FR 4.1). District changes the order but never hides a match. When an advert also asks for years of
  experience, its description says so, and the employer judges it.
- Skills are compared by their words. Capital letters never matter, and a skill counts as the same when all its
  words appear in the other one: "Excel" matches "MS Excel", and "Customer service" matches "Excellent customer
  service". Seekers write their own skills, and the employer checks them during their own application process.
- Admins add every opportunity. As set in the SRS for this version (section 2.5), listings are entered by an
  admin from real adverts, each with a link to the original. When an advert names the province but not the
  district (for example it only says "Kigali"), the listing says "district not stated". It is still shown to
  everyone it matches, but never as being in a seeker's own district.
- Expired opportunities are hidden automatically. Seekers never see an opportunity after its deadline (FR 4.2).
  In the admin's list it is marked Deadline passed, so an admin can close or remove it (FR 3.3).
- Emails are checked for a complete format (for example `name@gmail.com`). NextFit does not send a confirmation
  email at sign-up, so it cannot know whether a correctly written address really exists. Password reset links
  only ever go to the registered address, so an account can only be recovered by whoever owns that inbox.
  Capital letters in an email address don't matter: NextFit saves and compares addresses in lowercase.
- The website is in English, as set in the SRS (section 2.5).

## 12. Planned for later

As listed in the SRS: a mobile app, SMS reminders, and collecting opportunities automatically from partner
websites.
