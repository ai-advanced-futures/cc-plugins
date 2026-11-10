"""Canonical Magic Number computation — single source of truth.

Magic Number = (Quarterly Net New ARR × 4) / Prior Quarter S&M Spend

Annualizing the quarterly ARR (×4) before dividing normalizes the metric against
annual S&M spend, aligning with the standard SaaS benchmark where a score of
0.75 or more indicates healthy sales efficiency.

All callers (rule_of_40, unit_economics) delegate here
and adapt MagicNumberOutcome into their own output shapes. Do NOT re-implement the
×4 composition elsewhere (see tests/unit/test_magic_number.py single-source guard).
"""
from dataclasses import dataclass
from fractions import Fraction
from typing import Optional

from scripts.utils.calculators import safe_divide
from scripts.utils.constants import MAGIC_NUMBER_THRESHOLDS, assess_ratio_health
from scripts.utils.enums import MetricHealth
from scripts.utils.exact import Number, as_written


@dataclass(frozen=True)
class MagicNumberOutcome:
    """Canonical Magic Number result (single source of truth)."""

    magic_number: Optional[Fraction]
    health: MetricHealth
    interpretation: str


def calculate_magic_number(
    quarterly_net_new_arr: Number,
    prior_quarter_sm_spend: Number,
) -> MagicNumberOutcome:
    """Canonical Magic Number: (Quarterly Net New ARR × 4) / Prior Quarter S&M Spend.

    Args:
        quarterly_net_new_arr: Net new ARR added in the most recent quarter.
        prior_quarter_sm_spend: Sales & Marketing spend in the prior quarter.

    Returns:
        MagicNumberOutcome with the exact score (or None on zero spend), a typed
        MetricHealth band, and a plain-English interpretation string.
    """
    quarterly_net_new_arr = as_written(quarterly_net_new_arr)
    prior_quarter_sm_spend = as_written(prior_quarter_sm_spend)
    magic_number = safe_divide(quarterly_net_new_arr * 4, prior_quarter_sm_spend)
    if magic_number is None:
        return MagicNumberOutcome(
            None,
            MetricHealth.UNKNOWN,
            "Cannot calculate — prior quarter S&M spend is zero.",
        )
    # [LOCK-POINT A] negative-ARR handling: assess_ratio_health would return UNKNOWN
    # for a negative value (no threshold ≤ it), silently dropping the "declining"
    # signal. Intercept here so BOTH call sites surface the declining-ARR warning.
    if magic_number < 0:
        return MagicNumberOutcome(
            magic_number,
            MetricHealth.CRITICAL,
            "Negative Magic Number — ARR is declining; fix churn/retention.",
        )
    health = assess_ratio_health(magic_number, MAGIC_NUMBER_THRESHOLDS)
    interpretations = {
        MetricHealth.EXCELLENT: (
            "Strong sales efficiency (1.0 or more). Consider increasing S&M investment."
        ),
        MetricHealth.GOOD: "Healthy sales efficiency (0.75 up to 1.0). On track.",
        MetricHealth.WARNING: (
            "Below target (0.5 up to 0.75). Review sales process and marketing mix."
        ),
        MetricHealth.CRITICAL: (
            "Poor sales efficiency (under 0.5). Significant optimization needed."
        ),
    }
    return MagicNumberOutcome(
        magic_number,
        health,
        interpretations.get(health, ""),
    )
