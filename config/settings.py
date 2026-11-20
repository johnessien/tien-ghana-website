"""TIEN Ghana settings. Production (Render + Neon) is configured entirely through environment variables;
see .env.example and HANDOVER.md. Locally, a .env file is read if present."""
import os
import sys
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env(path):
    """Minimal .env reader (KEY=value lines); real environment variables win."""
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                v = v.split(" #", 1)[0].split("\t#", 1)[0]  # allow trailing comments, as in .env.example
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def env_list(name, default):
    return [x.strip() for x in os.environ.get(name, default).split(",") if x.strip()]


_load_env(BASE_DIR / ".env")
TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

# ---------------------------------------------------------------- core
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"   # off unless explicitly switched on
SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("DJANGO_SECRET_KEY") or ""
if not SECRET_KEY:
    if DEBUG or TESTING:
        SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"
    else:
        raise ImproperlyConfigured("SECRET_KEY is not set. Render generates it from render.yaml; locally put it in .env.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,.onrender.com,tienghana.org,www.tienghana.org")
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS", "https://*.onrender.com,https://tienghana.org,https://www.tienghana.org")
if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):  # set automatically by Render
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])
if TESTING:
    ALLOWED_HOSTS.append("testserver")

INSTALLED_APPS = ["django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
                  "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
                  "django.contrib.sitemaps", "django.contrib.humanize", "tien"]
MIDDLEWARE = ["tien.middleware.HealthCheckMiddleware",  # first: before host checks and HTTPS redirect
              "django.middleware.security.SecurityMiddleware",
              "whitenoise.middleware.WhiteNoiseMiddleware",
              "django.contrib.sessions.middleware.SessionMiddleware",
              "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
              "django.contrib.auth.middleware.AuthenticationMiddleware",
              "django.contrib.messages.middleware.MessageMiddleware",
              "django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"],
              "APP_DIRS": True, "OPTIONS": {"context_processors": [
                  "django.template.context_processors.request", "django.contrib.auth.context_processors.auth",
                  "django.contrib.messages.context_processors.messages", "tien.context_processors.navigation"]}}]

# ---------------------------------------------------------------- database (Neon via DATABASE_URL)
if os.environ.get("DATABASE_URL"):
    DATABASES = {"default": dj_database_url.config(conn_max_age=600, conn_health_checks=True, ssl_require=True)}
    if "-pooler." in os.environ["DATABASE_URL"]:  # Neon's pooled endpoint (PgBouncer, transaction mode)
        DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

# ---------------------------------------------------------------- static files (whitenoise) and uploads
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage" if TESTING
                    else "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Africa/Accra"
USE_TZ = True
AUTH_PASSWORD_VALIDATORS = [{"NAME": f"django.contrib.auth.password_validation.{v}"} for v in (
    "UserAttributeSimilarityValidator", "MinimumLengthValidator", "CommonPasswordValidator", "NumericPasswordValidator")]

# ---------------------------------------------------------------- app settings
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY", "").strip()
PAYSTACK_PUBLIC_KEY = os.environ.get("PAYSTACK_PUBLIC_KEY", "").strip()
ADMIN_PATH = os.environ.get("ADMIN_PATH", "secretariat-admin/").strip("/") + "/"

# ---------------------------------------------------------------- security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
if not DEBUG:
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # Render terminates HTTPS
    if not TESTING:  # the test client speaks plain HTTP
        SECURE_SSL_REDIRECT = True
        SECURE_HSTS_SECONDS = 31536000
        SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_PRELOAD = True

LOGGING = {"version": 1, "disable_existing_loggers": False,
           "handlers": {"console": {"class": "logging.StreamHandler"}},
           "root": {"handlers": ["console"], "level": "WARNING"},
           "loggers": {"tien": {"handlers": ["console"], "level": "INFO", "propagate": False}}}
