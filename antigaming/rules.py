"""
Each rule is a standalone callable that accepts an Assessment instance and
returns a FraudFlagResult (or None if no violation detected).
"""
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal


@dataclass
class FraudFlagResult:
    rule_id: str
    severity: str        # low | medium | high | critical
    penalty_pct: Decimal  # percentage to subtract from raw score
    description: str
    pillars_involved: str


def rule_age_exp_001(assessment) -> Optional[FraudFlagResult]:
    """
    AGE_EXP_001 — Critical
    Business start date implies the owner was under 14 years old at founding.
    Flag: (current_year - birth_year) - business_years_operating < 14
    """
    owner = assessment.owner
    business_years = assessment.pillar_3_data.get("years_operating", 0)
    if owner.age - business_years < 14:
        return FraudFlagResult(
            rule_id="AGE_EXP_001",
            severity="critical",
            penalty_pct=Decimal("50.00"),
            description=(
                f"Owner age ({owner.age}) minus declared years in business "
                f"({business_years}) implies business started when owner was "
                f"younger than 14. National ID date of birth used as reference."
            ),
            pillars_involved="P1, P3",
        )
    return None


def rule_debt_cont_001(assessment) -> Optional[FraudFlagResult]:
    """
    DEBT_CONT_001 — High
    Pillar 2 declares no existing debts, but Pillar 6 declares a positive
    debt-to-income ratio.
    """
    p2_debt_status = assessment.pillar_2_data.get("debt_status", "")
    p6_dti = assessment.pillar_6_data.get("debt_to_income_pct", 0)

    if p2_debt_status == "no_debts" and p6_dti > 0:
        return FraudFlagResult(
            rule_id="DEBT_CONT_001",
            severity="high",
            penalty_pct=Decimal("12.00"),
            description=(
                f"Pillar 2 declares no existing business debts, but Pillar 6 "
                f"reports {p6_dti}% of revenue goes to debt repayments. "
                "Direct contradiction across pillars."
            ),
            pillars_involved="P2, P6",
        )
    return None


def rule_rev_emp_001(assessment) -> Optional[FraudFlagResult]:
    """
    REV_EMP_001 — High
    Declared revenue cannot cover the declared employee payroll at minimum wage.
    Eswatini minimum wage: ~E1,500/month per employee.
    """
    from scoring.constants import REVENUE_MIDPOINTS
    MINIMUM_WAGE_PER_EMPLOYEE = 1500  # SZL

    revenue_bracket = assessment.pillar_2_data.get("revenue_bracket", "under_1k")
    monthly_revenue = REVENUE_MIDPOINTS.get(revenue_bracket, 0)
    employee_count = assessment.pillar_3_data.get("employee_count", 0)

    if employee_count == 0:
        return None

    min_payroll = employee_count * MINIMUM_WAGE_PER_EMPLOYEE
    if monthly_revenue < min_payroll:
        return FraudFlagResult(
            rule_id="REV_EMP_001",
            severity="high",
            penalty_pct=Decimal("10.00"),
            description=(
                f"Declared monthly revenue (E{monthly_revenue:,}) is less than "
                f"minimum wage payroll for {employee_count} employees "
                f"(E{min_payroll:,}/month). Revenue cannot support declared workforce."
            ),
            pillars_involved="P2, P3",
        )
    return None


def rule_loc_rev_001(assessment) -> Optional[FraudFlagResult]:
    """
    LOC_REV_001 — Medium
    Mobile hawker / no fixed location claiming revenue above E20,000/month.
    At that revenue level, premises rental is affordable and expected.
    """
    location_type = assessment.pillar_3_data.get("location_type", "")
    revenue_bracket = assessment.pillar_2_data.get("revenue_bracket", "")

    mobile_types = {"mobile_hawker", "no_fixed_location"}
    high_revenue_brackets = {"20k_50k", "above_50k"}

    if location_type in mobile_types and revenue_bracket in high_revenue_brackets:
        return FraudFlagResult(
            rule_id="LOC_REV_001",
            severity="medium",
            penalty_pct=Decimal("5.00"),
            description=(
                f"Location type '{location_type}' is inconsistent with declared "
                f"revenue bracket '{revenue_bracket}'. A business at this revenue "
                "level would typically afford permanent premises."
            ),
            pillars_involved="P2, P3",
        )
    return None


def rule_stok_sav_001(assessment) -> Optional[FraudFlagResult]:
    """
    STOK_SAV_001 — Medium
    Active stokvel member with zero savings discipline.
    Stokvel participation requires monthly contributions — these are savings.
    """
    stokvel_status = assessment.pillar_5_data.get("stokvel_status", "")
    savings_type = assessment.pillar_1_data.get("savings_type", "")
    buffer_months = assessment.pillar_6_data.get("emergency_buffer_months", 0)

    if (
        stokvel_status == "active_regular"
        and savings_type == "neither"
        and buffer_months == 0
    ):
        return FraudFlagResult(
            rule_id="STOK_SAV_001",
            severity="medium",
            penalty_pct=Decimal("5.00"),
            description=(
                "Active stokvel membership requires monthly cash contributions "
                "which constitute savings, but Pillar 1 declares no savings "
                "discipline and Pillar 6 declares zero emergency buffer."
            ),
            pillars_involved="P1, P5, P6",
        )
    return None


def rule_grow_rev_001(assessment) -> Optional[FraudFlagResult]:
    """
    GROW_REV_001 — Low
    Claims significant 2-year growth but sits in the lowest revenue bracket.
    If the business grew significantly, current revenue should reflect that.
    """
    growth = assessment.pillar_4_data.get("growth_2yr", "")
    revenue_bracket = assessment.pillar_2_data.get("revenue_bracket", "")

    if growth == "grew_significantly" and revenue_bracket == "under_1k":
        return FraudFlagResult(
            rule_id="GROW_REV_001",
            severity="low",
            penalty_pct=Decimal("2.00"),
            description=(
                "Pillar 4 claims significant growth over 2 years, but declared "
                "monthly revenue is under E1,000 — inconsistent with a "
                "business that has grown significantly."
            ),
            pillars_involved="P2, P4",
        )
    return None


def rule_rev_cust_001(assessment) -> Optional[FraudFlagResult]:
    """
    REV_CUST_001 — Low
    Implied average spend per regular customer is implausibly low
    for the declared sector.
    Threshold: below E10/customer/month for retail/food sectors.
    """
    from scoring.constants import REVENUE_MIDPOINTS

    revenue_bracket = assessment.pillar_2_data.get("revenue_bracket", "under_1k")
    monthly_revenue = REVENUE_MIDPOINTS.get(revenue_bracket, 0)
    customer_count = assessment.pillar_3_data.get("regular_customer_count", 0)
    sector = assessment.pillar_4_data.get("sector", "")

    retail_sectors = {"spaza", "food", "retail", "butchery", "general_trade"}

    if customer_count == 0 or sector not in retail_sectors:
        return None

    implied_spend = monthly_revenue / customer_count
    if implied_spend < 10:
        return FraudFlagResult(
            rule_id="REV_CUST_001",
            severity="low",
            penalty_pct=Decimal("2.00"),
            description=(
                f"Implied monthly spend per customer is E{implied_spend:.2f} "
                f"({customer_count} customers, E{monthly_revenue:,}/month). "
                "This is below E10 — implausible for retail/food sector."
            ),
            pillars_involved="P2, P3",
        )
    return None


def rule_rev_sav_001(assessment) -> Optional[FraudFlagResult]:
    """
    REV_SAV_001 — Low
    High revenue AND high profit margin with zero emergency savings.
    At this profitability level some cash accumulation is behaviorally expected.
    """
    revenue_bracket = assessment.pillar_2_data.get("revenue_bracket", "")
    profit_margin = assessment.pillar_2_data.get("profit_margin_pct", 0)
    buffer_months = assessment.pillar_6_data.get("emergency_buffer_months", 0)

    high_rev = revenue_bracket in {"20k_50k", "above_50k"}
    high_margin = profit_margin >= 30

    if high_rev and high_margin and buffer_months == 0:
        return FraudFlagResult(
            rule_id="REV_SAV_001",
            severity="low",
            penalty_pct=Decimal("2.00"),
            description=(
                f"Revenue bracket '{revenue_bracket}' and profit margin "
                f"{profit_margin}% are high, but emergency savings buffer is "
                "zero. Declared profitability not reflected in cash reserves."
            ),
            pillars_involved="P2, P6",
        )
    return None