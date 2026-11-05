"""
Post-save signal on Assessment.
When status transitions to SUBMITTED, the scoring pipeline
is dispatched asynchronously via Celery.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from assessments.models import Assessment


@receiver(post_save, sender=Assessment)
def on_assessment_submitted(sender, instance, created, **kwargs):
    """
    Triggered when an assessment is first saved with SUBMITTED status.
    Guards against re-triggering on subsequent saves.
    """
    if instance.status == Assessment.Status.SUBMITTED:
        # Only trigger if pipeline hasn't started (raw_bvss not yet set)
        if instance.raw_bvss is None:
            from tasks.celery_tasks import run_scoring_pipeline
            run_scoring_pipeline.apply_async(
                args=[str(instance.id)],
                countdown=5,  # short delay to let the request complete
            )