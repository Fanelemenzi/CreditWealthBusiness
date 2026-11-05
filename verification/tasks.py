from celery import shared_task
from django.utils import timezone
from django.utils.crypto import get_random_string


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_reference_verifications(self, assessment_id: str):
    """
    Dispatched 30 minutes after assessment submission.
    Sends SMS to each non-family reference.
    """
    from assessments.models import Assessment, SocialReference
    from verification.sms import send_reference_sms

    try:
        assessment = Assessment.objects.get(id=assessment_id)
        owner_name = assessment.owner.get_full_name()

        for ref in assessment.social_references.filter(
            is_family=False,
            verification_status=SocialReference.VerificationStatus.PENDING,
        ):
            ref.verification_token = get_random_string(8).upper()
            ref.save(update_fields=["verification_token"])

            success = send_reference_sms(ref, owner_name)
            if success:
                ref.verification_status = SocialReference.VerificationStatus.SENT
                ref.sms_sent_at = timezone.now()
                ref.save(update_fields=["verification_status", "sms_sent_at"])

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def expire_unresponded_references():
    """
    Runs daily. Marks references that haven't responded in 48h as expired.
    An expired (non-responding) reference does not confirm the claim —
    the assessment's Pillar 5 social_verification_score is adjusted.
    """
    from assessments.models import SocialReference
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(hours=48)
    SocialReference.objects.filter(
        verification_status=SocialReference.VerificationStatus.SENT,
        sms_sent_at__lt=cutoff,
    ).update(verification_status=SocialReference.VerificationStatus.EXPIRED)


@shared_task
def recompute_p5_after_verification(assessment_id: str):
    """
    Called after all references have either responded or expired.
    Adjusts the Pillar 5 score and the final BVSS based on social verification.

    Rule: if the composite trust score from references diverges from the
    self-reported P5 score by more than 40 percentage points, P5 is
    capped at 20% of its self-reported value.
    """
    from assessments.models import Assessment, SocialReference
    from decimal import Decimal

    try:
        assessment = Assessment.objects.get(id=assessment_id)
        refs = assessment.social_references.filter(
            composite_trust_score__isnull=False
        )

        if not refs.exists():
            return

        avg_trust = sum(r.composite_trust_score for r in refs) / refs.count()
        self_reported_p5 = float(assessment.score_p5 or 0)

        divergence = abs(avg_trust - self_reported_p5)

        if divergence > 40:
            # Cap P5 at 20% of its declared value
            adjusted_p5 = self_reported_p5 * 0.20
            assessment.score_p5 = Decimal(str(round(adjusted_p5, 2)))

            from assessments.models import FraudFlag
            FraudFlag.objects.get_or_create(
                assessment=assessment,
                rule_id="SOCIAL_DIVERGENCE_001",
                defaults={
                    "severity": "high",
                    "penalty_pct": Decimal("0"),  # handled via P5 cap, not multiplier
                    "description": (
                        f"Reference trust composite ({avg_trust:.1f}/100) diverges "
                        f"from self-reported P5 score ({self_reported_p5:.1f}/100) "
                        f"by {divergence:.1f} points. P5 capped at 20%."
                    ),
                    "pillars_involved": "P5",
                },
            )

            # Recompute final BVSS with adjusted P5
            from scoring.constants import PILLAR_WEIGHTS
            from scoring.engine import assign_risk_tier

            new_raw = (
                float(assessment.score_p1 or 0) * PILLAR_WEIGHTS["p1"]
                + float(assessment.score_p2 or 0) * PILLAR_WEIGHTS["p2"]
                + float(assessment.score_p3 or 0) * PILLAR_WEIGHTS["p3"]
                + float(assessment.score_p4 or 0) * PILLAR_WEIGHTS["p4"]
                + float(assessment.score_p5) * PILLAR_WEIGHTS["p5"]
                + float(assessment.score_p6 or 0) * PILLAR_WEIGHTS["p6"]
            ) * 10

            assessment.raw_bvss = Decimal(str(round(new_raw, 2)))
            assessment.final_bvss = assessment.raw_bvss * assessment.penalty_multiplier
            assessment.risk_tier = assign_risk_tier(float(assessment.final_bvss))

        assessment.social_verification_score = Decimal(str(round(avg_trust, 2)))
        assessment.social_verification_complete = True
        assessment.status = Assessment.Status.COMPLETE
        assessment.completed_at = timezone.now()

        from datetime import timedelta
        from django.conf import settings
        assessment.expires_at = timezone.now() + timedelta(
            days=settings.BVSS_SCORE_VALIDITY_DAYS
        )

        assessment.save()

    except Assessment.DoesNotExist:
        pass