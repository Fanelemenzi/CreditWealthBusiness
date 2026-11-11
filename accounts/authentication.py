from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from rest_framework import authentication, exceptions

User = get_user_model()


def get_firebase_app():
    """
    Initialise the Firebase Admin SDK once per process, then reuse it.
    Calling firebase_admin.get_app() raises ValueError if not yet initialised,
    so we catch that and initialise on first call.
    """
    try:
        return firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)
        return firebase_admin.initialize_app(cred)


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    DRF authentication class that validates Firebase ID tokens.

    Reads `Authorization: Bearer <Firebase ID token>`, verifies it against
    Google's public keys via the firebase-admin SDK, then returns (or creates)
    the matching Django BusinessOwner row from the shared database.

    Works identically for email/password and Google sign-in — Firebase issues
    the same kind of ID token for both methods.
    """

    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode()
        parts = header.split()

        # No token present — treat as anonymous; permission classes decide
        if not parts or parts[0].lower() != self.keyword.lower():
            return None

        if len(parts) != 2:
            raise exceptions.AuthenticationFailed("Invalid Authorization header format.")

        decoded_token = self._verify_token(parts[1])
        user = self._get_or_create_user(decoded_token)

        if not user.is_active:
            raise exceptions.AuthenticationFailed("This account has been disabled.")

        # request.user = user, request.auth = decoded token (useful for checking claims)
        return (user, decoded_token)

    def authenticate_header(self, request):
        # Returning a value here makes DRF emit 401 (not 403) when auth fails,
        # so the frontend knows to redirect to login rather than show "forbidden".
        return self.keyword

    # ------------------------------------------------------------------ helpers

    def _verify_token(self, token: str) -> dict:
        """
        Calls Firebase to verify the ID token signature and expiry.
        Raises AuthenticationFailed with a user-facing message on any failure.
        """
        try:
            return firebase_auth.verify_id_token(
                token,
                app=get_firebase_app(),
                check_revoked=getattr(settings, "FIREBASE_CHECK_REVOKED", False),
            )
        # Subclasses of InvalidIdTokenError must come first
        except firebase_auth.ExpiredIdTokenError:
            raise exceptions.AuthenticationFailed(
                "Token has expired. Please refresh it and try again."
            )
        except firebase_auth.RevokedIdTokenError:
            raise exceptions.AuthenticationFailed(
                "Token has been revoked. Please log in again."
            )
        except firebase_auth.UserDisabledError:
            raise exceptions.AuthenticationFailed(
                "This Firebase account has been disabled."
            )
        except firebase_auth.InvalidIdTokenError:
            raise exceptions.AuthenticationFailed("Invalid Firebase ID token.")
        except firebase_auth.CertificateFetchError:
            raise exceptions.AuthenticationFailed(
                "Could not reach Firebase to verify the token. Please try again."
            )

    def _get_or_create_user(self, decoded_token: dict) -> User:
        """
        Look up or create a BusinessOwner row from a decoded Firebase token.

        Strategy (in order):
          1. Find by firebase_uid — the normal path after first login.
          2. Find by verified email and no uid — link a pre-existing Django user.
          3. Create a brand-new user.
        """
        uid: str = decoded_token["uid"]
        email: str = decoded_token.get("email", "")
        email_verified: bool = decoded_token.get("email_verified", False)
        name: str = decoded_token.get("name", "")

        require_verified = getattr(settings, "FIREBASE_REQUIRE_VERIFIED_EMAIL", False)
        if require_verified and not email_verified:
            raise exceptions.AuthenticationFailed(
                "Please verify your email address before accessing the API."
            )

        # 1) Already linked — the happy path
        user = User.objects.filter(firebase_uid=uid).first()
        if user:
            # Keep the email in sync if the user updated it in Firebase
            if email and user.email != email:
                user.email = email
                user.save(update_fields=["email"])
            return user

        # 2) Pre-existing account with the same VERIFIED email — link it
        #    (only for verified emails; unverified would let anyone claim another's account)
        if email and email_verified:
            user = User.objects.filter(
                email__iexact=email, firebase_uid__isnull=True
            ).first()
            if user:
                user.firebase_uid = uid
                user.save(update_fields=["firebase_uid"])
                return user

        # 3) Brand-new user — create a minimal profile; the rest is filled in later
        first_name, _, last_name = name.partition(" ")
        try:
            with transaction.atomic():
                user = User(
                    firebase_uid=uid,
                    username=uid,          # uid is globally unique — safe as a username
                    email=email,
                    first_name=first_name[:150],
                    last_name=last_name[:150],
                )
                user.set_unusable_password()   # passwords live in Firebase, not Django
                user.save()
                return user
        except IntegrityError:
            # Race condition: two requests (or two API instances) tried to create
            # the same user simultaneously. The other one won — just fetch it.
            return User.objects.get(firebase_uid=uid)
