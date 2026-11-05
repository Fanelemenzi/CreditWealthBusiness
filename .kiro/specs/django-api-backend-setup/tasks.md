# Implementation Plan: Django API Backend Setup

## Overview

Incremental configuration changes to make CreditWealthBusiness production-ready. All work is in existing files (`settings.py`, `urls.py`, `requirements.txt`) plus two new `urls.py` stubs. No new models or migrations are needed.

## Tasks

- [x] 1. Fix settings.py BASE_DIR and environment-driven DEBUG / ALLOWED_HOSTS
  - [x] 1.1 Remove the duplicate `BASE_DIR` assignment and keep only `BASE_DIR = Path(__file__).resolve().parent.parent`
    - The current file sets `BASE_DIR` twice (`.parent.parent.parent` then `.parent.parent`); keep only the second, correct assignment
    - Replace the hard-coded `DEBUG = True` with `DEBUG = env.bool("DJANGO_DEBUG", default=True)`
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ]* 1.2 Write property tests for DEBUG and ALLOWED_HOSTS env-var round-trips
    - **Property 2: DEBUG value round-trips from environment variable**
    - **Validates: Requirements 6.1, 6.2**
    - **Property 3: ALLOWED_HOSTS round-trips from environment variable**
    - **Validates: Requirements 6.3**

- [x] 2. Fix MIDDLEWARE ordering and add CORS first
  - [x] 2.1 Reorder `MIDDLEWARE` in `settings.py` so `CorsMiddleware` is index 0 and `SecurityMiddleware` is index 1
    - Move `"corsheaders.middleware.CorsMiddleware"` from its current last-but-one position to index 0
    - Ensure `"django.middleware.security.SecurityMiddleware"` remains at index 1
    - Preserve the relative order of all remaining middleware entries
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 2.2 Write unit tests asserting middleware positions
    - Assert `settings.MIDDLEWARE[0] == "corsheaders.middleware.CorsMiddleware"`
    - Assert `settings.MIDDLEWARE[1] == "django.middleware.security.SecurityMiddleware"`
    - _Requirements: 1.1, 1.2_

- [x] 3. Add drf_yasg to INSTALLED_APPS and extend REST_FRAMEWORK settings
  - [x] 3.1 Append `"drf_yasg"` to the third-party block of `INSTALLED_APPS` in `settings.py`
    - _Requirements: 2.1_

  - [x] 3.2 Extend the `REST_FRAMEWORK` dict in `settings.py` with throttling, filter backends, and renderer classes
    - Add `DEFAULT_THROTTLE_CLASSES` with `AnonRateThrottle` and `UserRateThrottle`
    - Add `DEFAULT_THROTTLE_RATES` with `"anon": "100/day"` and `"user": "1000/day"`
    - Add `DEFAULT_FILTER_BACKENDS` with `SearchFilter` and `OrderingFilter`
    - Add `DEFAULT_RENDERER_CLASSES`: include `BrowsableAPIRenderer` only when `DEBUG` is `True`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 3.3 Write unit tests for the new REST_FRAMEWORK keys
    - Assert each new key is present and has the correct value
    - Test the renderer list differs between `DEBUG=True` and `DEBUG=False`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4. Add STATIC_ROOT and production security headers to settings.py
  - [x] 4.1 Add `STATIC_ROOT = BASE_DIR / "staticfiles"` below the existing `STATIC_URL` line
    - _Requirements: 5.1_

  - [x] 4.2 Add the `if not DEBUG:` block for production security headers
    - Set `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`
    - Set `X_FRAME_OPTIONS = "DENY"` and `SECURE_CONTENT_TYPE_NOSNIFF = True` unconditionally (outside the `if not DEBUG` block)
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9_

  - [ ]* 4.3 Write property test for production security flags
    - **Property 1: Production security flags are all enabled when DEBUG is False**
    - **Validates: Requirements 5.2, 5.3, 5.4, 5.5, 5.6, 5.7**

- [ ] 5. Checkpoint — verify settings module
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Create scoring/urls.py and antigaming/urls.py stubs
  - [x] 6.1 Create `scoring/urls.py` with an empty `urlpatterns` list and `app_name = "scoring"`
    - _Requirements: 3.3_

  - [x] 6.2 Create `antigaming/urls.py` with an empty `urlpatterns` list and `app_name = "antigaming"`
    - _Requirements: 3.4_

  - [ ]* 6.3 Write import smoke tests for both new urls.py files
    - Assert `from scoring.urls import urlpatterns` succeeds without error
    - Assert `from antigaming.urls import urlpatterns` succeeds without error
    - _Requirements: 3.3, 3.4_

- [x] 7. Update CreditWealthBusiness/urls.py with new routes and Swagger docs
  - [x] 7.1 Add `drf_yasg` imports and build `schema_view` at the top of `urls.py`
    - Import `get_schema_view`, `openapi`, `permissions`, and `settings`
    - Construct `schema_view` with title `"CreditWealthBusiness API"`, version `"v1"`, `public=True`, and `AllowAny` in debug / `IsAuthenticated` in production
    - _Requirements: 2.5, 2.6_

  - [x] 7.2 Add the scoring, antigaming, and Swagger/ReDoc URL patterns to `urlpatterns`
    - Append `path("api/scoring/", include("scoring.urls"))` and `path("api/antigaming/", include("antigaming.urls"))`
    - Append the three `schema_view` paths: `swagger.json`, `swagger/`, `redoc/`
    - _Requirements: 2.2, 2.3, 2.4, 3.1, 3.2_

  - [ ]* 7.3 Write integration tests for the Swagger and ReDoc endpoints
    - `GET /api/docs/swagger/` → HTTP 200 (debug mode, unauthenticated)
    - `GET /api/docs/redoc/` → HTTP 200 (debug mode, unauthenticated)
    - `GET /api/docs/swagger.json` → HTTP 200 with `application/json` content type
    - _Requirements: 2.2, 2.3, 2.4_

  - [ ]* 7.4 Write property test for OpenAPI schema coverage
    - **Property 4: OpenAPI schema contains all registered URL prefixes**
    - **Validates: Requirements 2.4, 3.1, 3.2**

- [x] 8. Update requirements.txt with new pinned packages
  - [x] 8.1 Append `drf-yasg==1.21.*` and `django-filter==24.*` to `requirements.txt`
    - Retain every existing package entry without modification
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ]* 8.2 Write property test for requirements.txt preservation
    - **Property 5: requirements.txt preserves all original packages**
    - **Validates: Requirements 7.3**

- [ ] 9. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (Properties 1–5 from the design)
- Unit tests validate specific examples and edge cases
- The `scoring/urls.py` and `antigaming/urls.py` stubs are intentionally empty; views will be added in future tasks

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "6.1", "6.2"] },
    { "id": 1, "tasks": ["1.2", "2.1", "3.1", "4.1", "8.1"] },
    { "id": 2, "tasks": ["2.2", "3.2", "4.2", "6.3"] },
    { "id": 3, "tasks": ["3.3", "4.3", "7.1"] },
    { "id": 4, "tasks": ["7.2", "8.2"] },
    { "id": 5, "tasks": ["7.3", "7.4"] }
  ]
}
```
