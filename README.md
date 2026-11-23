# MamaTrack

Postpartum follow-up and risk-flagging tool for health centres in Rwanda.

MamaTrack works out each mother's six-week (day 42) postnatal visit date, flags the ones who are
overdue, and lets nurses and community health workers (CHWs) attach a risk indicator so the most
urgent cases sit at the top of the dashboard.

- **Live app:** https://mamatrack.onrender.com

- **Demo video:** https://www.youtube.com/watch?v=0rgDzEf-DXc

- **SRS document:** https://docs.google.com/document/d/1MMfPlAPFU_D9ScDd8JEOuUgbFA9RwwKLRPwfJGu5vLY/edit?usp=sharing



## Quick tour for testers (5 minutes)

1. Open the live app and sign in as `nurse.alice` (password `MamaTrack2026`). The dashboard
   lists mothers by priority: overdue mothers with a risk tag first, in red.
2. Click **Register mother**, pick a delivery date and watch the follow-up date appear
   (delivery + 42 days). Save her.
3. Open an overdue mother, click **Record visit** and save. She moves to **Completed**.
4. Sign out and sign in as `chw.jean`. Turn off Wi-Fi (or use airplane mode on a phone),
   log a visit and see **Pending sync**. Turn Wi-Fi back on and it changes to **Synced**.
5. Sign in as `supervisor` to see both facilities, the **Summary**, the **Users** page and
   **Reset demo data**.

## The problem

Only about 57% of postpartum women in Rwanda receive any postnatal care, yet the first six weeks
after birth are when most maternal deaths from bleeding, infection and high blood pressure happen.
Health centres track follow-up by hand in spreadsheets, so nobody is told when a mother has missed
her visit, and a high-risk case can sit unnoticed in a long list.

## What the prototype does

| SRS | Feature | Where to find it |
|-----|---------|------------------|
| FR1 | Register a mother (name, delivery date, place of delivery, optional phone). Future dates are refused and duplicates are flagged. | Dashboard → **Register mother** |
| FR2 | Follow-up date = delivery date + 42 days, recalculated when the delivery date is corrected. | Registration form preview, profile, dashboard |
| FR3 | Mothers past the due date with no completed visit turn **Overdue** (red). | Dashboard, profile |
| FR4 | Record visit date and outcome (Attended / Referred / Other). The case moves to Completed. | Profile → **Record visit** |
| FR5 | Risk indicators from a fixed list, with an optional 200-character note. | Profile → **Add risk indicator** |
| FR6 | Priority order: overdue + risk, overdue, due soon, on track, completed. Longest overdue first. | Dashboard |
| FR7 | CHW phone view that keeps updates as **Pending sync** while offline and sends them when the network returns. | Sign in as a CHW → **Field visits** |
| FR8 | Login with 8+ character passwords, 15-minute lockout after 5 failed attempts, 15-minute idle sign-out. | `/login` |
| FR9 | Search by name or ID (e.g. `MT-0004`) and filter by Overdue, Due soon, Risk-tagged, Completed. | Dashboard |
| Rule 8 | Two different visits for the same mother go to **Sync review**; nothing is overwritten. | **Sync review** |
| Rule 9 | Each role only sees the actions it is allowed to do. | All pages |

Supervisors also approve sign-up requests, create and disable accounts, correct completed visits
(a reason is required and logged) and see an overdue/risk summary per facility.

## Demo accounts

All demo accounts use the password **`MamaTrack2026`**.

| Username | Role | Facility |
|----------|------|----------|
| `nurse.alice` | Nurse / Midwife | Kacyiru Health Centre |
| `nurse.paul` | Nurse / Midwife | Remera Health Centre |
| `chw.jean` | Community Health Worker | Kacyiru Health Centre |
| `chw.claire` | Community Health Worker | Remera Health Centre |
| `supervisor` | Supervisor / Admin | All facilities |

The demo data is created automatically the first time the app starts with an empty database.
If earlier testers have completed every case, sign in as `supervisor`, open **Users** and use
**Reset demo data** to bring back the original overdue and open cases.

## Tech stack

- Python 3.10+ and Flask 3
- SQLAlchemy with SQLite locally and PostgreSQL in production
- Jinja templates, plain CSS and vanilla JavaScript (no build step)
- Service worker and `localStorage` for the CHW offline queue
- Pytest for the automated tests
- Hosted on Render, database on Neon

## Run it on your computer

### Before you start

You need two free programs:

- **Python 3.10 or newer** from [python.org/downloads](https://www.python.org/downloads/).
  On Windows, tick **"Add python.exe to PATH"** on the first screen of the installer.
- **Git** from [git-scm.com/downloads](https://git-scm.com/downloads).

Open a terminal (Command Prompt, PowerShell or Git Bash on Windows; Terminal on macOS) and
check both are installed:

```bash
python --version
git --version
```

On macOS use `python3` instead of `python` in every command below.

**1. Clone the repository**

```bash
git clone https://github.com/YOUR-GITHUB-USERNAME/mamatrack.git
cd mamatrack
```

**2. Create and activate a virtual environment**

Windows (PowerShell or Command Prompt):

```powershell
python -m venv venv
venv\Scripts\activate
```

Windows (Git Bash):

```bash
python -m venv venv
source venv/Scripts/activate
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

You should now see `(venv)` at the start of your terminal line.

**3. Install the dependencies**

```bash
pip install -r requirements.txt
```

**4. Create your environment file**

Windows (PowerShell or Command Prompt): `copy .env.example .env`  
Git Bash, macOS / Linux: `cp .env.example .env`

The defaults work as they are. Change `SECRET_KEY` to any long random text if you like.

**5. Start the app**

```bash
python run.py
```

Open http://127.0.0.1:5000 in Chrome and sign in with one of the demo accounts above.
Press **Ctrl + C** in the terminal to stop the app.

The SQLite database is created at `instance/mamatrack.db`. Delete that file to start again with
fresh demo data.

**6. Run the tests (optional)**

```bash
pytest
```

All 18 tests should pass. They cover the 42-day due date, the overdue and priority rules,
Rwanda-time dates, login lockout, role restrictions, the demo reset and offline sync without
duplicates.

**Next time**, you only need to open a terminal in the `mamatrack` folder, activate the virtual
environment (step 2, second line only) and run `python run.py`.

### Common problems

| Message | Fix |
|---------|-----|
| `python is not recognized` | Reinstall Python and tick **Add python.exe to PATH**, then open a new terminal. |
| `No module named flask` | The virtual environment is not active. Run the activate command from step 2. |
| `No module named app` when running `pytest` | Run `pytest` from the main `mamatrack` folder, where `pytest.ini` is. |
| `Address already in use` | The app is already running in another terminal. Stop it with **Ctrl + C**. |

## Try the offline mode

The CHW **Field visits** page works without network on laptops and phones. Open it once while
online so the browser can keep a copy, then go offline.

On a laptop (live app or local):

1. While online, sign in as `chw.jean` and press **F5** once on the Field visits page.
2. Turn off Wi-Fi. The banner turns amber and says you are offline.
3. Click **Log visit** on a mother, choose an outcome and save. It shows **Pending sync**.
4. Press **F5**: the page still opens and the visit is still pending.
5. Turn Wi-Fi back on. Within about 15 seconds (or straight away with **Sync now**) it shows
   **Synced**.
6. Sign in as `nurse.alice`: the mother is now **Completed** on the dashboard.

Instead of turning off Wi-Fi you can use Chrome DevTools (F12): set **Network** to **Offline**
and also tick **Offline** under **Application → Service Workers**.

On a phone (live app):

1. Open the live URL in Chrome and sign in as `chw.jean` while connected.
2. Turn on **airplane mode**. The banner turns amber and says you are offline.
3. Log a visit. It shows **Pending sync** and stays on the phone even if you reload the page.
4. Turn airplane mode off. The visit is sent within about 15 seconds and shows **Synced**.

Pages other than Field visits need the network; opened offline they show a short
"You are offline" page with a button back to Field visits. If the 15-minute sign-out happens
while offline, the pending visits are kept and the banner offers a sign-in link to send them.


## Deploy your own copy

1. Fork this repository to your own GitHub account.
2. Sign in to [neon.tech](https://neon.tech) with GitHub and create a project named
   `mamatrack` in the **AWS US West 2 (Oregon)** region.
3. Click **Connect** and copy the connection string (it starts with `postgresql://`).
4. Sign in to [render.com](https://render.com) with GitHub and choose **New → Blueprint**.
5. Connect your copy of the repository. Render reads `render.yaml` and creates a free web
   service called `mamatrack`.
6. Paste the Neon connection string into `DATABASE_URL`. `SECRET_KEY` is generated for you
   and `PYTHON_VERSION` is already set.
7. Click **Deploy Blueprint** and wait for "Your service is live" (3–5 minutes). The app is at
   `https://<service-name>.onrender.com`, with demo data already loaded.

Every push to `main` redeploys automatically. The free Render plan sleeps after 15 minutes
without visitors, so the first page can take up to a minute to load.

## Development workflow

Each change after the first version was made on its own branch and merged into `main`
through a pull request:

| PR | Branch | Change |
|----|--------|--------|
| #1 | `fix/kigali-timezone` | Check dates against Rwanda time instead of the server's UTC clock |
| #2 | `feature/offline-fallback` | Offline page and safe sign-in when the session expires offline |
| #3 | `feature/demo-reset` | Supervisor button to restore the demo data |
| #4 | `fix/chw-buttons-after-reset` | Log visit buttons work again for the CHW after a demo reset |
| #5 | `docs/readme-update` | Live links, tester tour, offline testing and setup help in the README |

The first version was built in 20 small commits, one feature at a time.

## Project structure

```
mamatrack/
├── app/
│   ├── __init__.py       app factory, login guard, idle timeout
│   ├── config.py         settings (42-day rule, lockout limits, timezone)
│   ├── clock.py          today's date in Rwanda time
│   ├── models.py         Facility, User, Mother, Visit, RiskIndicator, AuditLog
│   ├── status.py         due date, overdue rule and dashboard priority
│   ├── permissions.py    role rules from SRS Rule 9
│   ├── risks.py          risk indicator list (one place to add new ones)
│   ├── validators.py     form checks
│   ├── auth.py           login, sign-up, logout
│   ├── mothers.py        dashboard, registration, profile, edit
│   ├── visits.py         visits, risk tags, sync review
│   ├── chw.py / sync.py  CHW field page and offline sync rules
│   ├── admin.py          users and summary report
│   ├── seed.py           demo data and reset
│   ├── templates/        HTML pages
│   └── static/           CSS, JavaScript, logo and the offline page
├── tests/
├── pytest.ini
├── render.yaml
└── run.py
```

## Known limitations

- SMS reminders are outside the scope of this prototype, as stated in the SRS.
- Overdue status is worked out live every time a page loads instead of by a midnight job, so it
  is never out of date.
- Kinyarwanda is used for the main labels only.
- The prototype covers a small set of facilities; multi-district rollout is future work.

## Author

Monique Niyobyose