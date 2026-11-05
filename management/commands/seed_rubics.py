"""
Seeds sector and benchmark data for the REV_CUST_001 rule.
Run once on a fresh database.

Usage:
    python manage.py seed_rubrics
"""
from django.core.management.base import BaseCommand


SECTOR_BENCHMARKS = [
    # (sector_key, display_name, min_customer_spend_szl, typical_revenue_range)
    ("spaza",        "Spaza shop",         20,  "1k_8k"),
    ("food",         "Food & catering",    30,  "3k_20k"),
    ("retail",       "General retail",     50,  "3k_50k"),
    ("butchery",     "Butchery",           80,  "8k_50k"),
    ("general_trade","General trade",       25,  "1k_20k"),
    ("salon",        "Hair & beauty",      60,  "3k_20k"),
    ("transport",    "Transport/taxi",    200,  "8k_50k"),
    ("construction", "Building/construction", 500, "20k_above"),
    ("services",     "Professional services", 300, "8k_above"),
    ("agriculture",  "Agriculture",        100,  "3k_20k"),
]


class Command(BaseCommand):
    help = "Seed sector benchmark data"

    def handle(self, *args, **options):
        # In a full implementation this would write to a SectorBenchmark model.
        # For now, validate constants are in sync.
        from antigaming.constants import RETAIL_SECTORS
        for sector_key, *_ in SECTOR_BENCHMARKS:
            if sector_key not in RETAIL_SECTORS:
                self.stdout.write(
                    self.style.WARNING(f"  {sector_key} not in RETAIL_SECTORS constant")
                )
        self.stdout.write(self.style.SUCCESS("Sector benchmark validation complete."))