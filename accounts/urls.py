from django.urls import path

from accounts.views import MeView

urlpatterns = [
    # GET  /api/auth/me/   — current user's profile
    # PATCH /api/auth/me/  — update profile fields
    path("me/", MeView.as_view(), name="me"),
]

# NOTE: There are intentionally no register/, login/, or token/ endpoints.
# All authentication flows (email/password, Google, password reset, email
# verification) are handled client-side by the Firebase SDK.
# The backend only verifies the Firebase ID token that the client sends.
