# CreditWealth Business API: Frontend Setup Guide

This guide explains how to connect a frontend application to the CreditWealth
Business API.

## 1. API URL

The API base URL must not include `/api`:

```env
# Vite
VITE_API_BASE_URL=http://localhost:8000

# Create React App
REACT_APP_API_BASE_URL=http://localhost:8000

# Next.js
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

For production, replace the local URL with the HTTPS API URL. Keep `.env`
files out of source control and commit only a safe `.env.example`.

The backend allows these local frontend origins by default:

- `http://localhost:3000`
- `http://localhost:5173`

The deployed frontend origin must be added to the backend
`CORS_ALLOWED_ORIGINS` environment variable.

## 2. Authentication

Authentication uses JSON Web Tokens (JWT). Register or log in, store the
returned tokens, and send the access token with every protected request.

### Register

`POST /api/auth/register/`

```json
{
  "phone": "+26870000000",
  "username": "business-owner",
  "password": "a-password-with-at-least-8-characters",
  "first_name": "Anele",
  "last_name": "Dlamini",
  "national_id": "9001010000000",
  "date_of_birth": "1990-01-01",
  "country": "SZ"
}
```

`phone`, `username`, `password`, `national_id`, and `date_of_birth` are
required. A successful response has HTTP status `201`.

### Log in

`POST /api/auth/token/`

```json
{
  "phone": "+26870000000",
  "password": "a-password-with-at-least-8-characters"
}
```

The response contains:

```json
{
  "refresh": "refresh-token",
  "access": "access-token"
}
```

### Refresh an access token

Access tokens are short-lived. Use the refresh token when an access token
expires:

`POST /api/auth/token/refresh/`

```json
{
  "refresh": "refresh-token"
}
```

Replace the stored access token with the `access` value in the response.
If refresh fails, clear both tokens and send the user to the login screen.

### Get the current user

`GET /api/auth/me/`

Required header:

```http
Authorization: Bearer <access-token>
```

The response contains the authenticated business owner's profile:

```json
{
  "id": "uuid",
  "phone": "+26870000000",
  "username": "business-owner",
  "first_name": "Anele",
  "last_name": "Dlamini",
  "national_id": "9001010000000",
  "date_of_birth": "1990-01-01",
  "country": "SZ",
  "created_at": "2026-01-01T10:00:00Z"
}
```

There is currently no logout endpoint. Logout is performed on the client by
clearing the stored access and refresh tokens.

## 3. Minimal API client

The following plain JavaScript client works with Vite, Create React App, or
Next.js after changing the environment-variable lookup for that framework:

```javascript
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

let accessToken = sessionStorage.getItem("access_token");
let refreshToken = sessionStorage.getItem("refresh_token");

async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.message || `Request failed (${response.status})`);
  }

  return response.status === 204 ? null : response.json();
}

export async function login(phone, password) {
  const tokens = await request("/api/auth/token/", {
    method: "POST",
    body: JSON.stringify({ phone, password }),
  });

  accessToken = tokens.access;
  refreshToken = tokens.refresh;
  sessionStorage.setItem("access_token", accessToken);
  sessionStorage.setItem("refresh_token", refreshToken);
  return tokens;
}

export function logout() {
  accessToken = null;
  refreshToken = null;
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("refresh_token");
}
```

For production applications, keep tokens in memory where possible. If a
persistent browser storage mechanism is required, understand that
`localStorage` is accessible to JavaScript and therefore increases the impact
of an XSS vulnerability. Never log tokens or place them in URLs.

## 4. Submit an assessment

All assessment endpoints require the `Authorization` header.

`POST /api/assessments/submit/`

The request body contains six pillar objects, four semantic answers, and
non-family social references:

```json
{
  "pillar_1_data": {},
  "pillar_2_data": {
    "monthly_revenue_midpoint": 15000
  },
  "pillar_3_data": {},
  "pillar_4_data": {},
  "pillar_5_data": {
    "stokvel_status": "active_regular",
    "stokvel_coordinator_phone": "+26871111111"
  },
  "pillar_6_data": {},
  "semantic_challenge_answer": "Describe a difficult business problem you solved.",
  "semantic_covid_answer": "Explain how your business adapted during COVID-19.",
  "semantic_customer_answer": "Who is your main customer?",
  "semantic_advantage_answer": "What makes your business different?",
  "social_references": [
    {
      "name": "Reference One",
      "phone": "+26872222222",
      "relationship": "Supplier",
      "is_family": false
    },
    {
      "name": "Reference Two",
      "phone": "+26873333333",
      "relationship": "Customer",
      "is_family": false
    }
  ]
}
```

Important validation rules:

- `social_references` must contain non-family references. A reference with
  `is_family: true` is rejected.
- If `pillar_5_data.stokvel_status` is `active_regular`,
  `stokvel_coordinator_phone` is required.
- The exact question keys for each pillar must be agreed with the backend
  scoring configuration. The backend stores pillar answers as JSON objects.

On success, the API returns HTTP `202`:

```json
{
  "message": "Assessment submitted. Scoring in progress."
}
```

The assessment is associated with the logged-in user and scoring runs
asynchronously. Do not expect the final score in the submission response.

Example:

```javascript
export function submitAssessment(assessment) {
  return request("/api/assessments/submit/", {
    method: "POST",
    body: JSON.stringify(assessment),
  });
}
```

## 5. Read assessment results

### List the user's assessments

`GET /api/assessments/`

The response is paginated when necessary and contains result fields such as
`id`, `status`, `final_bvss`, `risk_tier`, pillar scores,
`approved_loan_max`, `expires_at`, `improvement_tips`, and
`requires_manual_review`.

### Get one assessment result

`GET /api/assessments/<assessment-id>/result/`

While scoring is incomplete, the API returns HTTP `202`:

```json
{
  "status": "scoring",
  "message": "Scoring is still in progress. Check back shortly."
}
```

After scoring is complete, the API returns HTTP `200` with the result object.
The frontend may poll this endpoint with a reasonable delay, such as every
three to five seconds, and should stop polling after a defined timeout.

Possible assessment statuses include `draft`, `submitted`, `scoring`,
`verified`, `flagged`, and `complete`.

## 6. Common HTTP responses

| Status | Meaning | Frontend action |
|---|---|---|
| `201` | Registration succeeded | Continue to login or use the returned profile |
| `202` | Assessment accepted or still processing | Show progress and poll when appropriate |
| `400` | Invalid request or validation failure | Display field-level errors |
| `401` | Missing, invalid, or expired token | Refresh once, then require login |
| `404` | Resource does not exist or is not owned by the user | Show a not-found state |
| `429` | Rate limit reached | Wait before retrying |
| `500` | Backend failure | Show a retryable error and report the incident |

Do not retry non-idempotent requests such as registration or assessment
submission automatically unless the application can safely prevent duplicate
submissions.

## 7. API documentation and local testing

When the backend is running locally, use:

- Swagger UI: `http://localhost:8000/api/docs/swagger/`
- ReDoc: `http://localhost:8000/api/docs/redoc/`
- OpenAPI JSON: `http://localhost:8000/api/docs/swagger.json`

To start the backend:

```powershell
python manage.py runserver
```

Before testing protected endpoints, create a user or use an existing test
account, log in to obtain an access token, and include the token as a Bearer
token in each request.

## 8. Production checklist

- Use HTTPS for the frontend and API.
- Set the production frontend origin in `CORS_ALLOWED_ORIGINS`.
- Do not commit frontend `.env` files or API secrets.
- Do not expose JWT signing keys in frontend code.
- Do not trust decoded JWT claims for authorization; let the API verify tokens.
- Clear tokens on logout and when refresh fails.
- Handle `202` assessment responses without treating them as failures.
- Keep the API base URL configurable per environment.
