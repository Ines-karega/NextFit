# NextFit

A web platform that helps Rwandan youth (16-30) find the trainings, internships and jobs they already qualify for.
It matches a seeker's **age, education level and skills** against each opportunity's eligibility rules, shows the
**closest deadlines first**, puts opportunities in the seeker's **own district first**, and **explains why** each one matched.

Built from the NextFit Software Requirements Specification (SRS). Tools: Python, Flask, SQLite, HTML, CSS, JavaScript.

- **Live site:** _add your public URL here after deploying_
- **Demo video:** _add link_
- **SRS:** _add link_

## What you can do

**Seeker:** sign up, log in, reset a forgotten password, fill in and edit a profile, see personal matches with
explanations (full/partial skill match, days left), search and filter matches, browse all open opportunities, save and
remove opportunities, see in-app reminders when a saved deadline is 14 days away or less.

**Admin:** add, edit, close and remove opportunities (with age range, accepted education levels and required skills),
view and remove user accounts, create other admin accounts.

## Run it on your computer (every step)

You need **Python 3.10 or newer**. Download it from https://www.python.org/downloads/ and, in the installer,
tick **"Add python.exe to PATH"**.

1. Download the code and open a terminal in the project folder:
   ```
   git clone https://github.com/YOUR-USERNAME/NextFit.git
   cd NextFit
   ```
2. Create a virtual environment (a private box for this project's libraries):
   ```
   python -m venv venv
   ```
3. Turn it on.
   - Windows (PowerShell): `venv\Scripts\Activate.ps1`
   - Windows (Command Prompt): `venv\Scripts\activate.bat`
   - Mac / Linux: `source venv/bin/activate`

   (If PowerShell blocks it, run `Set-ExecutionPolicy -Scope Process Bypass` first, then try again.)
4. Install the libraries:
   ```
   pip install -r requirements.txt
   ```
5. Start the website:
   ```
   python backend/app.py
   ```
6. Open http://127.0.0.1:5000 in your browser.

The database file `nextfit.db` is created automatically the first time, with 22 sample opportunities.
To start fresh, stop the server, delete `nextfit.db`, and start again.

## Demo accounts

| Role | Email | Password |
|------|-------|----------|
| Seeker (profile already filled in) | seeker@nextfit.rw | Seeker123! |
| Admin | admin@nextfit.rw | Admin123! |

Or click **Sign up** to make your own seeker account. Admins cannot sign up publicly (SRS FR1.1): the first admin is
created by the program on first start, and only an admin can create more.

## Turn on password reset emails (optional on your computer, needed on the live site)

NextFit sends the email through any free SMTP service. The easiest is a Gmail account:

1. In your Google account turn on **2-Step Verification**, then create an **App password**
   (Google Account > Security > App passwords). Copy the 16-letter password.
2. Set these four settings before starting the site (never write them inside the code or upload them to GitHub).

   Windows PowerShell:
   ```
   $env:SMTP_HOST = "smtp.gmail.com"
   $env:SMTP_PORT = "587"
   $env:SMTP_USER = "your.address@gmail.com"
   $env:SMTP_PASSWORD = "your-16-letter-app-password"
   python backend/app.py
   ```
   Mac / Linux: use `export SMTP_HOST=smtp.gmail.com` and so on.
   On a hosting site (such as Render), add the same four names under **Environment variables**.
3. Open **Log in > Forgot your password?**, type an account's email, and check that inbox.

## Important notes

- The 22 opportunities are **sample data** (links go to example.org). Their deadlines are set relative to today so the
  demo always has open opportunities. One has an expired deadline on purpose, to show that expired ones stay hidden.
- **Forgot password:** the reset link is **emailed** to the user and works for 1 hour. This needs the email settings
  below. If they are not set (for example when you just run it on your computer), the link is shown on the screen
  instead ("demo mode") so you can still try it.
- Before going live, set a private `SECRET_KEY`, and `ADMIN_EMAIL` / `ADMIN_PASSWORD` for the first admin.
  Set `NEXTFIT_SEED=0` to skip the sample data.

## Files

**`backend/`** (Python, runs on the server)

| File | What it does |
|------|--------------|
| `app.py` | All the pages (routes): sign up, log in, profile, dashboard, saved, admin |
| `matching.py` | The matching rules and the "why you matched" explanation |
| `db.py` | Creates the SQLite tables and the first admin |
| `emailer.py` | Sends the password reset email |
| `seed.py` | The sample opportunities and demo seeker |
| `rwanda.py` | Provinces, districts and fixed lists (education levels, types) |

**`frontend/`** (what the user sees in the browser)

| Folder | What it has |
|--------|-------------|
| `templates/` | The HTML pages |
| `static/` | `style.css` (the look) and `app.js` (fills the district list) |

Other files in the main folder: `requirements.txt` (libraries to install), `nextfit.db` (created automatically).

## Not in this prototype (planned for later, as in the SRS)

Mobile app, SMS reminders, automatic collection of opportunities from other sites.
