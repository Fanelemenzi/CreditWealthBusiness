# Sharing authentication with another API

This API can be the **authentication owner** for a second API. The frontend
logs in only here, then sends the same access token to both APIs. The second
API is a resource server: it verifies tokens and protects its own endpoints,
but does not implement another login or token issuer.

The second API does not need access to this project's database.

## Architecture

```text
Frontend
   |-- POST /api/auth/token/          -> this API (login)
   |-- POST /api/auth/token/refresh/  -> this API (refresh)
   |-- Authorization: Bearer <access-token> -> this API
   `-- Authorization: Bearer <access-token> -> second API
```

Only access tokens go to resource endpoints. Keep refresh tokens for the
authentication API's refresh endpoint.

## 1. Configure this API (the token issuer)

Set these variables in this project's `.env` file or deployment secret
manager. Do not commit `.env` or private keys:

```dotenv
DJANGO_SECRET_KEY=<different-long-random-django-secret>
JWT_ALGORITHM=HS256
JWT_SECRET_KEY=<long-random-shared-jwt-secret>
JWT_ISSUER=creditwealth-auth
JWT_AUDIENCE=creditwealth-apis
```

`JWT_SIGNING_KEY` may be used instead of `JWT_SECRET_KEY`. The settings in
`CreditWealthBusiness/settings.py` read these variables and pass them to
SimpleJWT. Existing deployments that do not set a JWT key continue to use
`DJANGO_SECRET_KEY` as the signing-key fallback.

The actual authentication endpoints are:

```text
POST /api/auth/register/
POST /api/auth/token/
POST /api/auth/token/refresh/
GET  /api/auth/me/
```

Send the login credentials expected by the `BusinessOwner` model (the
username field is `phone`):

```json
{
  "phone": "+26870000000",
  "password": "your-password"
}
```

The response from `/api/auth/token/` contains `access` and `refresh`.

### Recommended production option: RS256

Use RS256 when the second API must not be able to mint tokens. Keep the
private key only in this API and give the second API only the public key:

```dotenv
JWT_ALGORITHM=RS256
JWT_SIGNING_KEY=<issuer-private-PEM-key>
JWT_VERIFYING_KEY=<issuer-public-PEM-key>
JWT_ISSUER=creditwealth-auth
JWT_AUDIENCE=creditwealth-apis
```

Use your organization's approved key-generation and secret-management
process. Do not put multiline keys in source control.

## 2. Configure the second API as verifier-only

Use the same algorithm, issuer, audience, and verification material:

| Setting | HS256 | RS256 |
|---|---|---|
| Algorithm | `HS256` | `RS256` |
| Verification key | the same `JWT_SECRET_KEY` | `JWT_VERIFYING_KEY` (public key) |
| Issuer | `creditwealth-auth` | `creditwealth-auth` |
| Audience | `creditwealth-apis` | `creditwealth-apis` |

The second API must:

1. Verify the signature and reject expired tokens.
2. Require the configured `iss`, `aud`, and `token_type=access` claims.
3. Never expose login, registration, or token-refresh endpoints.
4. Map `user_id` to a local user or request principal. This can be a
   lightweight local record; it does not require sharing this database.
5. Return `401 Unauthorized` for missing, invalid, expired, wrong-issuer,
   wrong-audience, or refresh tokens.
6. Enforce its own resource permissions after authentication.

### Django REST Framework second API

Install `djangorestframework-simplejwt` in the second API and set its
environment variables. In its `settings.py`:

```python
import os

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

SIMPLE_JWT = {
    "ALGORITHM": os.environ["JWT_ALGORITHM"],
    "VERIFYING_KEY": (
        os.environ["JWT_SECRET_KEY"]
        if os.environ["JWT_ALGORITHM"] == "HS256"
        else os.environ["JWT_VERIFYING_KEY"]
    ),
    "SIGNING_KEY": "",
    "ISSUER": os.environ["JWT_ISSUER"],
    "AUDIENCE": os.environ["JWT_AUDIENCE"],
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```

Do not add `TokenObtainPairView`, `TokenRefreshView`, or equivalent issuer
views to the second API. For HS256, protect the shared secret as carefully as
the issuer does. For RS256, the verifier receives only the public key.

### Node.js second API

With the `jose` package:

```javascript
import { jwtVerify } from "jose";
import { createPublicKey, createSecretKey } from "node:crypto";

const key = process.env.JWT_ALGORITHM === "RS256"
  ? createPublicKey(process.env.JWT_VERIFYING_KEY)
  : createSecretKey(Buffer.from(process.env.JWT_SECRET_KEY, "utf8"));

export async function verifyAccessToken(token) {
  const { payload } = await jwtVerify(token, key, {
    algorithms: [process.env.JWT_ALGORITHM],
    issuer: process.env.JWT_ISSUER,
    audience: process.env.JWT_AUDIENCE,
  });

  if (payload.token_type !== "access") {
    throw new Error("Access token required");
  }
  return payload;
}
```

Call this verifier in authentication middleware before every protected
resource handler. Never trust decoded claims without signature verification.

## 3. Configure the shared frontend

The frontend needs two base URLs, but one auth state:

```dotenv
VITE_AUTH_API_BASE_URL=http://localhost:8000
VITE_OTHER_API_BASE_URL=http://localhost:9000
```

For Create React App use `REACT_APP_` instead of `VITE_`; for Next.js use
`NEXT_PUBLIC_`. Put these variables in the frontend project's root `.env`
file and add that file to `.gitignore`.

The frontend flow is:

1. `POST ${AUTH_API}/api/auth/token/` with the phone and password.
2. Keep the returned access token in memory where possible.
3. Send `Authorization: Bearer <access-token>` to both API base URLs.
4. When it expires, call
   `${AUTH_API}/api/auth/token/refresh/` and replace the access token.
5. Clear the access and refresh tokens when the user signs out.

Example:

```javascript
const headers = {
  Authorization: `Bearer ${accessToken}`,
  "Content-Type": "application/json",
};

await fetch(`${AUTH_API}/api/auth/me/`, { headers });
await fetch(`${OTHER_API}/api/resource/`, { headers });
```

This project currently has no `/api/auth/logout/` endpoint. Logout is
therefore client-side token clearing unless a revocation/blacklist feature is
implemented deliberately. Do not invent a logout request in the frontend.

Do not decode a token and use its contents as authorization. Both APIs must
cryptographically verify the token and apply their own permissions.

## 4. CORS and deployment locations

In this API's `.env`, allow the real frontend origin:

```dotenv
CORS_ALLOWED_ORIGINS=https://app.example.com
```

Set the same frontend origin in the second API's CORS configuration. CORS
controls browser access; it does not replace JWT verification. Use HTTPS for
the frontend and both APIs, keep clocks synchronized, and never log tokens.

## 5. Verification checklist

Before deploying, test the second API with:

- a valid access token;
- no `Authorization` header;
- a malformed token;
- an expired token;
- a refresh token sent as a resource token;
- a token with the wrong issuer or audience;
- a token signed with the wrong key.

Only the first case should be accepted. For RS256 key rotation, deploy the
new public key to the second API before the issuer starts signing with its
matching private key.
