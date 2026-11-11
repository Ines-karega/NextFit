# NextFit

A web platform that helps Rwandan youth (16-30) find the trainings, internships and jobs they already qualify for.
It matches a seeker's **age, education level and skills** against each opportunity's eligibility rules, shows the
**closest deadlines first**, puts opportunities in the seeker's **own district first**, and **explains why** each one matched.

Built from the NextFit Software Requirements Specification (SRS). Tools: Python, Flask, SQLite, HTML, CSS, JavaScript.
On the live site the same code stores its data in PostgreSQL (see "Put it online" below).

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

The database file `nextfit.db` is created automatically the first time. It is filled with the real listings in
`backend/real_opportunities.csv` when that file has rows, and with 22 sample opportunities when it does not.
To start fresh, stop the server, delete `nextfit.db`, and start again.

## Demo accounts

| Role | Email | Password |
|------|-------|----------|
| Seeker (profile already filled in) | seeker@nextfit.rw | Seeker123! |
| Admin | admin@nextfit.rw | Admin123! |

Or click **Sign up** to make your own seeker account. Admins cannot sign up publicly (SRS FR1.1): the first admin is
created by the program on first start, and only an admin can create more.

These two demo accounts and the sample listings only exist on your own computer. The live site never creates them.

## Put it online (free): Render + Neon + Brevo

Free hosting deletes local files whenever the site restarts, so a SQLite file would lose its data there.
On the live site NextFit therefore keeps its data in a free PostgreSQL database. Nothing in the code needs
changing: when the `DATABASE_URL` setting exists, PostgreSQL is used; when it does not, SQLite is used.

1. **Database (Neon).** Create a free account at neon.com and a project in the **Frankfurt** region.
   Copy the **pooled connection string** (it starts with `postgresql://`).
2. **Email (Brevo).** Follow "On the live site: Brevo" in the next section to get an API key.
3. **Website (Render).** Put the code on GitHub, then in Render choose **New > Blueprint** and pick the
   repository. Render reads `render.yaml` and asks for these values:

   | Name | Value |
   |------|-------|
   | `DATABASE_URL` | the connection string from Neon |
   | `ADMIN_EMAIL` / `ADMIN_PASSWORD` | the first admin account. Choose a strong password. |
   | `BREVO_API_KEY` / `EMAIL_FROM` | from step 2, e.g. `noreply@karega.tech` |

   The site refuses to start without `ADMIN_PASSWORD`, so there is never a live admin with a known password.
4. **Your own address.** In Render open the site's **Settings > Custom Domains**, add `nextfit.karega.tech`,
   and create the CNAME record it shows in your domain's DNS settings. Render adds HTTPS by itself.
5. **Keep it awake.** Follow "Keep the live site awake" below.

On first start the live site creates the tables, the first admin, and loads the real listings from
`backend/real_opportunities.csv`. After that, the admin adds and edits opportunities on the website.

## Turn on password reset emails (optional on your computer, needed on the live site)

NextFit can send the email in two ways. If both are set up, Brevo is used.

### On the live site: Brevo (free, 300 emails a day, reaches any email address)

Brevo sends over normal HTTPS, so it works on hosts that block the usual email ports (such as Render's free plan).

1. Create a free account at brevo.com.
2. In Brevo, add and verify your domain (**Senders, Domains & Dedicated IPs > Domains**) by copying the DNS records
   it shows into your domain's DNS settings. This lets you send from an address such as `noreply@karega.tech`
   and keeps the emails out of spam folders.
3. Create an API key (**SMTP & API > API Keys**).
4. On the hosting site, add these under **Environment variables** (never write them inside the code):

   | Name | Value |
   |------|-------|
   | `BREVO_API_KEY` | the API key from step 3 |
   | `EMAIL_FROM` | the sending address on your domain, e.g. `noreply@karega.tech` |
   | `EMAIL_FROM_NAME` | optional, the sender name people see (default `NextFit`) |

5. If emails are refused, check **Security > Authorised IPs** in Brevo: it can block requests from servers it does
   not know. The reason for any failure is printed in the hosting site's logs.

### On your computer: a Gmail account (SMTP)

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
3. Open **Log in > Forgot your password?**, type an account's email, and check that inbox.

## Keep the live site awake (free hosting plans)

Render's free plan pauses the site after 15 minutes without visitors, and waking it takes about a minute.
A free monitor that visits the site every 5 minutes stops that from happening:

1. Create a free account at uptimerobot.com.
2. Click **New monitor**, choose **HTTP(s)**, and enter the site address followed by `/health`
   (for example `https://nextfit.karega.tech/health`).
3. Set the interval to **5 minutes** and save.

UptimeRobot also emails you if the site ever goes down.

## Important notes

- The 22 sample opportunities are **sample data** (links go to example.org). Their deadlines are set relative to today so the
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
| `db.py` | The only file that talks to the database: creates the tables and the first admin, and reads and saves everything |
| `emailer.py` | Sends the password reset email |
| `seed.py` | Loads the real listings from `real_opportunities.csv`, or the sample opportunities and demo seeker |
| `rwanda.py` | Provinces, districts and fixed lists (education levels, types) |

**`frontend/`** (what the user sees in the browser)

| Folder | What it has |
|--------|-------------|
| `templates/` | The HTML pages |
| `static/` | `style.css` (the look) and `app.js` (fills the district list) |

Other files in the main folder: `requirements.txt` (libraries to install), `render.yaml` (settings for the live
site), `nextfit.db` (created automatically on your computer).

## Not in this prototype (planned for later, as in the SRS)

Mobile app, SMS reminders, automatic collection of opportunities from other sites.
