"""
Scoring rubrics — maps each possible answer value to a raw point score (0–100).
All rubrics return int scores; the engine applies sub-question weights.
"""


def score_industry_experience(years: int) -> int:
    if years < 1:
        return 15
    elif years < 2:
        return 30
    elif years < 5:
        return 55
    elif years < 10:
        return 75
    return 100


def score_loan_repayment_history(status: str) -> int:
    """
    status values: never_borrowed | fully_repaid | mostly_repaid |
                   partial_repayment | defaulted
    """
    mapping = {
        "fully_repaid": 95,
        "mostly_repaid": 60,
        "never_borrowed": 40,
        "partial_repayment": 25,
        "defaulted": 0,
    }
    return mapping.get(status, 0)


def score_savings_discipline(savings_type: str) -> int:
    """
    savings_type: both | stokvel_only | bank_only | past_member | neither
    """
    mapping = {
        "both": 100,
        "stokvel_only": 80,
        "bank_only": 70,
        "past_member": 30,
        "neither": 0,
    }
    return mapping.get(savings_type, 0)


def score_full_time_commitment(commitment: str) -> int:
    mapping = {
        "full_time_sole": 100,
        "full_time_side_income": 75,
        "part_time": 35,
        "side_project": 15,
    }
    return mapping.get(commitment, 0)


def score_training_mentorship(level: str) -> int:
    mapping = {
        "formal_certificate": 100,
        "multi_day_workshop": 75,
        "informal_mentoring": 50,
        "none": 15,
    }
    return mapping.get(level, 0)


def score_references_provided(count: int, contactable: bool) -> int:
    if count >= 2 and contactable:
        return 100
    elif count == 1 and contactable:
        return 50
    elif count >= 2:
        return 40
    return 0


# --- Pillar 2 ---

def score_monthly_revenue(bracket: str) -> int:
    mapping = {
        "under_1k": 15,
        "1k_3k": 35,
        "3k_8k": 60,
        "8k_20k": 80,
        "20k_50k": 90,
        "above_50k": 100,
    }
    return mapping.get(bracket, 0)


def score_revenue_consistency(consistency: str) -> int:
    mapping = {
        "very_consistent": 100,
        "small_variation": 80,
        "seasonal_predictable": 60,
        "unpredictable": 25,
        "very_irregular": 10,
    }
    return mapping.get(consistency, 0)


def score_profit_margin(pct: int) -> int:
    if pct > 35:
        return 100
    elif pct >= 20:
        return 80
    elif pct >= 10:
        return 55
    elif pct >= 5:
        return 30
    return 0


def score_existing_debt(status: str) -> int:
    mapping = {
        "no_debts": 100,
        "minor_manageable": 70,
        "moderate": 40,
        "heavy": 10,
        "in_arrears": 0,
    }
    return mapping.get(status, 0)


def score_momo_bonus(momo_verified: bool, frequency: str) -> int:
    if not momo_verified:
        return 0
    if frequency == "regular":
        return 20
    elif frequency == "occasional":
        return 10
    return 0


# --- Pillar 3 ---

def score_years_operating(years: int) -> int:
    if years < 0.5:
        return 0
    elif years < 1:
        return 20
    elif years < 2:
        return 45
    elif years < 5:
        return 70
    elif years < 10:
        return 90
    return 100


def score_customer_base(count: int) -> int:
    if count < 10:
        return 15
    elif count < 30:
        return 35
    elif count < 100:
        return 60
    elif count < 300:
        return 80
    return 100


def score_location_stability(location_type: str) -> int:
    mapping = {
        "own_permanent": 100,
        "rented_3yr_plus": 90,
        "rented_moved_once": 65,
        "market_stall": 45,
        "mobile_hawker": 25,
        "no_fixed_location": 10,
    }
    return mapping.get(location_type, 10)


def score_record_keeping(method: str) -> int:
    mapping = {
        "accounting_software": 100,
        "written_cashbook": 80,
        "phone_notes": 50,
        "mental_only": 20,
        "no_tracking": 0,
    }
    return mapping.get(method, 0)


# --- Pillar 4 ---

def score_demand_strength(level: str) -> int:
    mapping = {
        "more_than_capacity": 100,
        "strong_consistent": 80,
        "good_with_slow_periods": 60,
        "competitive": 35,
        "weak_declining": 10,
    }
    return mapping.get(level, 0)


def score_competitive_advantage(level: str) -> int:
    mapping = {
        "clear_unique": 100,
        "strong_quality": 75,
        "price_only": 50,
        "no_differentiation": 20,
    }
    return mapping.get(level, 0)


def score_growth_trajectory(growth: str) -> int:
    mapping = {
        "grew_significantly": 100,
        "grew_modestly": 75,
        "stayed_same": 40,
        "shrank_recovering": 20,
        "declined": 5,
    }
    return mapping.get(growth, 0)


def score_revenue_diversification(stream_count: int) -> int:
    if stream_count >= 4:
        return 100
    elif stream_count >= 2:
        return 70
    return 25


# --- Pillar 5 ---

def score_stokvel_membership(status: str) -> int:
    mapping = {
        "active_regular": 100,
        "active_irregular": 50,
        "past_voluntary": 30,
        "never_member": 15,
        "expelled": 0,
    }
    return mapping.get(status, 0)


def score_business_association(status: str) -> int:
    mapping = {
        "active_leadership": 100,
        "active_member": 70,
        "registered_inactive": 30,
        "not_member": 0,
    }
    return mapping.get(status, 0)


def score_guarantors(count: int, non_family: bool) -> int:
    if count >= 2 and non_family:
        return 100
    elif count == 1 and non_family:
        return 60
    elif count >= 1:
        return 25
    return 0


def score_community_reputation(level: str) -> int:
    mapping = {
        "well_known": 100,
        "known_by_many": 70,
        "somewhat_known": 40,
        "new_to_area": 15,
    }
    return mapping.get(level, 0)


# --- Pillar 6 ---

def score_debt_to_income(pct: int) -> int:
    if pct == 0:
        return 100
    elif pct <= 10:
        return 85
    elif pct <= 20:
        return 60
    elif pct <= 35:
        return 30
    elif pct <= 50:
        return 10
    return 0


def score_emergency_buffer(months: int) -> int:
    if months >= 3:
        return 100
    elif months >= 1:
        return 70
    elif months > 0:
        return 35
    return 0


def score_collateral(collateral_type: str) -> int:
    mapping = {
        "formal_property": 100,
        "vehicle": 75,
        "equipment_livestock": 55,
        "household_valuables": 30,
        "nothing": 15,
    }
    return mapping.get(collateral_type, 15)