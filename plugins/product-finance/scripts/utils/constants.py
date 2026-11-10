"""
Centralized health thresholds and benchmark constants for the product-finance plugin.

Single source of truth — all scripts must import thresholds from here.
To update a threshold, change it HERE ONLY.

Threshold list format: [(upper_bound, MetricHealth), ...] ascending order.
Last entry must have float('inf') as upper bound.
Use assess_metric_health() for "lower is worse" metrics (CAC, churn, payback).
Use assess_ratio_health() for "higher is better" metrics (LTV:CAC, Magic Number).
"""
from scripts.utils.enums import MetricHealth

# ---------------------------------------------------------------------------
# CAC Thresholds (absolute USD) — lower is better
# ---------------------------------------------------------------------------
CAC_THRESHOLDS = [
    (100,          MetricHealth.EXCELLENT),   # Viral / product-led growth
    (500,          MetricHealth.GOOD),        # Healthy SMB acquisition
    (2_000,        MetricHealth.WARNING),     # Moderate — monitor
    (10_000,       MetricHealth.WARNING),     # Enterprise range — acceptable
    (float("inf"), MetricHealth.CRITICAL),
]

# ---------------------------------------------------------------------------
# LTV:CAC Ratio Thresholds — higher is better
# Format: [(lower_bound_inclusive, MetricHealth), ...] ascending order
# Use assess_ratio_health() — finds the LAST matching lower bound
# ---------------------------------------------------------------------------
LTV_CAC_THRESHOLDS = [
    (0.0,          MetricHealth.CRITICAL),    # < 1:1 — losing money
    (1.0,          MetricHealth.WARNING),     # 1:1 – 3:1 — below target
    (3.0,          MetricHealth.GOOD),        # 3:1 – 5:1 — healthy (3 inclusive)
    (5.0,          MetricHealth.EXCELLENT),   # > 5:1 — top quartile
]

# ---------------------------------------------------------------------------
# CAC Payback Period Thresholds (months) — lower is better
# ---------------------------------------------------------------------------
CAC_PAYBACK_THRESHOLDS = [
    (12,           MetricHealth.EXCELLENT),
    (18,           MetricHealth.GOOD),
    (24,           MetricHealth.WARNING),
    (float("inf"), MetricHealth.CRITICAL),
]

# ---------------------------------------------------------------------------
# Rule of 40 Thresholds (score = growth% + EBITDA margin%) — higher is better
# Format: [(lower_bound_inclusive, MetricHealth), ...] ascending order
# Use assess_ratio_health() for this threshold.
# ---------------------------------------------------------------------------
# These bands have no published source. They are kept only so that health_status does
# not change.
RULE_OF_40_THRESHOLDS = [
    (0,            MetricHealth.CRITICAL),   # score < 20 (lower-bound format)
    (20,           MetricHealth.WARNING),    # 20–30
    (30,           MetricHealth.GOOD),       # 30–40
    (40,           MetricHealth.EXCELLENT),  # >= 40
]

# ---------------------------------------------------------------------------
# AI Cost as % of Revenue — lower is better
# ---------------------------------------------------------------------------
AI_COST_THRESHOLDS = [
    (5,            MetricHealth.EXCELLENT),
    (10,           MetricHealth.GOOD),
    (20,           MetricHealth.WARNING),
    (float("inf"), MetricHealth.CRITICAL),
]

# ---------------------------------------------------------------------------
# Magic Number Thresholds — higher is better (use assess_ratio_health)
# ---------------------------------------------------------------------------
MAGIC_NUMBER_THRESHOLDS = [
    (0.0,          MetricHealth.CRITICAL),
    (0.5,          MetricHealth.WARNING),
    (0.75,         MetricHealth.GOOD),
    (1.0,          MetricHealth.EXCELLENT),
]

# ---------------------------------------------------------------------------
# Company Stage Definitions (ARR-based)
# ---------------------------------------------------------------------------
COMPANY_STAGES = {
    "early":  {"arr_min": 0,           "arr_max": 1_000_000,    "label": "Early Stage (<$1M ARR)"},
    "growth": {"arr_min": 1_000_000,   "arr_max": 10_000_000,   "label": "Growth Stage ($1M–$10M ARR)"},  # noqa: E501
    "scale":  {"arr_min": 10_000_000,  "arr_max": 50_000_000,   "label": "Scale Stage ($10M–$50M ARR)"},  # noqa: E501
    "mature": {"arr_min": 50_000_000,  "arr_max": float("inf"), "label": "Mature Stage (>$50M ARR)"},  # noqa: E501
}


def assess_metric_health(value: float, thresholds: list) -> MetricHealth:
    """
    Map a value to MetricHealth using ascending upper-bound thresholds.

    Use for metrics where LOWER is worse (CAC, churn rate, payback period).
    Finds the first threshold where value <= upper_bound.

    Args:
        value: The metric value to assess.
        thresholds: List of (upper_bound, MetricHealth) tuples, ascending.

    Returns:
        MetricHealth enum value.

    Example:
        assess_metric_health(300, CAC_THRESHOLDS) -> MetricHealth.GOOD
    """
    for upper_bound, health in thresholds:
        if value <= upper_bound:
            return health
    return MetricHealth.UNKNOWN


def assess_ratio_health(value: float, thresholds: list) -> MetricHealth:
    """
    Map a ratio value to MetricHealth using ascending lower-bound thresholds.

    Use for metrics where HIGHER is better (LTV:CAC, Magic Number, NRR).
    Finds the LAST threshold where value >= lower_bound.

    Args:
        value: The ratio value to assess.
        thresholds: List of (lower_bound_inclusive, MetricHealth) tuples, ascending.

    Returns:
        MetricHealth enum value.

    Example:
        assess_ratio_health(4.0, LTV_CAC_THRESHOLDS) -> MetricHealth.GOOD
    """
    result = MetricHealth.UNKNOWN
    for lower_bound, health in thresholds:
        if value >= lower_bound:
            result = health
    return result


def get_company_stage(arr: float) -> str:
    """
    Determine company stage from ARR value.

    Args:
        arr: Annual Recurring Revenue in dollars.

    Returns:
        Stage key: 'early', 'growth', 'scale', or 'mature'.
    """
    for stage_key, stage_data in COMPANY_STAGES.items():
        if stage_data["arr_min"] <= arr < stage_data["arr_max"]:
            return stage_key
    return "mature"
