# Design Document

## Overview

This design covers the changes required to make CreditWealthBusiness a production-ready Django REST Framework API backend. The work is concentrated in three files (`settings.py`, `urls.py`, `requirements.txt`) plus two new `urls.py` stubs for the `scoring` and `antigaming` apps. No new models, migrations, or business logic are introduced.

The project is a standard Django 4.2 / DRF 3.15 application using `django-environ` for environment variable management, `djangorestframework-simplejwt` for JWT authentication, `django-cors-headers` for CORS, and Celery + Redis for background tasks. Authentication is performed against the custom `accounts.BusinessOwner` user model.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  HTTP Request                           │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  MIDDLEWARE STACK (ordered)                             │
│  1. CorsMiddleware          ← CORS preflight            │
│  2. SecurityMiddleware      ← HSTS / SSL redirect       │
│  3. SessionMiddleware                                   │
│  4. CommonMiddleware                                    │
│  5. CsrfViewMiddleware                                  │
│  6. AuthenticationMiddleware                            │
│  7. MessageMiddleware                                   │
│  8. XFrameOptionsMiddleware                             │
│  9. BehavioralSignalMiddleware                          │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  ROOT URL CONF  (CreditWealthBusiness/urls.py)          │
│  /admin/                → Django admin                  │
│  /api/auth/             → accounts.urls                 │
│  /api/assessments/      → assessments.urls              │
│  /api/scoring/          → scoring.urls          (NEW)   │
│  /api/antigaming/       → antigaming.urls        (NEW)  │
│  /api/verification/     → verification.urls             │
│  /api/docs/swagger/     → drf_yasg SchemaView   (NEW)  │
│  /api/docs/redoc/       → drf_yasg SchemaView   (NEW)  │
│  /api/docs/swagger.json → drf_yasg SchemaView   (NEW)  │
└─────────────────────────────────────────────────────────┘
```

---

## Components and Interfaces

### 1. `CreditWealthBusiness/settings.py`

The single settings module is modified in-place. All additions are grouped by concern and gated by `DEBUG` where required.

#### 1.1 Middleware Ordering

`CorsMiddleware` is moved to index 0; `SecurityMiddleware` stays at index 1. All other middleware entries are preserved in their original relative order.

```python
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",          # index 0 — CORS first
    "django.middleware.security.SecurityMiddleware",  # index 1
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "antigaming.behavioral.BehavioralSignalMiddleware",
]
```

#### 1.2 Environment-Driven DEBUG and ALLOWED_HOSTS

`django-environ` is already installed. The existing hard-coded `DEBUG = True` is replaced with an environment-variable read. The `BASE_DIR` double-assignment bug (parent.parent.parent then parent.parent) is also corrected.

```python
DEBUG = env.bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
```

#### 1.3 INSTALLED_APPS — drf_yasg

`"drf_yasg"` is appended to the third-party block of `INSTALLED_APPS`.

#### 1.4 DRF Configuration

The existing `REST_FRAMEWORK` dict is extended:

```python
REST_FRAMEWORK = {
    # --- existing ---
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # --- new ---
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
```

#### 1.5 Static Files

`STATIC_ROOT` is added alongside the existing `STATIC_URL`:

```python
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
```

#### 1.6 Production Security Headers

All security settings are gated behind `if not DEBUG`:

```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
```

---

### 2. `CreditWealthBusiness/urls.py`

The root URL conf is extended with three new route groups:

```python
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="CreditWealthBusiness API",
        default_version="v1",
        description="BVSS credit scoring and anti-gaming API",
    ),
    public=True,
    permission_classes=(
        [permissions.AllowAny] if settings.DEBUG else [permissions.IsAuthenticated]
    ),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/assessments/", include("assessments.urls")),
    path("api/scoring/", include("scoring.urls")),        # NEW
    path("api/antigaming/", include("antigaming.urls")),  # NEW
    path("api/verification/sms-webhook/", include("verification.urls")),
    # Swagger / ReDoc docs
    path(
        "api/docs/swagger.json",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "api/docs/swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "api/docs/redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
]
```

---

### 3. `scoring/urls.py` (new file)

A stub `urlpatterns` list that is `include()`-compatible. Views will be added in a future task.

```python
from django.urls import path

app_name = "scoring"

urlpatterns = [
    # scoring endpoints registered here
]
```

---

### 4. `antigaming/urls.py` (new file)

Same pattern as `scoring/urls.py`.

```python
from django.urls import path

app_name = "antigaming"

urlpatterns = [
    # anti-gaming endpoints registered here
]
```

---

### 5. `requirements.txt`

Two pinned packages are appended to the existing file:

```
drf-yasg==1.21.*
django-filter==24.*
```

All existing packages are retained without modification.

---

## Data Models

No new models are introduced. This feature is purely configuration and routing.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| `DJANGO_DEBUG` env var absent | `env.bool` returns default `True`; server starts normally |
| `DJANGO_ALLOWED_HOSTS` absent in production | Django raises `DisallowedHost` on the first request to an unlisted host |
| `drf_yasg` not installed but URLs registered | `ImportError` at startup; surfaced immediately |
| Unauthenticated request to `/api/docs/` in production | DRF returns `HTTP 403 Forbidden` |
| `scoring.urls` or `antigaming.urls` import fails | `ImportError` at startup; surfaced immediately |

---

## Security Considerations

- `CorsMiddleware` at position 0 ensures preflight `OPTIONS` requests are resolved before any authentication or session middleware can reject them. Misplacing it after `SecurityMiddleware` can cause CORS failures on SSL-redirect responses.
- `SECURE_SSL_REDIRECT = True` in production will redirect all HTTP traffic to HTTPS. Ensure a TLS terminator (nginx, load balancer) is in front of the Django process; otherwise, infinite redirect loops may occur.
- `SECURE_HSTS_SECONDS = 31536000` (one year) is the HSTS preload requirement. Only set this when the domain is fully HTTPS — it cannot be easily reversed.
- `drf_yasg` Swagger UI is set to `AllowAny` in development and `IsAuthenticated` in production to prevent schema enumeration by unauthenticated callers.
- `X_FRAME_OPTIONS = "DENY"` prevents clickjacking across all environments regardless of `DEBUG`.
- `SECURE_CONTENT_TYPE_NOSNIFF = True` prevents MIME-type sniffing attacks.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Production security flags are all enabled when DEBUG is False

*For any* combination of environment variables that results in `DEBUG = False`, every security flag in `{SECURE_SSL_REDIRECT, SECURE_HSTS_INCLUDE_SUBDOMAINS, SECURE_HSTS_PRELOAD, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE}` SHALL be `True`, and `SECURE_HSTS_SECONDS` SHALL be greater than 0.

**Validates: Requirements 5.2, 5.3, 5.4, 5.5, 5.6, 5.7**

---

### Property 2: DEBUG value round-trips from environment variable

*For any* boolean-representable string value set as the `DJANGO_DEBUG` environment variable (`"True"`, `"False"`, `"1"`, `"0"`, `"yes"`, `"no"`), the resolved `DEBUG` setting SHALL equal the Python `bool` that corresponds to that string.

**Validates: Requirements 6.1, 6.2**

---

### Property 3: ALLOWED_HOSTS round-trips from environment variable

*For any* non-empty list of valid hostname strings serialised as a comma-separated value in `DJANGO_ALLOWED_HOSTS`, the resolved `ALLOWED_HOSTS` list SHALL contain exactly those hostnames in the same order.

**Validates: Requirements 6.3**

---

### Property 4: OpenAPI schema contains all registered URL prefixes

*For any* URL prefix registered under `urlpatterns` in `CreditWealthBusiness/urls.py`, the OpenAPI schema served at `/api/docs/swagger.json` SHALL contain at least one path entry whose key starts with that prefix.

**Validates: Requirements 2.4, 3.1, 3.2**

---

### Property 5: requirements.txt preserves all original packages

*For any* package name and version specifier that was present in `requirements.txt` before this feature was applied, the updated `requirements.txt` SHALL still contain that exact package name and version specifier.

**Validates: Requirements 7.3**

---

## Testing Strategy

### Unit Tests

- Assert `MIDDLEWARE[0]` is `corsheaders.middleware.CorsMiddleware` and `MIDDLEWARE[1]` is `django.middleware.security.SecurityMiddleware`.
- Assert `"drf_yasg"` is present in `INSTALLED_APPS`.
- Assert `REST_FRAMEWORK` contains `DEFAULT_THROTTLE_CLASSES`, `DEFAULT_THROTTLE_RATES`, `DEFAULT_FILTER_BACKENDS`, and `DEFAULT_RENDERER_CLASSES` with the correct values.
- Assert `STATIC_ROOT == BASE_DIR / "staticfiles"`.
- Assert `X_FRAME_OPTIONS == "DENY"` and `SECURE_CONTENT_TYPE_NOSNIFF is True` in all environments.
- Assert that with `DEBUG=False`, all production security flags are `True`.
- Assert that `from scoring.urls import urlpatterns` and `from antigaming.urls import urlpatterns` succeed without error.

### Integration Tests

- `GET /api/docs/swagger/` returns HTTP 200 in debug mode and HTTP 403 in production mode (unauthenticated).
- `GET /api/docs/redoc/` returns HTTP 200 in debug mode.
- `GET /api/docs/swagger.json` returns HTTP 200 with `Content-Type: application/json`.

### Property-Based Tests

Properties 1–5 in the Correctness Properties section map to property-based test cases that exercise the settings resolution logic and schema generation across varied inputs (boolean env var strings, hostname lists, registered URL prefixes).
