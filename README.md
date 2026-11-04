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
