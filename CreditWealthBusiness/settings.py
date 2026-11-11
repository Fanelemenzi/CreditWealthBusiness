from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-development-only")
DEBUG = env.bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])


# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "django_celery_beat",
    "django_celery_results",
    "corsheaders",
    "drf_yasg",
    # Local apps
    "accounts",
    "assessments",
    "scoring",
    "antigaming",
    "verification",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",                          # must be first
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "antigaming.behavioral.BehavioralSignalMiddleware",
]

ROOT_URLCONF = "CreditWealthBusiness.urls"

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

WSGI_APPLICATION = "CreditWealthBusiness.wsgi.application"


# ---------------------------------------------------------------------------
# Database — SQLite for local development; switch to PostgreSQL in production
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# To switch to PostgreSQL, replace the block above with:
#
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": env("DB_NAME", default="bvss_db"),
#         "USER": env("DB_USER", default="bvss_user"),
#         "PASSWORD": env("DB_PASSWORD", default=""),
#         "HOST": env("DB_HOST", default="localhost"),
#         "PORT": env("DB_PORT", default="5432"),
#     }
# }


# ---------------------------------------------------------------------------
# Auth — custom user model
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = "accounts.BusinessOwner"

# Password validators are kept for the Django admin superuser only;
# regular users authenticate via Firebase and have no Django password.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # Primary: Firebase ID token in `Authorization: Bearer <token>`
        "accounts.authentication.FirebaseAuthentication",
        # Fallback: keeps the Django admin's browsable API working in development
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
    },
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": (
        [
            "rest_framework.renderers.JSONRenderer",
            "rest_framework.renderers.BrowsableAPIRenderer",
        ]
        if DEBUG
        else ["rest_framework.renderers.JSONRenderer"]
    ),
}


# ---------------------------------------------------------------------------
# Firebase Authentication
# ---------------------------------------------------------------------------

# Path to the service account JSON downloaded from:
#   Firebase Console → Project settings → Service accounts → Generate new private key
# Store the file OUTSIDE your git repository.
FIREBASE_CREDENTIALS = env("FIREBASE_CREDENTIALS", default="")

# When True, email/password users must click the verification link before
# the API accepts their token.  Recommended True in production.
FIREBASE_REQUIRE_VERIFIED_EMAIL = env.bool("FIREBASE_REQUIRE_VERIFIED_EMAIL", default=False)

# When True, each request does a network call to Firebase to check whether
# the token has been revoked (e.g. after a forced logout).  Adds ~100 ms.
FIREBASE_CHECK_REVOKED = env.bool("FIREBASE_CHECK_REVOKED", default=False)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000", "http://localhost:5173"],
)


# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------

CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = "django-db"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"


# ---------------------------------------------------------------------------
# Africa's Talking (SMS verification)
# ---------------------------------------------------------------------------

AT_API_KEY = env("AT_API_KEY", default="")
AT_USERNAME = env("AT_USERNAME", default="")
AT_SENDER_ID = env("AT_SENDER_ID", default="BVSS")


# ---------------------------------------------------------------------------
# BVSS scoring config
# ---------------------------------------------------------------------------

BVSS_SCORE_VALIDITY_DAYS = 365
BVSS_FIRST_DISBURSEMENT_PCT = 0.60
BVSS_SECOND_DISBURSEMENT_PCT = 0.80


# ---------------------------------------------------------------------------
# Production security headers (applied only when DEBUG=False)
# ---------------------------------------------------------------------------

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
