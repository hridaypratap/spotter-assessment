
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

# Load the root .env file for local development.
# Render environment variables are supplied by the hosting platform.
load_dotenv(BASE_DIR.parent / ".env")


# Security
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")

DEBUG = os.getenv("DEBUG", "True").lower() == "true"

if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "local-development-only-key-do-not-deploy"
    else:
        raise RuntimeError(
            "DJANGO_SECRET_KEY must be configured in the environment."
        )


ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1",
    ).split(",")
    if host.strip()
]

# Render supplies this automatically for deployed web services.
render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if render_hostname:
    ALLOWED_HOSTS.append(render_hostname)


# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "routing",
]


# Middleware
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


# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = "static/"


# Email
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}


# CORS
CORS_ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173",
    ).split(",")
    if origin.strip()
]


# External services
MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")


# Primary key defaults
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
