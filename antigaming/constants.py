# apps/antigaming/constants.py

RULE_SEVERITIES = {
    "AGE_EXP_001":      ("critical", 50.00),
    "DEBT_CONT_001":    ("high",     12.00),
    "REV_EMP_001":      ("high",     10.00),
    "LOC_REV_001":      ("medium",    5.00),
    "STOK_SAV_001":     ("medium",    5.00),
    "BEH_REVISE_001":   ("medium",    5.00),
    "GROW_REV_001":     ("low",       2.00),
    "REV_CUST_001":     ("low",       2.00),
    "REV_SAV_001":      ("low",       2.00),
    "BEH_SPEED_001":    ("low",       2.00),
    "SOCIAL_DIVERGENCE_001": ("high", 0.00),  # handled via P5 cap
}

# Manual review is triggered by these rules
MANUAL_REVIEW_RULES = {"AGE_EXP_001", "DEBT_CONT_001"}

# GPS distance (km) beyond which a location mismatch flag is logged
GPS_MISMATCH_THRESHOLD_KM = 30

# Progressive disbursement ladder
DISBURSEMENT_LADDER = {
    "first_loan": 0.60,
    "after_3_payments": 0.80,
    "after_full_repayment": 1.00,
}

# Sector classification for REV_CUST_001
RETAIL_SECTORS = {"spaza", "food", "retail", "butchery", "general_trade"}