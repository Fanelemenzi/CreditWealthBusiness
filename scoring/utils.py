from decimal import Decimal
from typing import Optional


def weighted_average(scores: dict, weights: dict) -> Decimal:
    """Compute a weighted average, returning a Decimal."""
    total = sum(
        Decimal(str(scores[k])) * Decimal(str(weights[k]))
        for k in weights
        if k in scores
    )
    return total.quantize(Decimal("0.01"))


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))


def tier_from_score(score: float) -> str:
    from scoring.constants import TIER_BOUNDARIES
    for tier, low, high in TIER_BOUNDARIES:
        if low <= score <= high:
            return tier
    return "E"


def revenue_midpoint(bracket: str) -> Optional[int]:
    from scoring.constants import REVENUE_MIDPOINTS
    return REVENUE_MIDPOINTS.get(bracket)


def penalty_description(rules_fired: list) -> str:
    """Human-readable summary of penalties (for admin display only)."""
    if not rules_fired:
        return "No penalties applied."
    lines = [f"- {r['rule_id']}: −{r['penalty_pct']}% ({r['severity']})" for r in rules_fired]
    return "\n".join(lines)