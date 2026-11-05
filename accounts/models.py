from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class BusinessOwner(AbstractUser):
    """
    Extended user model. National ID is captured at registration and used
    by AGE_EXP_001 to cross-check declared experience years.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, unique=True)
    national_id = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField()
    country = models.CharField(max_length=2, default="SZ")  # ISO 3166-1
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["username", "national_id", "date_of_birth"]

    @property
    def age(self):
        from datetime import date
        today = date.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def __str__(self):
        return f"{self.get_full_name()} ({self.phone})"