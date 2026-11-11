from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class BusinessOwner(AbstractUser):
    """
    Extended user model for CreditWealth business owners.

    Authentication is handled by Firebase (email/password and Google).
    `firebase_uid` links this row to the Firebase account — it is the
    stable identifier regardless of which sign-in method the user chose.

    Business-profile fields (phone, national_id, date_of_birth) are
    collected after sign-up via PATCH /api/auth/me/ and are therefore
    optional at the point of first login.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Firebase linkage — unique per Firebase project
    firebase_uid = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )

    # Business profile — collected after first login
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    national_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=2, default="SZ")  # ISO 3166-1
    created_at = models.DateTimeField(auto_now_add=True)

    # Email is the primary identifier; Firebase always supplies it
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    @property
    def age(self):
        """Returns the owner's current age in years, or None if DOB not yet set."""
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def __str__(self):
        return self.email or self.username