from datetime import time, timedelta
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
import os
import warnings

# django-mcp-server / pydantic_settings: unresolved `lifespan` forward ref.
warnings.filterwarnings(
    "ignore",
    message=r".*Field 'lifespan' has an incomplete definition.*",
)

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "insecure-dev-key-change-me",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

# Railway healthchecks hit the private hostname, not the public *.up.railway.app domain.
if os.environ.get("RAILWAY_PUBLIC_DOMAIN"):
    ALLOWED_HOSTS.append(os.environ["RAILWAY_PUBLIC_DOMAIN"])
if os.environ.get("RAILWAY_PRIVATE_DOMAIN"):
    ALLOWED_HOSTS.append(os.environ["RAILWAY_PRIVATE_DOMAIN"])
if os.environ.get("RAILWAY_ENVIRONMENT"):
    ALLOWED_HOSTS.extend(
        [
            "*",
            ".up.railway.app",
            ".railway.app",
            ".railway.internal",
            "healthcheck.railway.app",
        ]
    )

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
if os.environ.get("RAILWAY_PUBLIC_DOMAIN"):
    CSRF_TRUSTED_ORIGINS.append(f"https://{os.environ['RAILWAY_PUBLIC_DOMAIN']}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "mcp_server",
    "accounts.apps.AccountsConfig",
    "bookings.apps.BookingsConfig",
    "payments.apps.PaymentsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
APPEND_SLASH = False

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

def _postgres_from_url(url):
    parsed = urlparse(url)
    sslmode = (parse_qs(parsed.query).get("sslmode") or [None])[0]
    config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path.lstrip("/")) or "railway",
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or 5432),
        "CONN_MAX_AGE": 60,
    }
    if sslmode:
        config["OPTIONS"] = {"sslmode": sslmode}
    return config


database_url = os.environ.get("DATABASE_URL")
if database_url:
    DATABASES = {"default": _postgres_from_url(database_url)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("PGDATABASE")
            or os.environ.get("POSTGRES_DB", "mahgooz"),
            "USER": os.environ.get("PGUSER") or os.environ.get("POSTGRES_USER", "mahgooz"),
            "PASSWORD": os.environ.get("PGPASSWORD")
            or os.environ.get("POSTGRES_PASSWORD", "mahgooz"),
            "HOST": os.environ.get("PGHOST") or os.environ.get("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.environ.get("PGPORT") or os.environ.get("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 6},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Cairo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip("/")
PUBLIC_API_URL = os.environ.get("PUBLIC_API_URL", "http://localhost:8000").rstrip("/")
STAFF_PHONE = os.environ.get("STAFF_PHONE", "")
STAFF_PASSWORD = os.environ.get("STAFF_PASSWORD", "")
STAFF_NAME = os.environ.get("STAFF_NAME", "Staff")

if os.environ.get("RAILWAY_ENVIRONMENT"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

PAYMOB_SECRET_KEY = os.environ.get("PAYMOB_SECRET_KEY", "")
PAYMOB_PUBLIC_KEY = os.environ.get("PAYMOB_PUBLIC_KEY", "")
PAYMOB_HMAC_SECRET = os.environ.get("PAYMOB_HMAC_SECRET", "")
PAYMOB_INTEGRATION_ID_CARD = os.environ.get("PAYMOB_INTEGRATION_ID_CARD", "")
PAYMOB_BASE_URL = os.environ.get("PAYMOB_BASE_URL", "https://accept.paymob.com").rstrip("/")
PAYMOB_CHECKOUT_BASE_URL = os.environ.get(
    "PAYMOB_CHECKOUT_BASE_URL",
    "https://eg.checkout.paymob.com",
).rstrip("/")

CORS_ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "https://mahgooz.ahmadfathallah89.workers.dev",
]
if FRONTEND_URL not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(FRONTEND_URL)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

DJANGO_MCP_GLOBAL_SERVER_CONFIG = {
    "name": "mahgooz",
    "instructions": (
        "Mahgooz (CourtPass) Django API. Padel court booking: Pay → Reserve → Redeem. "
        "Two courts in Sheikh Zayed, Egypt. Use get_server_instructions and listed tools "
        "to inspect app health and, later, booking models."
    ),
    "stateless": True,
}

DJANGO_MCP_ENDPOINT = "mcp"


def _int_env(name, default):
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


PAYMOB_TIMEOUT_SECONDS = _int_env("PAYMOB_TIMEOUT_SECONDS", 15)


# Booking rules: hours 08:00–22:00, last bookable start 21:00 (60-minute slots).
# One booking may cover multiple hours on the same court and date.
BOOKING_OPERATING_START = time(8, 0)
BOOKING_OPERATING_END = time(22, 0)
BOOKING_SLOT_DURATION_MINUTES = 60
BOOKING_WINDOW_DAYS = _int_env("BOOKING_WINDOW_DAYS", 14)
HOLD_TTL_MINUTES = _int_env("HOLD_TTL_MINUTES", 10)
HOLD_TTL = timedelta(minutes=HOLD_TTL_MINUTES)

BOOKING_PRICE_BANDS = (
    {
        "period": "morning",
        "start": time(8, 0),
        "end": time(12, 0),
        "price_egp": 200,
        "label": "Morning available",
    },
    {
        "period": "afternoon",
        "start": time(12, 0),
        "end": time(17, 0),
        "price_egp": 280,
        "label": "",
    },
    {
        "period": "evening",
        "start": time(17, 0),
        "end": time(22, 0),
        "price_egp": 350,
        "label": "",
    },
)
