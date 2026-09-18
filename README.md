# TELDEM AI Platform

**AI that Sees. Thinks. Protects. Informs.**
Smarter Spaces. Safer Lives.

A production-structured Django application for TELDEM Technologies: a
public marketing site plus a working product (accounts, device
management, simulated sensor telemetry, an AI alert engine, and
subscription billing) for a Nigerian smart-monitoring hardware + AI
platform.

> Hardware doesn't exist yet, so the sensor layer is simulated — but the
> software behaves exactly as it would with real devices: pairing,
> telemetry, thresholds, alerts, history and billing are all real,
> working code.

---

## Stack

- **Backend:** Django 5, Python 3.13
- **Database:** SQLite by default (zero-config); Postgres via `DATABASE_URL`
- **Frontend:** Tailwind CSS (CLI build) + vanilla JS + Chart.js (device history)
- **Simulation:** a management command (`simulate_readings`) + a lightweight
  APScheduler-based runner (`run_scheduler`) — no Redis/Celery required
- **Static files:** WhiteNoise

## Project layout

```
config/                 Django project settings, URLs
apps/
  accounts/             Custom User, Organization, Membership, auth views
  devices/              Device, SensorReading, registration, simulation, constants
  alerts/                Alert model + threshold engine
  billing/               SubscriptionPlan, Subscription, plan selection
  dashboard/             Authenticated overview dashboard
  marketing/             Public site, contact form, blog, error pages, demo data seeding
templates/               All HTML templates (base, marketing, accounts, devices, alerts, billing, dashboard)
static/                  Images (logo/favicon placeholders), compiled CSS, JS
static_src/css/          Tailwind source (input.css)
```

---

## 1. Setup

```bash
# from the project root
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux
```

`.env` defaults to SQLite and DEBUG=True, so the app runs with **zero
extra configuration**. To use Postgres instead, set `DATABASE_URL` in
`.env` (e.g. `postgres://user:pass@localhost:5432/teldem`).

### Postgres (shared dev database)

Local dev currently points at a shared Neon Postgres instance also used
by other projects on this machine (e.g. "caster"). To avoid table-name
collisions (both are Django apps with an `accounts.User` model, etc.),
TELDEM's tables live in their own **Postgres schema** (`teldem`) inside
that shared database rather than the default `public` schema — see the
`DATABASES` block in `config/settings.py`, which appends
`-c search_path=teldem,public` to the connection options whenever
`DATABASE_URL` points at Postgres.

Two things to know if you touch this:

- **Use Neon's unpooled (direct) host**, not the `-pooler` one. Neon's
  PgBouncer pooler rejects the `search_path` startup parameter this
  relies on (`unsupported startup parameter in options: search_path`) —
  Neon's own fix is to use the direct connection for anything that needs
  session-level parameters like this.
- This shared database is for **development convenience only**. Before
  a real deployment, point `DATABASE_URL` at a dedicated Postgres
  database for TELDEM (Neon or otherwise) rather than this shared one.

### Frontend (Tailwind)

```bash
npm install
npm run build-css      # one-off build -> static/css/tailwind.css
# npm run watch-css     # rebuild on change, while developing
```

The compiled CSS is git-ignored by design — always run `build-css`
after cloning or after editing any template/`static_src/css/input.css`.

### Database

```bash
python manage.py migrate
python manage.py createsuperuser     # optional — seed_demo_data creates one for you
```

### Demo data (recommended)

```bash
python manage.py seed_demo_data
```

This creates subscription plans, a superuser, a demo individual account,
a demo organization with three team members (owner/admin/viewer), a
realistic device fleet for both, **48 hours of historical sensor
readings**, alerts raised from real threshold breaches, and a few
published blog posts. Safe to re-run at any time.

**The live/deployed database ships clean, without this demo data** —
seeding is opt-in for local development and demos only. To remove the
seeded demo accounts/devices/readings/alerts/subscriptions/blog posts
at any point (e.g. before a real launch), run:

```bash
python manage.py clear_demo_data
```

This keeps the `admin` superuser (so you aren't locked out of
`/admin/`) and the `SubscriptionPlan` rows (real pricing-tier
configuration, not fake data) — everything else seeded goes. Pass
`--include-admin` to remove the seeded superuser too, once you've
created your own.

### Run it

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`.

---

## 2. Demo login credentials

| Role | Username / Email | Password |
|---|---|---|
| Django admin (superuser) | `admin` | `TeldemAdmin2026!` |
| Individual (B2C) account | `demo.household@teldem.ai` | `TeldemDemo2026!` |
| Organization owner (B2B) | `demo.business@teldem.ai` | `TeldemDemo2026!` |
| Organization admin | `demo.manager@teldem.ai` | `TeldemDemo2026!` |
| Organization viewer | `demo.staff@teldem.ai` | `TeldemDemo2026!` |

Login accepts either the **username** or the **email** shown above.

**Change or disable these before any real deployment** — they are seed
data for demos only.

---

## 3. Running the sensor simulator

Real TELDEM hardware doesn't exist yet, so telemetry is generated by
`simulate_readings`, which produces one realistic reading per metric for
every online device (a random walk around a "normal" value, with
occasional excursions outside the safe range) and runs every reading
through the same alert engine real hardware data would use.

**One-off run:**

```bash
python manage.py simulate_readings
```

**Keep it running continuously** (in-process scheduler, no Celery/Redis needed):

```bash
python manage.py run_scheduler --interval-seconds 60
```

In production, prefer an OS-level scheduled task instead of
`run_scheduler` (which is a convenience for local/demo use):

- **cron:** `* * * * * /path/to/venv/bin/python manage.py simulate_readings`
- **Windows Task Scheduler:** run `venv\Scripts\python.exe manage.py simulate_readings` on a schedule

---

## 4. How the alert engine works

Every metric a device reports has a configured safe range or trigger
value in `apps/devices/constants.py` (`METRIC_CONFIG`) — this is the
single source of truth used by the simulator, the alert engine
(`apps/alerts/engine.py`), and the device detail page's charts.

- **Gauge metrics** (temperature, gas level, stock level): alert when
  outside the configured safe range.
- **Binary metrics** (motion, smoke, door, impact): alert when
  triggered; motion/door alerts on security-capable devices only fire
  while the device is **armed**.
- Alerts are de-duplicated: a new alert isn't raised for a device+metric
  while an unresolved one already exists, so the inbox doesn't get spammed.
- Critical alerts additionally attempt an admin email notification (via
  `mail_admins`, console backend in dev) — a stub for a real
  SMS/push/email integration.

## 5. Billing / subscriptions

`SubscriptionPlan` and `Subscription` are real, DB-backed models mapped
to the public pricing tiers (Starter, Home, Business, Enterprise).
Choosing a plan (`/billing/subscribe/<slug>/`) simulates a successful
checkout so the models and views work end-to-end — swap the marked
integration point in `apps/billing/views.py` for a real Paystack/
Flutterwave charge + webhook when you're ready to take real payments.

---

## 6. Notable design decisions / assumptions

- **Auth:** custom `User` model (`accounts.User`) with an `account_type`
  of `individual` or `organization`. Organization accounts get a
  `Organization` + `Membership` (owner/admin/viewer roles) created at
  signup. Login accepts username or email via a small custom auth backend.
- **Device ownership:** a `Device` belongs to either a `User` (individual)
  or an `Organization` (business) — never both.
- **Pricing:** numbers in `seed_demo_data` (₦2,500–₦15,000/mo, ₦45,000–
  ₦150,000 device cost) are reasonable placeholders for a Nigerian
  hardware/AI subscription product — adjust freely in Django admin
  (`SubscriptionPlan`) or the pricing page reads live from the DB.
- **Payments:** intentionally stubbed (see billing section above) —
  no real gateway calls are made.
- **Email verification / SMS:** stubbed — `is_email_verified` exists on
  the user model for a future verification flow; console email backend
  is used in dev.
- **Logo:** `static/img/logo.png` (and `favicon.ico`) are
  programmatically generated placeholders in TELDEM's brand colors —
  swap them for the real logo file at the same path.

## 7. Admin (internal ops)

Everything is registered in Django admin with sensible list/filter/search
configuration: `/admin/` — manage users, organizations, devices, sensor
readings, alerts, subscription plans, subscriptions, contact submissions
and blog posts from day one.
