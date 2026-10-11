# Wissen Nexus

Nexus is an observability dashboard with a React frontend and a Django API backed by Microsoft SQL Server.

## Project layout

```text
src/
  components/       Shared brand and page-level UI components
  lib/              Browser helpers and integration logo mapping
  assets/           Static and integration assets
backend/
  config/           Django settings, root URL configuration, WSGI, and ASGI
  apps/
    accounts/       User records, sessions, views, and account URLs
    connections/    Data sources, views, and connection URLs
    telemetry/      Metric models, collection services, and migrations
    dashboard/      Dashboard analysis views and URLs
  integrations/     Provider adapters and encrypted credential helpers
    cato/
    site24x7/
    solarwinds/
  api/              Shared API middleware and HTTP helpers
  manage.py         Django management entry point
  schema.sql        Idempotent SQL Server base schema
scripts/
  dev.mjs           Starts the local API and Vite development server
```

The API runs on Django and uses the Microsoft-supported `mssql-django` backend with Django's ORM. Each domain owns its models, views, and URL configuration; the root URL configuration includes each app's `urls.py`. Provider-specific configuration and integration code lives under `integrations/`, separate from the Django apps that own persisted data. Existing SQL Server `dbo` tables are mapped directly so the conversion can preserve current data.

## Local development

Create `backend/.env` from `backend/.env.example`, set the SQL Server connection values, create a Django secret key, and generate a Fernet key for `DATASOURCE_ENCRYPTION_KEY`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Install and start the backend and frontend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
cd ..
npm install
npm run dev
```

The first Django migration idempotently creates missing core tables or adopts existing Nexus tables; the telemetry migration adds the generic metric-point table and carries forward existing Site24x7 readings. `backend/schema.sql` remains available for manual SQL Server provisioning. `npm run dev` starts Django on port 5001 and Vite on its development port. Vite proxies `/api` requests to Django. Use `npm run dev:vite` when the backend is already running separately.

## Deployment

Build the frontend with `npm run build`; the static output is written to `dist/`. Run `python manage.py migrate` from `backend` as a release step, then serve `config.wsgi:application` with a production WSGI server. Configure the web server or gateway to serve the frontend and forward `/api` requests to Django. Set the MSSQL values, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DATASOURCE_ENCRYPTION_KEY`, and trusted `FRONTEND_ORIGIN` values in the deployment environment. Keep secrets out of source control and set `DJANGO_DEBUG=false`.

## Authentication and session security

Successful sign-in creates an opaque, random session cookie. The API stores only its SHA-256 hash in `dbo.NexusSessions`, associates it with the authenticated user, and expires it after 12 hours. Data-source endpoints derive ownership from this server-side session; they do not accept a client-supplied user ID. State-changing API requests require a CSRF token. The cookie is `HttpOnly` and `SameSite=Lax` by default. New accounts require passwords of at least 12 characters; login errors use the same message for unknown usernames and incorrect passwords.

For HTTPS deployment, set `API_ENV=production` or `SESSION_COOKIE_SECURE=true`. If the frontend and API are hosted on different sites, use HTTPS and set `SESSION_COOKIE_SAMESITE=None`; keep `FRONTEND_ORIGIN` restricted to exact trusted origins.

## Dashboard data

The home dashboard requests `/api/dashboard/overview` from Django. It accepts optional `start` and `end` dates (`YYYY-MM-DD`) and repeated `source_id` filters, then returns owner-scoped summaries and time-bucketed metric series. Without a date range it returns the last 24 hours. `dbo.NexusMetricPoints` is the provider-neutral telemetry table indexed by source/time and metric/time. Site24x7 currently seeds demo measurements; provider collectors and live connection tests still need implementation before integrations can supply real telemetry.
