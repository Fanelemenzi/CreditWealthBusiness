"""
FraudDetectionEngine — orchestrates all anti-gaming rule checks and
applies the cumulative penalty to the assessment's raw BVSS.
"""
from decimal import Decimal
from django.db import transaction

from antigaming.rules import (
    rule_age_exp_001,
    rule_debt_cont_001,
    rule_rev_emp_001,
    rule_loc_rev_001,
    rule_stok_sav_001,
    rule_grow_rev_001,
    rule_rev_cust_001,
    rule_rev_sav_001,
)
from antigaming.behavioral import BehavioralRuleChecker
from assessments.models import FraudFlag


# Rules that require mandatory manual review when triggered
MANUAL_REVIEW_RULES = {"AGE_EXP_001", "DEBT_CONT_001"}

# All cross-pillar consistency rules in execution order
CONSISTENCY_RULES = [
    rule_age_exp_001,
    rule_debt_cont_001,
    rule_rev_emp_001,
    rule_loc_rev_001,
    rule_stok_sav_001,
    rule_grow_rev_001,
    rule_rev_cust_001,
    rule_rev_sav_001,
]


class FraudDetectionEngine:
    """
    Usage:
        engine = FraudDetectionEngine(assessment)
        result = engine.run()
        # result.final_bvss is the penalized score
    """

    def __init__(self, assessment):
        self.assessment = assessment
        self.flags = []

    def run(self) -> "FraudDetectionResult":
        self._run_consistency_rules()
        self._run_behavioral_rules()
        self._apply_penalties()
        return FraudDetectionResult(
            flags=self.flags,
            final_bvss=self.assessment.final_bvss,
            penalty_multiplier=self.assessment.penalty_multiplier,
            requires_manual_review=self.assessment.requires_manual_review,
        )

    def _run_consistency_rules(self):
        for rule_fn in CONSISTENCY_RULES:
            result = rule_fn(self.assessment)
            if result:
                self.flags.append(result)

    def _run_behavioral_rules(self):
        try:
            behavioral = self.assessment.behavioral_signal
        except Exception:
            return

        checker = BehavioralRuleChecker(behavioral)
        self.flags.extend(checker.run())

    @transaction.atomic
    def _apply_penalties(self):
        """
        Penalties are multiplicative and cumulative.
        Example: two medium (−5%) and one high (−12%) flags:
            multiplier = (1 - 0.05) × (1 - 0.05) × (1 - 0.12) = 0.7942
            final_bvss = raw_bvss × 0.7942

        This is harsher than additive (−22%) for multiple violations,
        which is intentional — it penalises systematic cheating more heavily.
        """
        multiplier = Decimal("1.0000")
        requires_review = False

        for flag in self.flags:
            penalty_fraction = flag.penalty_pct / Decimal("100")
            multiplier *= (Decimal("1") - penalty_fraction)

            if flag.rule_id in MANUAL_REVIEW_RULES:
                requires_review = True

            FraudFlag.objects.create(
                assessment=self.assessment,
                rule_id=flag.rule_id,
                severity=flag.severity,
                penalty_pct=flag.penalty_pct,
                description=flag.description,
                pillars_involved=flag.pillars_involved,
            )

        raw = self.assessment.raw_bvss or Decimal("0")
        final = max(Decimal("0"), min(Decimal("1000"), raw * multiplier))

        from scoring.engine import assign_risk_tier

        self.assessment.penalty_multiplier = multiplier.quantize(Decimal("0.0001"))
        self.assessment.final_bvss = final.quantize(Decimal("0.01"))
        self.assessment.risk_tier = assign_risk_tier(float(final))
        self.assessment.requires_manual_review = requires_review
        self.assessment.save(update_fields=[
            "penalty_multiplier", "final_bvss", "risk_tier", "requires_manual_review"
        ])


class FraudDetectionResult:
    def __init__(self, flags, final_bvss, penalty_multiplier, requires_manual_review):
        self.flags = flags
        self.final_bvss = final_bvss
        self.penalty_multiplier = penalty_multiplier
        self.requires_manual_review = requires_manual_review
        self.flag_count = len(flags)

    def summary(self) -> dict:
        return {
            "flag_count": self.flag_count,
            "flags": [
                {
                    "rule_id": f.rule_id,
                    "severity": f.severity,
                    "penalty_pct": float(f.penalty_pct),
                }
                for f in self.flags
            ],
            "penalty_multiplier": float(self.penalty_multiplier),
            "final_bvss": float(self.final_bvss),
            "requires_manual_review": self.requires_manual_review,
        }