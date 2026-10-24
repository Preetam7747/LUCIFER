# SmartHostel — Hackathon Demo Notes

## One-line pitch

**SmartHostel brings daily hostel operations into one calm, traceable workspace—so students know where to go for help and staff can see what needs attention.**

## A 2-minute judge walkthrough

**0:00–0:15 — First impression**
Open `http://127.0.0.1:5000`. Point out the Aurora Oasis theme: deep ocean navy gives the interface structure, mint highlights actions and healthy status, lilac separates secondary actions, and coral is reserved for warmth/attention. The landing page is responsive and does not rely on external CDNs.

**0:15–0:45 — Student experience**
Sign in using a student account (create one from **Get started** first). Show the student dashboard, today's mess menu, assigned room if available, and the complaints/outpass workflows. Submit a short complaint using demo data.

**0:45–1:10 — Staff loop**
Sign out and sign in as `warden` / `Warden123!`. Open Complaints and update the submitted record's status. Explain that the same record is visible to the student on the next visit; the core value is a traceable workflow instead of unstructured messages.

**1:10–1:45 — Resource awareness**
Sign in as `admin` / `1`, open Water Management or Electricity Management, and review meters/readings/thresholds. Add a manual or simulated reading beyond the configured threshold to demonstrate the alert path. Clarify that seeded readings are demo data—not a connection to physical sensors.

**1:45–2:00 — Close with extensibility**
Show the mess payment register and CSV export. Explain the next step: connect real meter hardware and authenticated notification/payment providers, then deploy with a strong secret, HTTPS, backups and production hardening.

## Architecture at a glance

- **Frontend:** Jinja templates, semantic HTML, responsive CSS (`style.css` + `aurora.css`) and a small vanilla JavaScript file for CSRF form fields, mobile navigation, flash-message dismissal, and date-time input convenience.
- **Backend:** Flask routes with student/staff/admin role checks.
- **Persistence:** SQLite, created locally on first run. Passwords are stored as Werkzeug password hashes.
- **Observability:** utility alert records and an audit table for selected administrator actions; CSV export for utility readings.

## What is implemented today

The student/warden/admin dashboards, room allocation, mess menu, mess-payment register, complaints, outpasses, water/electricity meters and readings, utility thresholds/alerts, tariff settings, audit entries, and utility CSV export have Flask routes/templates in the application.

The files inside `design_preview/` are an earlier visual mockup gallery of additional possible modules (for example, a dedicated notification centre and staff/settings screens). They are **not** all connected to live backend routes. Do not present those static mockups as implemented functionality.

## Strong next improvements for a competition submission

1. Add real notice/notification records and show unread items in both dashboards.
2. Add role-managed staff accounts and a proper student profile page.
3. Add tests for authorization, CSRF handling, room capacity, and utility thresholds.
4. Connect hardware telemetry only after defining device identity, time-series ingestion, stale-reading detection, and alert delivery.
5. Use a persistent production secret, secure cookies, HTTPS, login rate limiting, backups, and a production WSGI server before deployment.
