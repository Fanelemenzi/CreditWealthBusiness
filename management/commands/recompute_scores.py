"""
Management command to recompute scores for all assessments
in COMPLETE or VERIFIED status. Useful after rubric updates.

Usage:
    python manage.py recompute_scores
    python manage.py recompute_scores --dry-run
    python manage.py recompute_scores --tier C
"""
from django.core.management.base import BaseCommand
from assessments.models import Assessment
from scoring.engine import ScoringEngine
from antigaming.engine import FraudDetectionEngine


class Command(BaseCommand):
    help = "Recompute BVSS scores for completed assessments"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--tier", type=str, choices=["A", "B", "C", "D", "E"])

    def handle(self, *args, **options):
        qs = Assessment.objects.filter(
            status__in=[Assessment.Status.COMPLETE, Assessment.Status.VERIFIED]
        )

        if options["tier"]:
            qs = qs.filter(risk_tier=options["tier"])

        count = qs.count()
        self.stdout.write(f"Found {count} assessments to recompute.")

        if options["dry_run"]:
            self.stdout.write("Dry run — no changes made.")
            return

        for assessment in qs.iterator(chunk_size=100):
            # Clear existing flags
            assessment.fraud_flags.all().delete()

            se = ScoringEngine(assessment)
            se.compute()

            de = FraudDetectionEngine(assessment)
            de.run()

            self.stdout.write(
                f"  Recomputed {assessment.id}: BVSS {assessment.final_bvss} [{assessment.risk_tier}]"
            )

        self.stdout.write(self.style.SUCCESS(f"Done. {count} assessments recomputed."))