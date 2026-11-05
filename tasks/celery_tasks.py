from celery import shared_task, chain
from django.utils import timezone


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_scoring_pipeline(self, assessment_id: str):
    """
    Master pipeline task. Runs in sequence:
        1. compute_pillar_scores
        2. run_antigaming_engine
        3. (30-minute delay) send_reference_verifications
    """
    try:
        from assessments.models import Assessment
        assessment = Assessment.objects.get(id=assessment_id)
        assessment.status = Assessment.Status.SCORING
        assessment.save(update_fields=["status"])

        pipeline = chain(
            compute_pillar_scores.si(assessment_id),
            run_antigaming_engine.si(assessment_id),
            send_reference_verifications_delayed.si(assessment_id),
        )
        pipeline.apply_async()

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def compute_pillar_scores(self, assessment_id: str):
    try:
        from assessments.models import Assessment
        from scoring.engine import ScoringEngine
        from antigaming.semantic import score_all_semantic_answers

        assessment = Assessment.objects.get(id=assessment_id)
        engine = ScoringEngine(assessment)
        engine.compute()

        # Score semantic traps and store results (informational, not penalty)
        semantic_scores = score_all_semantic_answers(assessment)
        assessment.pillar_4_data["semantic_advantage_score"] = (
            semantic_scores.get("advantage", {}).raw_score
            if hasattr(semantic_scores.get("advantage", {}), "raw_score") else 0
        )
        assessment.save(update_fields=["pillar_4_data"])

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def run_antigaming_engine(self, assessment_id: str):
    try:
        from assessments.models import Assessment
        from antigaming.engine import FraudDetectionEngine

        assessment = Assessment.objects.get(id=assessment_id)
        engine = FraudDetectionEngine(assessment)
        result = engine.run()

        if result.requires_manual_review:
            assessment.status = Assessment.Status.FLAGGED
        else:
            assessment.status = Assessment.Status.VERIFIED

        assessment.save(update_fields=["status"])

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def send_reference_verifications_delayed(assessment_id: str):
    """
    Schedules the social verification SMS with a 30-minute delay.
    This gives applicants a window to correct obvious errors before
    references are contacted.
    """
    from verification.tasks import send_reference_verifications
    send_reference_verifications.apply_async(
        args=[assessment_id],
        countdown=1800,  # 30 minutes
    )