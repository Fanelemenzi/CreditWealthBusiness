from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Assessment(models.Model):
    """
    Central record for one complete BVSS self-assessment.
    Raw answers are stored in six pillar JSON fields.
    Computed scores are stored after the scoring engine runs.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        SCORING = "scoring", "Scoring in progress"
        VERIFIED = "verified", "Verified"
        FLAGGED = "flagged", "Flagged for review"
        COMPLETE = "complete", "Complete"

    class RiskTier(models.TextChoices):
        A = "A", "Premium (800–1000)"
        B = "B", "Standard (650–799)"
        C = "C", "Conditional (500–649)"
        D = "D", "Micro (350–499)"
        E = "E", "Not ready (0–349)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # --- Raw pillar answers (one JSON blob per pillar) ---
    pillar_1_data = models.JSONField(default=dict, help_text="Owner character answers")
    pillar_2_data = models.JSONField(default=dict, help_text="Financial performance answers")
    pillar_3_data = models.JSONField(default=dict, help_text="Business maturity answers")
    pillar_4_data = models.JSONField(default=dict, help_text="Market position answers")
    pillar_5_data = models.JSONField(default=dict, help_text="Social capital answers")
    pillar_6_data = models.JSONField(default=dict, help_text="Repayment capacity answers")

    # --- Semantic trap free-text answers ---
    semantic_challenge_answer = models.TextField(blank=True)
    semantic_covid_answer = models.TextField(blank=True)
    semantic_customer_answer = models.TextField(blank=True)
    semantic_advantage_answer = models.TextField(blank=True)

    # --- Computed pillar scores (0–100 each) ---
    score_p1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    score_p2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    score_p3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    score_p4 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    score_p5 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    score_p6 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # MoMo bonus points applied to P2 (0–20)
    score_p2_momo_bonus = models.DecimalField(
        max_digits=4, decimal_places=2, default=0
    )

    # --- Anti-gaming outputs ---
    raw_bvss = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text="Weighted score before anti-gaming penalties"
    )
    penalty_multiplier = models.DecimalField(
        max_digits=5, decimal_places=4, default=1.0000,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    final_bvss = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text="Final score after all penalties applied"
    )
    risk_tier = models.CharField(
        max_length=1, choices=RiskTier.choices, null=True, blank=True
    )

    # --- Verification ---
    social_verification_complete = models.BooleanField(default=False)
    social_verification_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="0–100 composite trust score from reference SMS responses"
    )

    # --- Manual review ---
    requires_manual_review = models.BooleanField(default=False)
    reviewer_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["risk_tier", "final_bvss"]),
        ]

    def __str__(self):
        return f"Assessment {self.id} — {self.owner} [{self.status}]"

    @property
    def approved_loan_max(self):
        """
        Returns maximum loan multiple based on tier.
        Always returns the STAGED first-disbursement amount (60%).
        """
        multipliers = {"A": 12, "B": 8, "C": 4, "D": 2, "E": 0}
        if not self.risk_tier or not self.pillar_2_data:
            return 0
        monthly_rev = self.pillar_2_data.get("monthly_revenue_midpoint", 0)
        gross = monthly_rev * multipliers.get(self.risk_tier, 0)
        return round(gross * settings.BVSS_FIRST_DISBURSEMENT_PCT, 2)


class FraudFlag(models.Model):
    """
    One record per anti-gaming rule that fired on an assessment.
    """

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="fraud_flags"
    )
    rule_id = models.CharField(max_length=30)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    penalty_pct = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField()
    pillars_involved = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-penalty_pct"]

    def __str__(self):
        return f"{self.rule_id} on {self.assessment_id} [{self.severity}]"


class BehavioralSignal(models.Model):
    """
    Passively collected metadata from the assessment session.
    Never shown to the applicant.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.OneToOneField(
        Assessment, on_delete=models.CASCADE, related_name="behavioral_signal"
    )
    # Time spent per question (seconds), keyed by question_id
    question_timings = models.JSONField(default=dict)
    # Number of times each answer was revised
    revision_counts = models.JSONField(default=dict)
    # GPS data
    declared_location_lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    declared_location_lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    gps_lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    gps_lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    gps_distance_km = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    # Device
    device_fingerprint = models.CharField(max_length=64, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SocialReference(models.Model):
    """
    A non-family reference provided by the applicant.
    Receives an SMS verification sequence.
    """

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "SMS sent"
        RESPONDED = "responded", "Responded"
        EXPIRED = "expired", "Expired (no response)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name="social_references"
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    relationship = models.CharField(max_length=100)
    is_family = models.BooleanField(default=False)

    # Verification lifecycle
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    sms_sent_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    verification_token = models.CharField(max_length=8, blank=True)

    # Reference responses (scored 0–100 each)
    q1_reliability_score = models.IntegerField(null=True, blank=True)
    q2_financial_score = models.IntegerField(null=True, blank=True)
    q3_duration_score = models.IntegerField(null=True, blank=True)
    composite_trust_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reference {self.name} for {self.assessment_id}"