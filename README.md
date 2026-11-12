# MamaTrack

Postpartum follow-up and risk-flagging tool for health centres in Rwanda.

MamaTrack works out each mother's six-week (day 42) postnatal visit date, flags the ones who are
overdue, and lets nurses and community health workers (CHWs) attach a risk indicator so the most
urgent cases sit at the top of the dashboard.

- **Live app:** https://mamatrack.onrender.com
- **Demo video:** _add link_
- **SRS document:** _add link_

![Dashboard](docs/screenshots/dashboard.png)

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

## Tech stack

- Python 3.10+ and Flask 3
- SQLAlchemy with SQLite locally and PostgreSQL in production
- Jinja templates, plain CSS and vanilla JavaScript (no build step)
- Service worker and `localStorage` for the CHW offline queue
- Pytest for the automated tests
- Hosted on Render, database on Neon

## Run it on your computer

You need **Python 3.10 or newer** and **Git**. Check with:

```bash
python --version
git --version
```

**1. Clone the repository**

```bash
git clone https://github.com/<your-username>/mamatrack.git
cd mamatrack
```

**2. Create and activate a virtual environment**

Windows (PowerShell):

```powershell
python -m venv venv
venv\Scripts\activate
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

Windows: `copy .env.example .env`  
macOS / Linux: `cp .env.example .env`

The defaults work as they are. Change `SECRET_KEY` to any long random text if you like.

**5. Start the app**

```bash
python run.py
```

Open http://127.0.0.1:5000 in Chrome and sign in with one of the demo accounts above.
The SQLite database is created at `instance/mamatrack.db`. Delete that file to start again with
fresh demo data.

**6. Run the tests (optional)**

```bash
pytest
```

## Try the offline mode

1. Sign in as `chw.jean`.
2. Open Chrome DevTools (F12) → **Network** → change *No throttling* to **Offline**.
3. Tap **Log visit** on a mother and save. The update shows **Pending sync**.
4. Switch the network back to *No throttling*. Within a few seconds it changes to **Synced**.
5. Sign in as `nurse.alice`: the mother is now **Completed** on the dashboard.

<img src="docs/screenshots/chw-offline.png" alt="CHW field view while offline" width="300">

## Deploy your own copy

1. Create a free PostgreSQL database at [neon.tech](https://neon.tech) and copy its connection
   string (it starts with `postgresql://`).
2. Sign in to [render.com](https://render.com) with GitHub and choose **New → Blueprint**.
3. Pick this repository. Render reads `render.yaml` and creates the web service.
4. When asked for `DATABASE_URL`, paste the Neon connection string. `SECRET_KEY` is generated for you.
5. Click **Apply** and wait for the build to finish. Your app is live at
   `https://<service-name>.onrender.com`, with demo data already loaded.

The free Render plan sleeps after 15 minutes without visitors, so the first page can take
up to a minute to load.

## Project structure

```
mamatrack/
├── app/
│   ├── __init__.py       app factory, login guard, idle timeout
│   ├── config.py         settings (42-day rule, lockout limits)
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
│   ├── seed.py           demo data
│   ├── templates/
│   └── static/
├── tests/
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

Monique Niyobyose, African Leadership University, Software Engineering