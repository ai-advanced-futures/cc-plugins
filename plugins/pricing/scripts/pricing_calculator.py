# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Pricing Plugin — Core Calculation Module

Author: Luis F. Amadeo (Chief Agentic Officer)
Version: 1.2.0

Frameworks:
  - Amadeo: VALUE = Speed × Accuracy of Outcome
  - Amadeo: Agentic Tier Classification + Cost-of-Replacement Pricing
  - Ramanujam: Leader/Filler/Killer classification, Good/Better/Best packaging
  - Campbell: Value metric criteria, per-user antipattern detection
  - Helmer: 7 Powers moat multiplier, Scale Economy advisory
"""

from __future__ import annotations

import dataclasses
import json
import math
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class FeatureClassification(Enum):
    LEGACY = "legacy"
    HYBRID = "hybrid"
    AI_ERA = "ai_era"


class RamanujamCategory(Enum):
    LEADER = "leader"
    FILLER = "filler"
    KILLER = "killer"


class FreemiumGateType(Enum):
    NO_FREE_TIER = "no_free_tier"
    TRIAL_GATE = "trial_gate"
    FREEMIUM_USAGE_LIMITED = "freemium_usage_limited"
    FREEMIUM_FEATURE_LIMITED = "freemium_feature_limited"


class ConfidenceTier(Enum):
    VALIDATED = "validated"
    ESTIMATED = "estimated"


class AgenticTier(Enum):
    COMMODITY     = "commodity"
    AUGMENTED     = "augmented"
    AUTONOMOUS    = "autonomous"
    FULLY_AGENTIC = "fully_agentic"


# ---------------------------------------------------------------------------
# Data Classes — Audit
# ---------------------------------------------------------------------------


@dataclass
class Layer1Score:
    """5-dimension 0/1 scoring for AI-era fast triage (Layer 1 rubric)."""

    uses_ml_inference: bool          # Feature uses ML/AI inference as primary value delivery
    quality_improves_over_time: bool # Outcome quality improves as feature accumulates data/usage
    faster_than_manual: bool         # Speed of outcome delivery measurably faster than non-AI alt
    ai_causes_value: bool            # AI mechanism is direct cause of value (vs underlying dataset)
    ai_rare_in_market: bool          # AI capability rare in current competitive landscape

    @property
    def score(self) -> int:
        return sum([
            self.uses_ml_inference,
            self.quality_improves_over_time,
            self.faster_than_manual,
            self.ai_causes_value,
            self.ai_rare_in_market,
        ])


@dataclass
class Layer2Gate:
    """3-condition gate for AI_MULTIPLIER > 5x (Layer 2 rubric)."""

    has_autonomy: bool      # Feature executes without human intervention on primary job
    has_compounding: bool   # Value increases with usage over time (not fixed at training)
    has_attribution: bool   # Speed×Accuracy improvement causally isolatable vs non-AI equivalent


@dataclass
class AgenticClassification:
    """Output of the 4-question agentic tier classification rubric."""

    tier: AgenticTier
    is_generic_ai: bool
    has_multi_step_execution: bool
    human_review_required: bool
    replaces_human_role: bool


@dataclass
class MetricScore:
    """Campbell criteria scoring for a value metric candidate."""

    alignment_score: int        # 0 or 1: metric reflects value delivered to customer
    understandability_score: int # 0 or 1: customer understands and can control the metric
    growth_alignment_score: int  # 0 or 1: growth in metric equals growth in customer value
    ai_era_alignment: int        # 0 or 1: metric scales with Speed × Accuracy of Outcome

    @property
    def total_score(self) -> int:
        return (
            self.alignment_score
            + self.understandability_score
            + self.growth_alignment_score
            + self.ai_era_alignment
        )

    @property
    def is_campbell_approved(self) -> bool:
        return self.total_score >= 3


# ---------------------------------------------------------------------------
# Data Classes — Price Results
# ---------------------------------------------------------------------------


@dataclass
class PathBResult:
    """Output of Path B (data-poor) dual-output pricing formula."""

    right_price: float           # max(MARGIN_FLOOR, min(WTP_max, BASE × AI_MULT × MOAT_MULT))
    value_signal: float          # Unconstrained BASE × AI_MULT × MOAT_MULT — strategic gap signal
    confidence_tier: str         # Always "estimated" for Path B
    margin_floor: float          # Computed MARGIN_FLOOR used in formula
    segment_signal: Optional[dict]  # Present when value_signal > wtp_max; dict keys: wtf_gap (WTP-Fit Gap = value_signal - wtp_max), interpretation
    moat_advisory: Optional[str]    # Penetration pricing advisory if Scale Economy detected


@dataclass
class PathAResult:
    """Output of Path A (data-rich) EVC additive pricing formula."""

    right_price: float           # min(WTP_max, VALUE_SIGNAL); VALUE_SIGNAL when WTP_max is None
    evc: float                   # EVC used: it bounds the formula; WTP_max caps the price
    confidence_tier: str         # Always "validated" for Path A
    margin_floor: float          # Computed MARGIN_FLOOR used in formula
    segment_signal: Optional[dict]  # Present when additive_sum > wtp_max: headroom, not a market gap
    value_signal: float          # max(MARGIN_FLOOR, min(EVC, REF + AI_DELTA + MOAT_DELTA)): the price before the WTP cap
    floor_advisory: Optional[str] = None  # Present when MARGIN_FLOOR > WTP_max: the capped price is below the floor


@dataclass
class AiMultiplierResult:
    """Output of compute_ai_multiplier() — multiplier value + fear signal flag."""

    multiplier: float        # AI_MULTIPLIER value (1.0 when fear signal fires)
    fear_signal_triggered: bool  # True when accuracy_improvement < accuracy_fear_signal_threshold


@dataclass
class PathCAutonomousResult:
    """Output of Path C-Autonomous (transaction-based) pricing formula."""

    right_price: float          # max(MARGIN_FLOOR, min(WTP_MAX_PER_TASK, TASK_VALUE × capture_rate))
    task_value: float           # time_saved_per_task × hourly_cost_of_human
    value_capture_rate: float   # fraction of task value the vendor captures
    confidence_tier: str        # Always "estimated" for Path C
    margin_floor: float         # Computed MARGIN_FLOOR used in formula
    pricing_unit: str           # Always "per task"


@dataclass
class PathCFullyAgenticPriced:
    """
    Output when Path C-Fully Agentic completes pricing normally.
    Returned when automation_rate >= automation_rate_fear_signal_threshold.
    """

    right_price: float          # max(MARGIN_FLOOR, min(WTP_MAX_ANNUAL, AUTOMATION_VALUE × value_share))
    replacement_cost: float     # annual_salary × (1 + overhead_rate)
    automation_rate: float      # fraction of the human role the agent covers
    value_share: float          # fraction of replacement value the vendor captures
    confidence_tier: str        # Always "estimated"
    margin_floor: float         # Computed MARGIN_FLOOR used in formula
    pricing_unit: str           # Always "per agent per year"
    risk_advisory: Optional[str]  # None for priced case (automation_rate >= threshold)


@dataclass
class PathCFullyAgenticReclassified:
    """
    Output when Path C-Fully Agentic reclassifies to Autonomous path.
    Returned when automation_rate < automation_rate_fear_signal_threshold.
    right_price is intentionally absent — this case must not produce a price.
    """

    reclassification_path: str          # Always "C-autonomous"
    recovery_inputs_required: list[str] # Inputs needed for C-Autonomous pricing
    risk_advisory: str                  # Non-optional: explains why reclassification occurred
    confidence_tier: str                # Always "estimated"
    pricing_unit: str                   # Always "per task"


# ---------------------------------------------------------------------------
# Audit Functions
# ---------------------------------------------------------------------------


def classify_layer1(layer1: Layer1Score) -> FeatureClassification:
    """
    Classify a feature using Layer 1 fast triage rubric.

    Scoring:
      0–2 → LEGACY
      3–4 → HYBRID
        5 → AI_ERA (provisionally)
    """
    score = layer1.score
    if score <= 2:
        return FeatureClassification.LEGACY
    if score <= 4:
        return FeatureClassification.HYBRID
    return FeatureClassification.AI_ERA


def apply_layer2_gate(layer2: Layer2Gate) -> bool:
    """
    Apply Layer 2 high-multiplier gate (only used when AI_MULTIPLIER would exceed 5x).

    Returns True only when ALL THREE conditions are satisfied.
    If any condition fails, AI_MULTIPLIER is capped at 5x.
    """
    return layer2.has_autonomy and layer2.has_compounding and layer2.has_attribution


def classify_agentic_tier(
    is_generic_ai: bool,
    has_multi_step_execution: bool,
    human_review_required: bool,
    replaces_human_role: bool,
) -> AgenticClassification:
    """
    Classify a feature on the 4-tier agentic spectrum using the Amadeo decision tree.

    Decision tree (evaluated in order):
      1. is_generic_ai            → COMMODITY
      2. not has_multi_step       → AUGMENTED  (route to Path A/B)
      3. human_review_required    → AUTONOMOUS (Path C-Autonomous)
      4. replaces_human_role      → FULLY_AGENTIC (Path C-Fully Agentic)
      5. default                  → AUTONOMOUS (conservative)
    """
    if is_generic_ai:
        tier = AgenticTier.COMMODITY
    elif not has_multi_step_execution:
        tier = AgenticTier.AUGMENTED
    elif human_review_required:
        tier = AgenticTier.AUTONOMOUS
    elif replaces_human_role:
        tier = AgenticTier.FULLY_AGENTIC
    else:
        tier = AgenticTier.AUTONOMOUS  # conservative default

    return AgenticClassification(
        tier=tier,
        is_generic_ai=is_generic_ai,
        has_multi_step_execution=has_multi_step_execution,
        human_review_required=human_review_required,
        replaces_human_role=replaces_human_role,
    )


def compute_review_window(competitor_count: Optional[int]) -> tuple[int, bool]:
    """
    Compute the AI-era classification review window in months.

    Formula: review_window_months = 36 / log2(1 + competitor_count)
    Range: [6, 36] months.

    Returns:
      (months: int, is_placeholder: bool)
      is_placeholder=True when competitor_count is None (18-month conservative default).
    """
    if competitor_count is None:
        return (18, True)
    if competitor_count == 0:
        return (36, False)
    raw = 36.0 / math.log2(1 + competitor_count)
    months = max(6, min(36, round(raw)))
    return (int(months), False)


# ---------------------------------------------------------------------------
# Price Computation Functions
# ---------------------------------------------------------------------------


def compute_ai_multiplier(
    speed_improvement: float,
    accuracy_improvement: float,
    accuracy_fear_signal_threshold: float,
) -> AiMultiplierResult:
    """
    Compute AI_MULTIPLIER from speed and accuracy improvements.

    Formula: AI_MULTIPLIER = 1.0 + (speed_improvement × accuracy_improvement)

    Parameters:
      speed_improvement: Ratio multiplier (e.g., 3.0 = 3x faster than non-AI alt)
      accuracy_improvement: Quality fraction (0–1 scale, e.g., 0.9 = 90% accuracy)
      accuracy_fear_signal_threshold: Config-governed threshold from defaults.json
        path_b.accuracy_fear_signal_threshold (required — no default)

    Fear signal: accuracy_improvement < threshold → multiplier = 1.0, fear_signal_triggered = True

    Raises:
      ValueError: if speed_improvement < 0.0
      ValueError: if accuracy_improvement < 0.0
      ValueError: if accuracy_fear_signal_threshold not in (0.0, 1.0]
    """
    if speed_improvement < 0.0:
        raise ValueError(
            f"speed_improvement must be >= 0.0, got {speed_improvement}"
        )
    if accuracy_improvement < 0.0:
        raise ValueError(
            f"accuracy_improvement must be >= 0.0, got {accuracy_improvement}"
        )
    if not (0.0 < accuracy_fear_signal_threshold <= 1.0):
        raise ValueError(
            f"accuracy_fear_signal_threshold must be in (0.0, 1.0], got {accuracy_fear_signal_threshold}"
        )
    if accuracy_improvement < accuracy_fear_signal_threshold:
        return AiMultiplierResult(multiplier=1.0, fear_signal_triggered=True)
    return AiMultiplierResult(
        multiplier=1.0 + (speed_improvement * accuracy_improvement),
        fear_signal_triggered=False,
    )


def compute_moat_multiplier(
    helmer_score: float, is_scale_economy: bool
) -> tuple[float, Optional[str]]:
    """
    Compute MOAT_MULTIPLIER from Helmer 7 Powers assessment.

    Rules:
      - Floor: 1.0, ceiling: 2.5
      - Scale Economy moats: floor locked at 1.0 + penetration pricing advisory (type-based trigger)
    """
    _SCALE_ECONOMY_ADVISORY = (
        "Penetration pricing advisory: Scale Economy moat detected. "
        "Your pricing power comes from volume, not premium. "
        "Consider pricing below competitors to accelerate volume growth and widen the cost advantage. "
        "MOAT_MULTIPLIER locked at 1.0."
    )
    if is_scale_economy:
        return (1.0, _SCALE_ECONOMY_ADVISORY)
    multiplier = max(1.0, min(2.5, helmer_score))
    return (multiplier, None)


def compute_margin_floor(production_cost: float, target_margin: float) -> float:
    """
    Compute MARGIN_FLOOR = PRODUCTION_COST / (1 - target_margin).

    Returns 0.0 when production_cost is 0.

    Raises:
      ValueError: if production_cost < 0.0
      ValueError: if target_margin < 0.0 or target_margin >= 1.0

    Note (v1.3): A `margin_floor > wtp_max` guard is intentionally deferred. This function
    does not receive wtp_max, and the formula callers handle this case gracefully via
    `max(margin_floor, min(wtp_max, ...))` — margin_floor > wtp_max produces right_price = margin_floor,
    which is the correct behavior (cost floor takes precedence over market ceiling).
    """
    if production_cost < 0.0:
        raise ValueError(f"production_cost must be >= 0.0, got {production_cost}")
    if target_margin < 0.0 or target_margin >= 1.0:
        raise ValueError(
            f"target_margin must be in [0.0, 1.0), got {target_margin}"
        )
    if production_cost == 0.0:
        return 0.0
    return production_cost / (1.0 - target_margin)


def compute_path_b(
    base_price: float,
    ai_multiplier: float,
    moat_multiplier: float,
    margin_floor: float,
    wtp_max: float,
) -> PathBResult:
    """
    Compute Path B (data-poor) dual-output pricing formula.

    Formula:
      RIGHT_PRICE = max(MARGIN_FLOOR, min(WTP_max, BASE × AI_MULT × MOAT_MULT))
      VALUE_SIGNAL = BASE × AI_MULT × MOAT_MULT  [unconstrained — strategic gap signal]
    """
    value_signal = base_price * ai_multiplier * moat_multiplier
    right_price = max(margin_floor, min(wtp_max, value_signal))

    segment_signal: Optional[dict] = None
    if value_signal > wtp_max:
        segment_signal = {
            "wtf_gap": value_signal - wtp_max,
            "interpretation": (
                "Addressable market at value-justified price exceeds current WTP ceiling. "
                "Consider running jtbd-market-discovery to validate and expand WTP."
            ),
        }

    return PathBResult(
        right_price=right_price,
        value_signal=value_signal,
        confidence_tier="estimated",
        margin_floor=margin_floor,
        segment_signal=segment_signal,
        moat_advisory=None,
    )


def compute_path_a(
    reference_price: float,
    ai_value_delta: float,
    moat_value_delta: float,
    margin_floor: float,
    evc: float,
    wtp_max: Optional[float],
    price_period: Optional[str] = None,
    unit_period: Optional[str] = None,
) -> PathAResult:
    """
    Compute Path A (data-rich) EVC additive pricing formula.

    Formula:
      VALUE_SIGNAL = max(MARGIN_FLOOR, min(EVC, REFERENCE_PRICE + AI_VALUE_DELTA + MOAT_VALUE_DELTA))
      RIGHT_PRICE  = min(WTP_max, VALUE_SIGNAL)   (VALUE_SIGNAL when WTP_max is None)

    Parameters:
      wtp_max: the highest willingness to pay jtbd measured for the segment. A Path A
               price never exceeds it (operator ruling T7-2); a higher VALUE_SIGNAL is
               headroom, not the price. None leaves the price uncapped.
               Also sets segment_signal when the additive sum exceeds it.
      price_period, unit_period: the price's period (the jtbd willingness to pay's) and the
               period of an answered pricing unit. When they differ, every money figure is
               converted after the cap: x12 from month to year, /12 from year to month. Any
               other pair raises ValueError, which the run records as a gap.

    Segment signal: when additive_sum > wtp_max, emits Path B's segment_signal structure with a
    Path A interpretation: headroom, not a market gap.
    """
    to_unit = _period_converter(price_period, unit_period)
    additive_sum = reference_price + ai_value_delta + moat_value_delta
    value_signal = max(margin_floor, min(evc, additive_sum))
    right_price = value_signal if wtp_max is None else min(wtp_max, value_signal)
    # re-review N1: convert after the cap, so the cap holds in either period
    value_signal, right_price, margin_floor, evc, additive_sum = (
        to_unit(x) for x in (value_signal, right_price, margin_floor, evc, additive_sum))
    wtp_max = None if wtp_max is None else to_unit(wtp_max)
    floor_advisory: Optional[str] = None
    if wtp_max is not None and margin_floor > wtp_max:  # T7-2: the cap wins over the floor, visibly
        floor_advisory = (
            "Below margin floor: the price is capped at the highest willingness to pay (%g), "
            "which is below the margin floor (%g), so the offering does not clear its margin floor "
            "at this willingness to pay." % (wtp_max, margin_floor)
        )

    segment_signal: Optional[dict] = None
    if wtp_max is not None and additive_sum > wtp_max:
        segment_signal = {
            "wtf_gap": additive_sum - wtp_max,
            "interpretation": (
                "Path A headroom: the value the jtbd data supports is above the highest willingness to pay jtbd "
                "measured, so the price is capped at that willingness to pay. This is headroom, not a market gap."
            ),
        }

    return PathAResult(
        right_price=right_price,
        evc=evc,
        confidence_tier="validated",
        margin_floor=margin_floor,
        segment_signal=segment_signal,
        value_signal=value_signal,
        floor_advisory=floor_advisory,
    )


def _period_converter(price_period: Optional[str], unit_period: Optional[str]):
    """The x12 / /12 rule from the price's period to the unit's; identity when they agree."""
    if price_period is None and unit_period is None:
        return lambda x: x
    if price_period is None or unit_period is None:
        raise ValueError("price_period and unit_period go together: got %r and %r" % (price_period, unit_period))
    if price_period == unit_period:
        return lambda x: x
    if (price_period, unit_period) == ("month", "year"):
        return lambda x: x * 12
    if (price_period, unit_period) == ("year", "month"):
        return lambda x: x / 12
    raise ValueError("pricing unit has a period the price cannot take: %s to %s" % (price_period, unit_period))


def compute_path_c_autonomous(
    time_saved_per_task: float,
    hourly_cost_of_human: float,
    value_capture_rate: float,
    margin_floor: float,
    wtp_max_per_task: float,
) -> PathCAutonomousResult:
    """
    Compute Path C-Autonomous (transaction-based) pricing formula.

    Formula:
      TASK_VALUE  = time_saved_per_task × hourly_cost_of_human
      RIGHT_PRICE = max(MARGIN_FLOOR, min(WTP_MAX_PER_TASK, TASK_VALUE × value_capture_rate))
    """
    task_value = time_saved_per_task * hourly_cost_of_human
    right_price = max(margin_floor, min(wtp_max_per_task, task_value * value_capture_rate))

    return PathCAutonomousResult(
        right_price=right_price,
        task_value=task_value,
        value_capture_rate=value_capture_rate,
        confidence_tier="estimated",
        margin_floor=margin_floor,
        pricing_unit="per task",
    )


def compute_path_c_fully_agentic(
    annual_salary: float,
    overhead_rate: float,
    automation_rate: float,
    value_share: float,
    margin_floor: float,
    wtp_max_annual: float,
    automation_rate_fear_signal_threshold: float,
) -> PathCFullyAgenticPriced | PathCFullyAgenticReclassified:
    """
    Compute Path C-Fully Agentic (cost-of-replacement) pricing formula.

    Formula:
      REPLACEMENT_COST = annual_salary × (1 + overhead_rate)
      AUTOMATION_VALUE = REPLACEMENT_COST × automation_rate
      RIGHT_PRICE      = max(MARGIN_FLOOR, min(WTP_MAX_ANNUAL, AUTOMATION_VALUE × value_share))

    Reclassification gate: automation_rate < threshold → PathCFullyAgenticReclassified.
    No price is computed when the agent does not cover enough of the role.
    """
    _FEAR_ADVISORY = (
        f"Agent covers less than {int(automation_rate_fear_signal_threshold * 100)}% of the role "
        "— customer still needs a human for the remainder. "
        "Consider positioning as Autonomous (with human-in-the-loop) and pricing per task instead."
    )

    if automation_rate < automation_rate_fear_signal_threshold:
        return PathCFullyAgenticReclassified(
            reclassification_path="C-autonomous",
            recovery_inputs_required=[
                "time_saved_per_task",
                "hourly_cost_of_human",
                "wtp_max_per_task",
            ],
            risk_advisory=_FEAR_ADVISORY,
            confidence_tier="estimated",
            pricing_unit="per task",
        )

    replacement_cost = annual_salary * (1.0 + overhead_rate)
    automation_value = replacement_cost * automation_rate
    right_price = max(margin_floor, min(wtp_max_annual, automation_value * value_share))

    return PathCFullyAgenticPriced(
        right_price=right_price,
        replacement_cost=replacement_cost,
        automation_rate=automation_rate,
        value_share=value_share,
        confidence_tier="estimated",
        margin_floor=margin_floor,
        pricing_unit="per agent per year",
        risk_advisory=None,
    )


# ---------------------------------------------------------------------------
# Value Metric Functions
# ---------------------------------------------------------------------------


def evaluate_value_metric(
    customer_can_control: bool,
    customer_wants_it_to_grow: bool,
    aligns_with_value_delivered: bool,
    aligns_with_ai_outcome: bool,
) -> MetricScore:
    """
    Score a value metric candidate against Campbell's 3 criteria + Amadeo AI-era test.

    Dimension mapping:
      alignment_score        ← aligns_with_value_delivered
      understandability_score ← customer_can_control
      growth_alignment_score  ← customer_wants_it_to_grow
      ai_era_alignment        ← aligns_with_ai_outcome
    """
    return MetricScore(
        alignment_score=int(aligns_with_value_delivered),
        understandability_score=int(customer_can_control),
        growth_alignment_score=int(customer_wants_it_to_grow),
        ai_era_alignment=int(aligns_with_ai_outcome),
    )


def detect_per_user_antipattern(growth_equals_value_growth: bool) -> bool:
    """
    Detect Campbell's per-user pricing antipattern.

    Returns True (antipattern present) when adding users does NOT proportionally
    increase value delivered.
    """
    return not growth_equals_value_growth


# ---------------------------------------------------------------------------
# Package Functions
# ---------------------------------------------------------------------------


def select_freemium_gate_type(
    requires_sales_assistance: bool,
    has_network_effects: bool,
    value_immediately_apparent: bool,
    value_metric_scales_with_usage: bool,
) -> FreemiumGateType:
    """
    Select freemium gate type for seed-to-Series B persona.

    Decision logic (in priority order):
      1. requires_sales_assistance → NO_FREE_TIER
      2. has_network_effects AND value_metric_scales_with_usage → FREEMIUM_USAGE_LIMITED
      3. has_network_effects → FREEMIUM_FEATURE_LIMITED
      4. value_immediately_apparent → TRIAL_GATE
      5. default → NO_FREE_TIER
    """
    if requires_sales_assistance:
        return FreemiumGateType.NO_FREE_TIER
    if has_network_effects and value_metric_scales_with_usage:
        return FreemiumGateType.FREEMIUM_USAGE_LIMITED
    if has_network_effects:
        return FreemiumGateType.FREEMIUM_FEATURE_LIMITED
    if value_immediately_apparent:
        return FreemiumGateType.TRIAL_GATE
    return FreemiumGateType.NO_FREE_TIER


def validate_tier_complexity(benefits_per_tier: dict[str, list]) -> list[str]:
    """
    Validate Ramanujam's packaging complexity threshold (max 9 benefits per tier).

    Returns list of tier names that violate the 9-benefit limit (empty = all valid).
    """
    return [tier for tier, benefits in benefits_per_tier.items() if len(benefits) > 9]


# ---------------------------------------------------------------------------
# Command line — what the price skill runs:
#   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/pricing_calculator.py <function> '<JSON object of arguments>'
# Prints the result as JSON. Exit 0 ok, 1 a ValueError (message on stderr), 2 bad use.
# ---------------------------------------------------------------------------

COMMANDS = (
    "compute_margin_floor",
    "compute_ai_multiplier",
    "compute_moat_multiplier",
    "compute_path_a",
    "compute_path_b",
    "compute_path_c_autonomous",
    "compute_path_c_fully_agentic",
)


def _plain(value):
    if dataclasses.is_dataclass(value):
        fields = {f.name: _plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
        return {"type": type(value).__name__, **fields}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    return value


def _refuse_constant(name: str) -> float:
    raise ValueError("%s is not a number the calculator accepts" % name)


def main(argv: list[str]) -> int:
    usage = ("usage: pricing_calculator.py <%s> '<JSON object of arguments>'\n"
             "       pricing_calculator.py defaults\n" % "|".join(COMMANDS))
    if argv[1:] == ["defaults"]:
        # The values of config/defaults.json: a skill run in the default mode cannot read that file (STORY-321).
        path = Path(__file__).resolve().parent.parent / "config" / "defaults.json"
        print(json.dumps(json.loads(path.read_text(encoding="utf-8"))["formulas"]))
        return 0
    if len(argv) != 3 or argv[1] not in COMMANDS:
        sys.stderr.write(usage)
        return 2
    try:
        kwargs = json.loads(argv[2], parse_constant=_refuse_constant)
    except ValueError as exc:
        sys.stderr.write("arguments are not JSON: %s\n" % exc)
        return 2
    if not isinstance(kwargs, dict):
        sys.stderr.write("arguments must be a JSON object\n")
        return 2
    try:
        result = globals()[argv[1]](**kwargs)
    except TypeError as exc:
        sys.stderr.write("%s\n" % exc)
        return 2
    except ValueError as exc:
        sys.stderr.write("%s\n" % exc)
        return 1
    try:
        text = json.dumps(_plain(result), allow_nan=False)
    except ValueError as exc:
        sys.stderr.write("result is not finite: %s\n" % exc)
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
