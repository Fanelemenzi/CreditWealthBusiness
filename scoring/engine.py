from decimal import Decimal
from django.utils import timezone
from django.conf import settings

from scoring import rubrics
from scoring.constants import (
    PILLAR_WEIGHTS,
    P1_WEIGHTS, P2_WEIGHTS, P3_WEIGHTS,
    P4_WEIGHTS, P5_WEIGHTS, P6_WEIGHTS,
    MOMO_BONUS_MAX,
    TIER_BOUNDARIES,
    REVENUE_MIDPOINTS,
)


class ScoringEngine:
    """
    Computes all six pillar scores and the raw BVSS.
    Anti-gaming penalties are applied separately by FraudDetectionEngine.
    """

    def __init__(self, assessment):
        self.assessment = assessment
        self.p1 = assessment.pillar_1_data
        self.p2 = assessment.pillar_2_data
        self.p3 = assessment.pillar_3_data
        self.p4 = assessment.pillar_4_data
        self.p5 = assessment.pillar_5_data
        self.p6 = assessment.pillar_6_data

    def compute(self) -> dict:
        """
        Run all pillar scoring, return a results dict, and persist to the
        assessment model. Does NOT trigger anti-gaming — that runs via signal.
        """
        scores = {
            "p1": self._score_pillar_1(),
            "p2": self._score_pillar_2(),
            "p3": self._score_pillar_3(),
            "p4": self._score_pillar_4(),
            "p5": self._score_pillar_5(),
            "p6": self._score_pillar_6(),
            "p2_momo_bonus": self._score_momo_bonus(),
        }

        raw_bvss = sum(
            scores[k] * PILLAR_WEIGHTS[k]
            for k in ("p1", "p2", "p3", "p4", "p5", "p6")
        ) * 10  # scale to 0–1000

        scores["raw_bvss"] = round(raw_bvss, 2)
        self._persist(scores)
        return scores

    def _weighted(self, scores_map: dict, weights: dict) -> Decimal:
        total = sum(scores_map[k] * weights[k] for k in weights if k in scores_map)
        return Decimal(str(round(total, 2)))

    # ------------------------------------------------------------------ #
    # Pillar 1 — Owner character (weight: 20%)                            #
    # ------------------------------------------------------------------ #

    def _score_pillar_1(self) -> Decimal:
        sub = {
            "industry_experience": rubrics.score_industry_experience(
                self.p1.get("industry_experience_years", 0)
            ),
            "loan_repayment_history": rubrics.score_loan_repayment_history(
                self.p1.get("loan_repayment_status", "never_borrowed")
            ),
            "savings_discipline": rubrics.score_savings_discipline(
                self.p1.get("savings_type", "neither")
            ),
            "full_time_commitment": rubrics.score_full_time_commitment(
                self.p1.get("commitment_level", "part_time")
            ),
            "training_mentorship": rubrics.score_training_mentorship(
                self.p1.get("training_level", "none")
            ),
            "references_provided": rubrics.score_references_provided(
                count=self.p1.get("reference_count", 0),
                contactable=self.p1.get("references_contactable", False),
            ),
        }
        return self._weighted(sub, P1_WEIGHTS)

    # ------------------------------------------------------------------ #
    # Pillar 2 — Financial performance (weight: 25%)                      #
    # ------------------------------------------------------------------ #

    def _score_pillar_2(self) -> Decimal:
        sub = {
            "monthly_revenue": rubrics.score_monthly_revenue(
                self.p2.get("revenue_bracket", "under_1k")
            ),
            "revenue_consistency": rubrics.score_revenue_consistency(
                self.p2.get("revenue_consistency", "unpredictable")
            ),
            "profit_margin": rubrics.score_profit_margin(
                self.p2.get("profit_margin_pct", 0)
            ),
            "existing_debt": rubrics.score_existing_debt(
                self.p2.get("debt_status", "no_debts")
            ),
        }
        return self._weighted(sub, P2_WEIGHTS)

    def _score_momo_bonus(self) -> Decimal:
        bonus = rubrics.score_momo_bonus(
            momo_verified=self.p2.get("momo_verified", False),
            frequency=self.p2.get("momo_frequency", ""),
        )
        return Decimal(str(min(bonus, MOMO_BONUS_MAX)))

    # ------------------------------------------------------------------ #
    # Pillar 3 — Business maturity (weight: 15%)                          #
    # ------------------------------------------------------------------ #

    def _score_pillar_3(self) -> Decimal:
        sub = {
            "years_operating": rubrics.score_years_operating(
                self.p3.get("years_operating", 0)
            ),
            "customer_base_stability": rubrics.score_customer_base(
                self.p3.get("regular_customer_count", 0)
            ),
            "location_stability": rubrics.score_location_stability(
                self.p3.get("location_type", "no_fixed_location")
            ),
            "record_keeping": rubrics.score_record_keeping(
                self.p3.get("record_keeping_method", "no_tracking")
            ),
        }
        return self._weighted(sub, P3_WEIGHTS)

    # ------------------------------------------------------------------ #
    # Pillar 4 — Market position (weight: 15%)                            #
    # ------------------------------------------------------------------ #

    def _score_pillar_4(self) -> Decimal:
        sub = {
            "demand_strength": rubrics.score_demand_strength(
                self.p4.get("demand_level", "competitive")
            ),
            "competitive_advantage": rubrics.score_competitive_advantage(
                self.p4.get("advantage_level", "no_differentiation")
            ),
            "growth_trajectory": rubrics.score_growth_trajectory(
                self.p4.get("growth_2yr", "stayed_same")
            ),
            "revenue_diversification": rubrics.score_revenue_diversification(
                self.p4.get("revenue_stream_count", 1)
            ),
        }
        return self._weighted(sub, P4_WEIGHTS)

    # ------------------------------------------------------------------ #
    # Pillar 5 — Social capital (weight: 15%)                             #
    # ------------------------------------------------------------------ #

    def _score_pillar_5(self) -> Decimal:
        sub = {
            "stokvel_membership": rubrics.score_stokvel_membership(
                self.p5.get("stokvel_status", "never_member")
            ),
            "business_association": rubrics.score_business_association(
                self.p5.get("association_status", "not_member")
            ),
            "guarantors": rubrics.score_guarantors(
                count=self.p5.get("guarantor_count", 0),
                non_family=self.p5.get("guarantors_non_family", False),
            ),
            "community_reputation": rubrics.score_community_reputation(
                self.p5.get("community_reputation", "new_to_area")
            ),
        }
        return self._weighted(sub, P5_WEIGHTS)

    # ------------------------------------------------------------------ #
    # Pillar 6 — Repayment capacity (weight: 10%)                         #
    # ------------------------------------------------------------------ #

    def _score_pillar_6(self) -> Decimal:
        sub = {
            "debt_to_income": rubrics.score_debt_to_income(
                self.p6.get("debt_to_income_pct", 0)
            ),
            "emergency_buffer": rubrics.score_emergency_buffer(
                self.p6.get("emergency_buffer_months", 0)
            ),
            "collateral": rubrics.score_collateral(
                self.p6.get("collateral_type", "nothing")
            ),
        }
        return self._weighted(sub, P6_WEIGHTS)

    # ------------------------------------------------------------------ #
    # Persist                                                             #
    # ------------------------------------------------------------------ #

    def _persist(self, scores: dict):
        from django.utils import timezone

        a = self.assessment
        a.score_p1 = scores["p1"]
        a.score_p2 = scores["p2"]
        a.score_p3 = scores["p3"]
        a.score_p4 = scores["p4"]
        a.score_p5 = scores["p5"]
        a.score_p6 = scores["p6"]
        a.score_p2_momo_bonus = scores["p2_momo_bonus"]
        a.raw_bvss = scores["raw_bvss"]
        a.save(update_fields=[
            "score_p1", "score_p2", "score_p3", "score_p4",
            "score_p5", "score_p6", "score_p2_momo_bonus", "raw_bvss",
        ])


def assign_risk_tier(score: float) -> str:
    for tier, low, high in TIER_BOUNDARIES:
        if low <= score <= high:
            return tier
    return "E"