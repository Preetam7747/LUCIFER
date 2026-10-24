# SmartHostel — Aurora Oasis Edition

A responsive Flask + SQLite hostel-management prototype designed for a clear, polished hackathon demo. The visual direction pairs **deep ocean navy** with **luminous mint**, **soft lilac**, and a restrained **coral** accent. CSS effects are local and CSS-only; the app does not depend on external font, image, or JavaScript CDNs.

## What's included

- **Public product landing page** with a clear call to action and an illustrated in-product preview.
- **Role-aware dashboards** for students, wardens, and administrators.
- **Room and bed allocation** with availability checks and a student directory search.
- **Mess menu** management and history, plus an administrator mess subscription/payment register.
- **Complaints** with student submission and staff status updates.
- **Outpasses** with approve/reject workflow and departure/return events.
- **Water and electricity monitoring** with meters, manual/simulated readings, thresholds, alerts, and audit records.
- **CSV export** for utility readings.
- Responsive layouts, visible focus styles, reduced-motion support, horizontally scrollable tables on small screens, flash-message dismissal, session CSRF checks, and password hashing.
- `HACKATHON_DEMO.md`: a short demo script, architecture notes, and honest scope notes.
- `design_preview/`: an earlier visual concept gallery with sample screen previews. It illustrates additional ideas; those static concepts are not all implemented as routes in the Flask app.

## Run on Windows (recommended)

1. Extract the ZIP to a normal folder, for example `C:\SmartHostel`.
2. Open the extracted `SmartHostel` folder in VS Code (the folder containing `app.py` and `requirements.txt`).
3. Open **Terminal → New Terminal** and run:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   python app.py
   ```

4. Open **http://127.0.0.1:5000**. The new landing page appears first; click **Sign in** to enter a workspace.

A convenience launcher, `run_windows.bat`, is also included. It creates a local virtual environment if needed, installs requirements, and starts the app for local development.

If PowerShell blocks virtual-environment activation, use Command Prompt and run `venv\Scripts\activate.bat`. If the `python` command is not recognized, install Python 3.10+ and enable **Add Python to PATH** during setup.

## Run the smoke tests

After installing the requirements, run:

```powershell
python -m unittest discover -s tests -v
```

The smoke tests cover the landing/auth pages, administrator and warden page access, student registration/workspace, and rejection of a POST without a CSRF token.

## Local demo accounts

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `1` |
| Warden | `warden` | `Warden123!` |

These intentionally simple accounts are only for a local demo. **Change/remove them before any deployment** and configure a strong `SMARTHOSTEL_SECRET` environment variable. Do not expose this demo publicly with the default accounts. The application starts with Flask debug mode off; set `FLASK_DEBUG=1` only for local development.

## What is real vs. simulated

- User accounts, rooms, allocations, complaint/outpass records, menu changes, payment entries, meter readings, threshold alerts, and audit records are persisted to the local SQLite database.
- Meter records seeded by the app are labeled as demo meters. Reading sources distinguish manual, simulated, and hardware records; real hardware must be integrated before describing this as live IoT telemetry.
- Water/electricity charges are estimates based on the configured rates, not official bills.
- The “present/outside” dashboard figures are based on recorded departure/return events, not physical-presence tracking.
- SMS, email, push notifications, online payments, and external identity providers are not configured in this prototype.

## Data and security notes

- `smarthostel.db` is created next to `app.py` on first launch. Back it up before experimenting with real records. Do not put a real database in a public repository.
- Set `SMARTHOSTEL_DB_PATH` to use a different database file (useful for tests or a demo copy).
- Set `SMARTHOSTEL_SECRET` to a stable, strong secret for any shared environment. Without it, a random local secret is generated at process start, so all sessions are invalidated when the app restarts.
- The app has basic route-level role checks, password hashing, form-session CSRF checks, and input validation. Before production use, add stronger account provisioning, login rate limiting, security logging/review, backups, migrations, HTTPS, secure cookie settings, and deployment configuration.

## Useful demo path

For a 2–3 minute demo, use the flow in `HACKATHON_DEMO.md`: show the landing page, sign in as a student, submit a complaint or outpass request, switch to a staff account to update it, then demonstrate the utility threshold workflow as admin.
