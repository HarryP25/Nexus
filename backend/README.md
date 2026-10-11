# Nexus Backend

Nexus's backend is a Django API that uses Django's ORM with Microsoft SQL Server. The React frontend calls the API under `/api/`.

## Backend layout

```text
backend/
  config/                 Django settings, root URLs, WSGI, and ASGI
  apps/
    accounts/             Users, session handling, account views and URLs
    connections/           Data-source models, connection views and URLs
    dashboard/             Live analysis views and URLs
    telemetry/             Metric models, services, and migrations
  integrations/            Provider validation and credential helpers
    cato/
    site24x7/
    solarwinds/
  api/                     Shared HTTP helpers and security middleware
  manage.py                Django management entry point
  schema.sql               Idempotent SQL Server schema reference
  requirements.txt         Python dependencies
  .env.example             Environment variable template
```

Each Django app owns its endpoint definitions in its own `urls.py`. `config/urls.py` includes those URL files. Provider-specific integration code is kept outside the Django apps because providers do not currently have separate database models or migration lifecycles.

## Requirements

- Python and pip
- Microsoft SQL Server
- Microsoft ODBC Driver 18 for SQL Server
- Node.js/npm for running the frontend with the backend

Install the Python dependencies in a virtual environment:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` in this directory and set the database and security values. Do not commit `.env` or put production secrets in source control.

| Variable | Purpose |
| --- | --- |
| `MSSQL_SERVER` | SQL Server host/instance, such as `localhost\SQLEXPRESS` |
| `MSSQL_DATABASE` | Database name |
| `MSSQL_WINDOWS_AUTH` | Set `true` to use Windows integrated authentication; otherwise use SQL credentials |
| `MSSQL_USERNAME`, `MSSQL_PASSWORD` | SQL login; required when Windows authentication is disabled |
| `MSSQL_PORT` | Optional SQL Server port |
| `MSSQL_DRIVER` | ODBC driver name; defaults to ODBC Driver 18 for SQL Server |
| `MSSQL_ENCRYPT`, `MSSQL_TRUST_SERVER_CERTIFICATE` | ODBC encryption and certificate settings |
| `MSSQL_APPLICATION_NAME`, `MSSQL_CONNECTION_TIMEOUT`, `MSSQL_CONN_MAX_AGE` | Connection label, timeout, and Django connection reuse settings |
| `DJANGO_SECRET_KEY` | Django signing secret; required when `DJANGO_DEBUG=false` |
| `DJANGO_DEBUG` | Django debug mode; disable for deployment |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated Django host names |
| `FRONTEND_ORIGIN` | Comma-separated trusted frontend origins for API CORS |
| `DATASOURCE_ENCRYPTION_KEY` | Fernet key used to encrypt stored datasource credentials |
| `SESSION_COOKIE_SAMESITE`, `SESSION_COOKIE_SECURE`, `SESSION_LIFETIME_SECONDS` | Session cookie policy and session lifetime |
| `API_ENV`, `DJANGO_SECURE_SSL_REDIRECT` | Deployment security behavior and optional HTTPS redirect |

Generate a Django secret key and a Fernet encryption key after installing requirements:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set the generated values in `.env`. Keep a secure backup of `DATASOURCE_ENCRYPTION_KEY`: stored integration credentials cannot be decrypted if this key is lost or changed.

## Database setup and migrations

The configured SQL Server database is required for normal API operation. From `backend/`, run:

```powershell
python manage.py check
python manage.py migrate
```

The initial account migration creates missing Nexus tables and adopts/extends existing tables where supported. The telemetry migration creates `dbo.NexusMetricPoints` and copies existing Site24x7 metric rows into it. `backend/schema.sql` is provided for manual schema provisioning. Review and back up the target database before applying migrations in a production environment.

Most models map to the existing `dbo` tables and are marked unmanaged by Django; database structure changes are handled by the explicit SQL migrations rather than routine ORM model migrations.

## Run locally

From the repository root, `npm run dev` starts Django on `127.0.0.1:5001` and Vite on its development port. Vite proxies `/api` requests to Django. The combined development script uses Django's `--noreload`, so restart `npm run dev` after changing backend code.

To run only Django from `backend/`:

```powershell
python manage.py runserver 127.0.0.1:5001
```

The Django development server is for local development only. Deploy with a production WSGI or ASGI server using `config.wsgi:application` or `config.asgi:application`, and configure the web server to serve the frontend and proxy `/api` to Django.

## API routes

All API routes are under `/api/`; the current routes do not require a trailing slash.

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Basic API health response |
| `GET` | `/api/session` | Restore the current session and return a CSRF token |
| `POST` | `/api/signup` | Create an account |
| `POST` | `/api/login` | Sign in and issue an HttpOnly session cookie |
| `POST` | `/api/logout` | Revoke the current session |
| `GET` | `/api/users/count` | Return the user count; requires authentication |
| `GET`, `POST` | `/api/datasources` | List or create the signed-in user's data sources |
| `PUT`, `DELETE` | `/api/datasources/<uuid>` | Update or delete an owned data source |
| `GET` | `/api/datasources/<uuid>/analysis` | Read Site24x7 analysis data for an owned source |
| `GET` | `/api/dashboard/overview` | Return date-range telemetry summary and chart series |

The dashboard endpoint accepts `start` and `end` as `YYYY-MM-DD` dates and accepts repeated `source_id` filters. If no dates are supplied, it returns the last 24 hours. The maximum range is 366 days. Results are scoped to the authenticated user's data sources.

## Sessions and request security

The API stores a hash of the opaque session cookie in `dbo.NexusSessions`; the raw cookie is HttpOnly. Successful session restoration provides a CSRF token. State-changing requests (`POST`, `PUT`, `PATCH`, and `DELETE`) must send it in the `X-CSRF-Token` header. The frontend helper adds the token and sends cookies automatically.

Production deployments should use HTTPS, set `API_ENV=production`, configure a strong `DJANGO_SECRET_KEY`, set exact trusted origins in `FRONTEND_ORIGIN`, and use a secure cookie. If frontend and API are on separate sites, configure `SESSION_COOKIE_SAMESITE=None` and HTTPS.

## Telemetry and integrations

The home dashboard reads live data from `dbo.NexusMetricPoints`. The API groups readings into hourly, daily, or weekly buckets depending on the selected range and returns average, minimum, maximum, and count for each metric bucket.

Provider-specific payload validation lives under `integrations/`. Site24x7 currently has seeded/demo metric behavior; Cato and SolarWinds configuration handling is present, but live collectors and provider connectivity tests are not yet implemented.

The local test database currently includes a 30-day demo series attached to the Site24x7 source. Those rows are marked in `dimensionsJson` with `nexus-demo-telemetry-v1` and can be inspected with:

```sql
SELECT hostName, metricName, metricValue, unit, status, recordedAt
FROM dbo.NexusMetricPoints
WHERE dimensionsJson LIKE N'%nexus-demo-telemetry-v1%'
ORDER BY recordedAt, hostName, metricName;
```

This demo series is database content, not a checked-in data file. It is specific to the configured local database.
