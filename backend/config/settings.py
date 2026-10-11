"""Django settings for the Nexus API."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

API_ENV = os.getenv("API_ENV", "development").lower()
DEBUG = os.getenv("DJANGO_DEBUG", "false" if API_ENV == "production" else "true").lower() == "true"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY and not DEBUG:
    raise RuntimeError("Set DJANGO_SECRET_KEY before running Django outside debug mode.")
if not SECRET_KEY:
    SECRET_KEY = "development-only-nexus-secret-key-change-before-deploying"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
    if host.strip()
]

WINDOWS_AUTH = os.getenv("MSSQL_WINDOWS_AUTH", "false").lower() == "true"
missing_database_settings = [
    name
    for name, value in {
        "MSSQL_SERVER": os.getenv("MSSQL_SERVER"),
        "MSSQL_DATABASE": os.getenv("MSSQL_DATABASE"),
    }.items()
    if not value
]
if not WINDOWS_AUTH:
    missing_database_settings.extend(
        name
        for name, value in {
            "MSSQL_USERNAME": os.getenv("MSSQL_USERNAME"),
            "MSSQL_PASSWORD": os.getenv("MSSQL_PASSWORD"),
        }.items()
        if not value
    )
if missing_database_settings:
    raise RuntimeError(f"Missing database environment values: {', '.join(missing_database_settings)}")

INSTALLED_APPS = [
    "apps.accounts.apps.AccountsConfig",
    "apps.connections.apps.ConnectionsConfig",
    "apps.telemetry.apps.TelemetryConfig",
    "apps.dashboard.apps.DashboardConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "api.middleware.ApiSecurityMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = []
USE_TZ = True
TIME_ZONE = "UTC"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
APPEND_SLASH = False
DATA_UPLOAD_MAX_MEMORY_SIZE = 64 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 64 * 1024

DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": os.getenv("MSSQL_DATABASE", ""),
        "USER": "" if WINDOWS_AUTH else os.getenv("MSSQL_USERNAME", ""),
        "PASSWORD": "" if WINDOWS_AUTH else os.getenv("MSSQL_PASSWORD", ""),
        "HOST": os.getenv("MSSQL_SERVER", ""),
        "PORT": os.getenv("MSSQL_PORT", ""),
        "CONN_MAX_AGE": int(os.getenv("MSSQL_CONN_MAX_AGE", "60")),
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "driver": os.getenv("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server"),
            "extra_params": ";".join([
                f"Encrypt={os.getenv('MSSQL_ENCRYPT', 'yes')}",
                f"TrustServerCertificate={os.getenv('MSSQL_TRUST_SERVER_CERTIFICATE', 'no')}",
                f"APP={os.getenv('MSSQL_APPLICATION_NAME', 'Nexus')}",
                f"Connection Timeout={os.getenv('MSSQL_CONNECTION_TIMEOUT', '15')}",
                *( ["Trusted_Connection=yes"] if WINDOWS_AUTH else [] ),
            ]),
        },
    }
}

SESSION_COOKIE_NAME = "nexus_session"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true" if API_ENV == "production" else "false").lower() == "true"
SESSION_LIFETIME_SECONDS = int(os.getenv("SESSION_LIFETIME_SECONDS", "43200"))
FRONTEND_ORIGINS = tuple(
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")
    if origin.strip()
)

SECURE_HSTS_SECONDS = 31536000 if API_ENV == "production" else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = API_ENV == "production"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "false").lower() == "true"
