# Requirements Document

## Introduction

This feature configures the CreditWealthBusiness Django project as a production-ready Django REST Framework API backend. The work covers six areas: correcting middleware ordering, adding drf-yasg Swagger documentation, wiring missing URL routes for the scoring and antigaming apps, adding throttling and filter backend configuration to DRF, adding STATIC_ROOT and HTTP security headers for production, and toggling debug/production behaviour through environment variables in a single settings.py file.

## Glossary

- **CreditWealthBusiness**: The Django project being configured, located at the workspace root.
- **Settings_Module**: The single `CreditWealthBusiness/settings.py` file that controls all project-wide Django configuration.
- **CORS_Middleware**: `corsheaders.middleware.CorsMiddleware`, the middleware class that injects CORS response headers.
- **Security_Middleware**: `django.middleware.middleware.SecurityMiddleware`, the Django middleware that sets HTTP security headers.
- **Common_Middleware**: `django.middleware.common.CommonMiddleware`, the Django middleware that handles URL normalisation.
- **DRF**: Django REST Framework, version 3.15, the primary API framework used in this project.
- **SimpleJWT**: `djangorestframework-simplejwt` 5.3, the JWT authentication library already installed.
- **drf-yasg**: The `drf-yasg` Python package that generates an interactive Swagger 2.0 OpenAPI UI for DRF APIs.
- **Swagger_UI**: The interactive browser-based API documentation served by drf-yasg at a configured URL path.
- **ReDoc_UI**: An alternative read-only documentation view also served by drf-yasg.
- **Throttle**: A DRF rate-limiting class that limits the number of API requests a client may make in a given time window.
- **Filter_Backend**: A DRF backend class that enables query-parameter-based filtering of list endpoints.
- **STATIC_ROOT**: The Django setting that specifies the filesystem path to which `collectstatic` gathers all static files for production serving.
- **DEBUG_Mode**: The runtime mode controlled by the `DJANGO_DEBUG` environment variable; when `False`, production security settings apply.
- **Scoring_App**: The `scoring` Django app at `scoring/`, which contains business logic for BVSS credit scoring.
- **Antigaming_App**: The `antigaming` Django app at `antigaming/`, which contains fraud and anti-gaming detection logic.
- **Root_URL_Conf**: The `CreditWealthBusiness/urls.py` file that is the entry point for all URL routing.
- **BusinessOwner**: The custom user model defined in `accounts.BusinessOwner`, used as `AUTH_USER_MODEL`.

## Requirements

### Requirement 1: CORS and Middleware Ordering

**User Story:** As a frontend developer, I want CORS preflight requests to be handled before any other middleware processes them, so that cross-origin requests are never blocked by an incorrect middleware execution order.

#### Acceptance Criteria

1. THE Settings_Module SHALL place CORS_Middleware as the first entry in the `MIDDLEWARE` list, before Security_Middleware and all other middleware.
2. THE Settings_Module SHALL place Security_Middleware as the second entry in the `MIDDLEWARE` list, immediately after CORS_Middleware.
3. THE Settings_Module SHALL retain all previously defined middleware entries, preserving their relative order below Security_Middleware and CORS_Middleware.

---

### Requirement 2: Swagger API Documentation

**User Story:** As an API consumer, I want interactive Swagger 2.0 documentation available at a dedicated URL, so that I can explore, understand, and test all API endpoints without reading source code.

#### Acceptance Criteria

1. THE Settings_Module SHALL include `"drf_yasg"` in the `INSTALLED_APPS` list.
2. WHEN the server receives a GET request at `/api/docs/swagger/`, THE Swagger_UI SHALL render an interactive Swagger 2.0 page listing all registered API endpoints.
3. WHEN the server receives a GET request at `/api/docs/redoc/`, THE ReDoc_UI SHALL render a read-only OpenAPI documentation page.
4. WHEN the server receives a GET request at `/api/docs/swagger.json`, THE Root_URL_Conf SHALL return the raw OpenAPI schema as a JSON response.
5. THE Root_URL_Conf SHALL define a `SchemaView` using `drf_yasg.views.get_schema_view` with the API title set to `"CreditWealthBusiness API"`, version set to `"v1"`, and `public=True`.
6. WHERE `DEBUG_Mode` is `False`, THE Swagger_UI SHALL require authentication to access the documentation endpoints.

---

### Requirement 3: Missing URL Routes for Scoring and Antigaming

**User Story:** As an API consumer, I want all application routes to be reachable through the central URL configuration, so that scoring and anti-gaming endpoints are accessible at predictable paths.

#### Acceptance Criteria

1. THE Root_URL_Conf SHALL include a `path("api/scoring/", include("scoring.urls"))` entry so that all Scoring_App endpoints are reachable under the `/api/scoring/` prefix.
2. THE Root_URL_Conf SHALL include a `path("api/antigaming/", include("antigaming.urls"))` entry so that all Antigaming_App endpoints are reachable under the `/api/antigaming/` prefix.
3. THE Scoring_App SHALL contain a `urls.py` file that defines a `urlpatterns` list compatible with `include()`.
4. THE Antigaming_App SHALL contain a `urls.py` file that defines a `urlpatterns` list compatible with `include()`.

---

### Requirement 4: DRF Throttling and Filter Backend Configuration

**User Story:** As a system operator, I want default rate limiting and filter backends configured in DRF, so that API endpoints are protected against abuse and support query-parameter filtering out of the box.

#### Acceptance Criteria

1. THE Settings_Module SHALL add `"DEFAULT_THROTTLE_CLASSES"` to the `REST_FRAMEWORK` dictionary, containing `["rest_framework.throttling.AnonRateThrottle", "rest_framework.throttling.UserRateThrottle"]`.
2. THE Settings_Module SHALL add `"DEFAULT_THROTTLE_RATES"` to the `REST_FRAMEWORK` dictionary with `"anon"` set to `"100/day"` and `"user"` set to `"1000/day"`.
3. THE Settings_Module SHALL add `"DEFAULT_FILTER_BACKENDS"` to the `REST_FRAMEWORK` dictionary, containing `["rest_framework.filters.SearchFilter", "rest_framework.filters.OrderingFilter"]`.
4. THE Settings_Module SHALL add `"DEFAULT_RENDERER_CLASSES"` to the `REST_FRAMEWORK` dictionary with `"rest_framework.renderers.JSONRenderer"` as the first entry.
5. WHERE `DEBUG_Mode` is `True`, THE Settings_Module SHALL also include `"rest_framework.renderers.BrowsableAPIRenderer"` in `DEFAULT_RENDERER_CLASSES` so that the browsable API is available during development.

---

### Requirement 5: Static Files and Production Security Headers

**User Story:** As a DevOps engineer, I want STATIC_ROOT configured and production HTTP security headers enabled, so that static file collection works correctly and the API is hardened against common web attacks in production.

#### Acceptance Criteria

1. THE Settings_Module SHALL define `STATIC_ROOT` as `BASE_DIR / "staticfiles"` so that `python manage.py collectstatic` can gather files to a known directory.
2. WHERE `DEBUG_Mode` is `False`, THE Settings_Module SHALL set `SECURE_SSL_REDIRECT` to `True`.
3. WHERE `DEBUG_Mode` is `False`, THE Settings_Module SHALL set `SECURE_HSTS_SECONDS` to `31536000`.
4. WHERE `DEBUG_Mode` is `False`, THE Settings_Module SHALL set `SECURE_HSTS_INCLUDE_SUBDOMAINS` to `True`.
5. WHERE `DEBUG_Mode` is `False`, THE Settings_Module SHALL set `SECURE_HSTS_PRELOAD` to `True`.
6. WHERE `DEBUG_Mode` is `False`, THE Settings_Module SHALL set `SESSION_COOKIE_SECURE` to `True`.
7. WHERE `DEBUG_Mode` is `False`, THE Settings_Module SHALL set `CSRF_COOKIE_SECURE` to `True`.
8. THE Settings_Module SHALL set `X_FRAME_OPTIONS` to `"DENY"`.
9. THE Settings_Module SHALL set `SECURE_CONTENT_TYPE_NOSNIFF` to `True`.

---

### Requirement 6: Environment-Driven Debug and Allowed Hosts

**User Story:** As a developer, I want DEBUG mode and ALLOWED_HOSTS to be driven entirely by environment variables, so that the same settings.py file works correctly in both local development and production without code changes.

#### Acceptance Criteria

1. THE Settings_Module SHALL read the `DEBUG` value from the `DJANGO_DEBUG` environment variable using `env.bool("DJANGO_DEBUG", default=True)`.
2. IF the `DJANGO_DEBUG` environment variable is absent or unreadable, THEN THE Settings_Module SHALL default `DEBUG` to `True`.
3. THE Settings_Module SHALL read `ALLOWED_HOSTS` from the `DJANGO_ALLOWED_HOSTS` environment variable as a list, with a default of `["localhost", "127.0.0.1"]`.
4. WHERE `DEBUG_Mode` is `False`, THE Settings_Module SHALL require `DJANGO_ALLOWED_HOSTS` to contain at least the production domain, validated at startup by Django's host validation mechanism.

---

### Requirement 7: Package Dependencies

**User Story:** As a developer, I want all newly required packages listed in requirements.txt, so that the environment can be reproduced with a single install command.

#### Acceptance Criteria

1. THE project's `requirements.txt` SHALL include `drf-yasg==1.21.*` as a pinned dependency.
2. THE project's `requirements.txt` SHALL include `django-filter==24.*` as a pinned dependency so that DjangoFilterBackend is available for future use.
3. THE project's `requirements.txt` SHALL retain all previously listed packages without modification.
