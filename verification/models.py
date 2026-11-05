from django.db import models
import uuid


class StokvelsCoordinatorVerification(models.Model):
    """
    Tracks stokvel coordinator verification requests.
    Separate from SocialReference because coordinator is not a personal reference.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        DENIED = "denied", "Denied"
        NO_RESPONSE = "no_response", "No response"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.OneToOneField(
        "assessments.Assessment",
        on_delete=models.CASCADE,
        related_name="stokvel_verification",
    )
    coordinator_phone = models.CharField(max_length=20)
    token = models.CharField(max_length=8)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    sms_sent_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Stokvel verification for {self.assessment_id} [{self.status}]"


class SMSWebhookLog(models.Model):
    """Raw log of all inbound SMS replies for audit trail."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_number = models.CharField(max_length=20)
    body = models.TextField()
    token_found = models.CharField(max_length=8, blank=True)
    processed = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)