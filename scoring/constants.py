# Pillar weights — must sum to 1.0
PILLAR_WEIGHTS = {
    "p1": 0.20,   # Owner character
    "p2": 0.25,   # Financial performance
    "p3": 0.15,   # Business maturity
    "p4": 0.15,   # Market position
    "p5": 0.15,   # Social capital
    "p6": 0.10,   # Repayment capacity
}

# Within-pillar sub-question weights
P1_WEIGHTS = {
    "industry_experience": 0.20,
    "loan_repayment_history": 0.25,
    "savings_discipline": 0.20,
    "full_time_commitment": 0.15,
    "training_mentorship": 0.10,
    "references_provided": 0.10,
}

P2_WEIGHTS = {
    "monthly_revenue": 0.30,
    "revenue_consistency": 0.25,
    "profit_margin": 0.20,
    "existing_debt": 0.25,
}

P3_WEIGHTS = {
    "years_operating": 0.35,
    "customer_base_stability": 0.25,
    "location_stability": 0.20,
    "record_keeping": 0.20,
}

P4_WEIGHTS = {
    "demand_strength": 0.35,
    "competitive_advantage": 0.25,
    "growth_trajectory": 0.25,
    "revenue_diversification": 0.15,
}

P5_WEIGHTS = {
    "stokvel_membership": 0.30,
    "business_association": 0.20,
    "guarantors": 0.30,
    "community_reputation": 0.20,
}

P6_WEIGHTS = {
    "debt_to_income": 0.40,
    "emergency_buffer": 0.30,
    "collateral": 0.30,
}

# MoMo bonus ceiling (added to P2 raw before capping at 100)
MOMO_BONUS_MAX = 20

# Risk tier boundaries
TIER_BOUNDARIES = [
    ("A", 800, 1000),
    ("B", 650, 799),
    ("C", 500, 649),
    ("D", 350, 499),
    ("E", 0, 349),
]

# Revenue bracket midpoints (SZL) for loan calculation
REVENUE_MIDPOINTS = {
    "under_1k": 750,
    "1k_3k": 2000,
    "3k_8k": 5500,
    "8k_20k": 14000,
    "20k_50k": 35000,
    "above_50k": 60000,
}