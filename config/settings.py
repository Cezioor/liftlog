"""
Django settings for LiftLog.

All environment-specific values come from environment variables. Locally they
can be put in a `.env` file (see `.env.example`), which python-dotenv loads.
On Render they are set in the dashboard / render.yaml. No secrets live in this file.
"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_list(name):
    """Comma-separated environment variable -> list without empty items."""
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]


DEBUG = os.environ.get("DEBUG", "0") == "1"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set when DEBUG is off.")
    SECRET_KEY = "django-insecure-local-development-only"

# In development accept any host, so the app can be opened from a phone on the
# same Wi-Fi via the computer's LAN IP. In production only the real domain(s).
# Render sets RENDER_EXTERNAL_HOSTNAME (e.g. liftlog.onrender.com) automatically.
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

if DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
    if RENDER_EXTERNAL_HOSTNAME:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Origins allowed to send POST forms over HTTPS (needed behind Render's proxy).
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Sign-up with email verification, login, password reset (django-allauth)
    "allauth",
    "allauth.account",
    # Sends email through a provider's HTTP API (Render's free plan blocks SMTP ports)
    "anymail",
    # Local apps
    "accounts",
    "exercises",
    "plans",
    "workouts",
    "feedback",
]

MIDDLEWARE = [
    # First on purpose: answers /healthz/ before host checks and HTTPS redirects.
    "config.middleware.HealthCheckMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise serves /static/ from gunicorn, so no separate file server is needed.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "feedback.context_processors.feedback_form",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database: DATABASE_URL (Neon gives one like postgresql://user:pass@host/db?sslmode=require)
# in production, SQLite file locally when it is not set.
DATABASE_URL = os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        # Neon suspends an idle database; check reused connections before using them.
        conn_health_checks=True,
    )
}
if "-pooler." in DATABASE_URL:
    # Neon's pooled endpoint (PgBouncer, transaction mode) doesn't support
    # server-side cursors, which Django uses for .iterator().
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True


# Authentication
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # admin login by username
    "allauth.account.auth_backends.AuthenticationBackend",  # app login by email
]

LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "home"

# django-allauth: log in with email; an account works only after its email is confirmed.
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]  # username is generated
# "mandatory": no access until the emailed link is clicked (default).
# "optional": logged in right after sign-up; the link is still sent (a temporary
# switch while email delivery is being set up). Set on Render, no code change needed.
ACCOUNT_EMAIL_VERIFICATION = os.environ.get("ACCOUNT_EMAIL_VERIFICATION", "mandatory").strip()
if ACCOUNT_EMAIL_VERIFICATION not in {"mandatory", "optional"}:
    raise ImproperlyConfigured(
        f'ACCOUNT_EMAIL_VERIFICATION must be "mandatory" or "optional", '
        f'not "{ACCOUNT_EMAIL_VERIFICATION}".'
    )
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3  # the email says "ważny przez 3 dni"
ACCOUNT_LOGOUT_REDIRECT_URL = "account_login"
# Say clearly that an email is already registered (with links to log in / reset the
# password) instead of pretending the sign-up worked. Fine for a small personal app.
ACCOUNT_PREVENT_ENUMERATION = False
ACCOUNT_FORMS = {"signup": "accounts.forms.SignupForm"}
ACCOUNT_ADAPTER = "accounts.adapter.AccountAdapter"
ACCOUNT_EMAIL_SUBJECT_PREFIX = ""  # the subjects name LiftLog themselves
# Attempts per time window, counted in the shared cache below (m = minute, s = seconds).
ACCOUNT_RATE_LIMITS = {
    "login": "30/m/ip",
    "login_failed": "10/m/ip,5/300s/key",  # 5 wrong passwords per email in 5 minutes
    "signup": "10/m/ip",
    "confirm_email": "1/180s/key",  # one verification email per address every 3 minutes
    "reset_password": "20/m/ip,5/m/key",
    "reset_password_from_key": "20/m/ip",
    "change_password": "5/m/user",
    "manage_email": "10/m/user",
    "reauthenticate": "10/m/user",
}

# Rate limits live in the cache. A database table (created by build.sh with
# createcachetable) is shared by all gunicorn workers, unlike per-process memory.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    }
}

# Email: printed to the console locally; sent through Brevo's HTTP API when
# BREVO_API_KEY is set (Render). The key lives only in the environment.
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
if BREVO_API_KEY:
    EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"
    ANYMAIL = {"BREVO_API_KEY": BREVO_API_KEY}
else:
    EMAIL_BACKEND = os.environ.get(
        "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
    )
# Where feedback reports are emailed (feedback app); empty = only saved, not emailed.
FEEDBACK_EMAIL = os.environ.get("FEEDBACK_EMAIL", "").strip()
# Must be a sender verified in Brevo (Senders, domains & dedicated IPs).
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "LiftLog <noreply@liftlog.local>")


# Internationalization: store times in UTC, show them in Warsaw time.
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, images)
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Hashed file names (app.3f2a1c.css) + gzip/brotli: browsers can cache files
    # forever and still get new versions after a deploy. Needs collectstatic.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
if DEBUG:
    # Locally serve files straight from static/ without running collectstatic.
    STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Production security (everything below only applies when DEBUG is off).
if not DEBUG:
    # Render terminates HTTPS and forwards plain HTTP with this header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "1") == "1"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HSTS tells browsers to use HTTPS only. Start short (1 hour); once
    # everything works, raise DJANGO_HSTS_SECONDS to e.g. 2592000 (30 days).
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "3600"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

SILENCED_SYSTEM_CHECKS = [
    # Deliberate: we only control liftlog.onrender.com, not its subdomains,
    # and HSTS preload is a long-term commitment we don't want yet.
    "security.W005",
    "security.W021",
]

# Without this, errors on the server would not appear in Render's logs.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        # Bots probing random host names would fill the logs with tracebacks.
        "django.security.DisallowedHost": {"handlers": [], "propagate": False},
    },
}
