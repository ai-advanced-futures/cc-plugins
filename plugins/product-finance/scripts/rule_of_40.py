# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Rule of 40 Calculator for SaaS Financial Health Analysis.

This module provides Rule of 40 calculations:
- Classic Rule of 40 (Revenue Growth % + EBITDA Margin %)
- Weighted Rule of 40 (1.33 × Growth + 0.67 × EBITDA Margin), a plugin convention, not graded
- A target of 40, 50 or 60, graded on each margin given
- The ladder of the score against each bar, and reference lines

Sources: the verified source ids FELD, VISTA, ICONIQ, BVP-AI, BVP-X and MERITECH. The
constants table below holds each source's title and date (SOURCES) and every quote.

The target rule: each margin given is scored as growth + margin against the target
(40 by default, or 50 or 60 as chosen). A score equal to the target meets it. A product
with 12 or fewer months of revenue is not graded.

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT
"""

import json
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from scripts.input_check import checked_input, limits, read_json_input  # noqa: E402
from scripts.utils.enums import GrowthStage, MetricHealth  # noqa: E402
from scripts.utils.exact import Number, as_written, shown  # noqa: E402
from scripts.utils.magic_number import calculate_magic_number  # noqa: E402


@dataclass
class RuleOf40Input:
    """Input data for Rule of 40 calculation.

    Attributes:
        revenue_growth_rate: Revenue growth rate as a percentage (can be negative)
        ebitda_margin: EBITDA margin as a percentage (can be negative)
        company_stage: Growth stage, used only for health_status (optional)
        previous_period_growth: Previous period's growth rate for trend analysis (optional)
        previous_period_margin: Previous period's EBITDA margin for trend analysis (optional)
        arr: Annual Recurring Revenue for context (optional)
        quarterly_net_new_arr: Net new ARR added in most recent quarter, for Magic Number (optional)
        prior_quarter_sm_spend: S&M spend in prior quarter, for Magic Number (optional)
        target: Rule of 40 target to grade against: 40, 50 or 60 (optional)
        fcf_margin: Free cash flow margin as a percentage (optional)
        months_of_revenue: Months the product has earned revenue, 1 to 1200 (optional)
        nrr: Net revenue retention as a percentage (optional)
        gross_margin: Gross margin as a percentage (optional)
    """

    TOGETHER: ClassVar[Tuple[Tuple[str, str], ...]] = (
        ("previous_period_growth", "previous_period_margin"),
        ("quarterly_net_new_arr", "prior_quarter_sm_spend"),
    )

    revenue_growth_rate: float = limits(ge=-100, le=1000)
    ebitda_margin: float = limits(ge=-500, le=100)
    company_stage: Optional[GrowthStage] = None
    previous_period_growth: Optional[float] = None
    previous_period_margin: Optional[float] = None
    arr: Optional[float] = limits(gt=0, le=100_000_000_000, default=None)
    quarterly_net_new_arr: Optional[float] = None
    prior_quarter_sm_spend: Optional[float] = limits(ge=0, default=None)
    target: Optional[int] = limits(one_of=(40, 50, 60), default=None)
    fcf_margin: Optional[float] = limits(ge=-500, le=100, default=None)
    months_of_revenue: Optional[int] = limits(gt=0, le=1200, default=None)
    nrr: Optional[float] = limits(ge=0, le=1000, default=None)
    gross_margin: Optional[float] = limits(ge=-500, le=100, default=None)


# The classes input_check reads, in the order fields.json recorded them.
INPUT_CLASSES = (RuleOf40Input,)

# The constants table (spec 0.15.0, "Verified sources"). Every quoted source string
# lives here, and nowhere else in the plugin's code: the report and `--help` are built
# from it, and test_rule_of_40_docs.py holds each quote in the docs to a QUOTES fragment
# and each ladder Source cell to LADDER_SOURCES. Each quoted fragment is a substring of
# its verified passage, character for character (test_rule_of_40_targets.py,
# TestSources).
# Source id -> (title, date as the source prints it; None when the page shows no date).
SOURCES: Dict[str, Tuple[str, Optional[str]]] = {
    "FELD": ("The Rule of 40% For a Healthy SaaS Company", "3 Feb 2015"),
    "VISTA": ("Rethinking Software Benchmarks in an AI-Driven Market", "8 Jan 2026"),
    "ICONIQ": ("The ICONIQ Enterprise Five", None),
    "BVP-AI": ("The State of AI 2025", "13 Aug 2025"),
    "BVP-X": ("The Rule of X", "2 Jan 2024"),
    "MERITECH": ("Software Pulse", "14-August-2026"),
}
FELD_QUOTE = "The 40% rule is that your growth rate + your profit should add up to 40%."
VISTA_QUOTE = "an emerging aspiration, not a universal baseline"
VISTA_SHORT = "an emerging aspiration"
ICONIQ_WEIGHT = (
    "we typically only begin to place real weight against Rule of 40 for companies "
    "with at least $25M ARR"
)
ICONIQ_REASON = (
    "exceptional year-over-year growth inflates Rule of 40 performance for early-stage companies"
)
ICONIQ_CITATION = f"ICONIQ, {SOURCES['ICONIQ'][0]} (2025 KPIs)"

# (source id, quoted fragment), one row per quote.
QUOTES: Tuple[Tuple[str, str], ...] = (
    ("FELD", FELD_QUOTE),
    ("VISTA", VISTA_QUOTE),
    ("VISTA", VISTA_SHORT),
    ("ICONIQ", ICONIQ_WEIGHT),
    ("ICONIQ", ICONIQ_REASON),
)

# The Source cell of each ladder row (spec section 4).
LADDER_SOURCES: Dict[int, str] = {
    40: f'Feld (2015): "{FELD_QUOTE}"',
    50: "No published benchmark found. A bar you set.",
    60: f'Vista Equity Partners ({SOURCES["VISTA"][1]}): "{VISTA_QUOTE}".',
}
ICONIQ_CAUTION = (
    f'Caution (ICONIQ): "{ICONIQ_WEIGHT}", because "{ICONIQ_REASON}" ({ICONIQ_CITATION}).'
)
# A paraphrase of Bessemer's figures, not a quote.
GROSS_MARGIN_SOURCE = (
    f"Bessemer, {SOURCES['BVP-AI'][0]} ({SOURCES['BVP-AI'][1]}): AI Supernovas average 25% "
    "gross margins; Shooting Stars about 60%."
)
SPLIT_LINE = (
    "The EBITDA and FCF lines disagree at {target}. The two margins differ by capital "
    "spending, stock-based pay, working capital, interest and tax. Use the margin your "
    "board or investors use."
)
WEIGHTED_LABEL = "plugin convention, not graded"

TARGETS = (40, 50, 60)
DEFAULT_TARGET = 40


@dataclass
class TargetLine:
    """One margin against the target (spec section 2).

    Attributes:
        basis: "ebitda" or "fcf"
        margin: the margin, as a percentage
        score: growth + margin
        status: "met", "short" or "not_graded"
        short_by: target - score when the status is "short", else None
    """

    basis: str
    margin: Fraction
    score: Fraction
    status: str
    short_by: Optional[Fraction]


def target_status_for(
    growth: Fraction,
    ebitda_margin: Fraction,
    fcf_margin: Optional[Fraction],
    target: int,
    months_of_revenue: Optional[int],
) -> Tuple[str, List[TargetLine]]:
    """The target status and one line per given margin, EBITDA first (spec section 2).

    A line is met when its score is at least the target. The product is not graded
    when `months_of_revenue` is given and is 12 or less. Otherwise the status is
    "met" when every line is met, "short" when every line is short, else "split".
    """
    growth = as_written(growth)
    margins = [("ebitda", as_written(ebitda_margin))]
    if fcf_margin is not None:
        margins.append(("fcf", as_written(fcf_margin)))
    graded = months_of_revenue is None or months_of_revenue > 12
    lines = []
    for basis, margin in margins:
        score = growth + margin
        if not graded:
            status, short_by = "not_graded", None
        elif score >= target:
            status, short_by = "met", None
        else:
            status, short_by = "short", target - score
        lines.append(TargetLine(basis, margin, score, status, short_by))
    if not graded:
        return "not_graded", lines
    statuses = {line.status for line in lines}
    if statuses == {"met"}:
        return "met", lines
    if statuses == {"short"}:
        return "short", lines
    return "split", lines


def _json2(x: Fraction) -> float:
    """A new JSON figure: `x` at 2 places, with a negative zero written 0.0 (spec section 5)."""
    value = float(shown(x, 2))
    return 0.0 if value == 0 else value


def _ladder_cell(x: Fraction) -> str:
    """A ladder cell: score minus bar at 1 place, with a sign (spec section 4).

    An exact zero prints 0.0 (`shown` gives it no sign). A value that is not zero
    but prints as zero keeps its sign: -0.0 below the bar, +0.0 above it.
    """
    text = str(shown(x, 1))
    return "+" + text if x > 0 else text


@dataclass
class LadderRow:
    """One bar of the ladder (spec section 4).

    Attributes:
        bar: 40, 50 or 60
        target: True on the target's row
        ebitda: the EBITDA score minus the bar (never the score)
        fcf: the FCF score minus the bar, or None when fcf_margin is not given
        source: the row's Source cell
    """

    bar: int
    target: bool
    ebitda: Fraction
    fcf: Optional[Fraction]
    source: str


def _ladder(lines: List[TargetLine], target: int) -> List[LadderRow]:
    """Each line's score minus each bar, 40, 50 and 60. Arithmetic, not a verdict, so it
    is the same whether or not the product is graded."""
    scores = {line.basis: line.score for line in lines}
    fcf = scores.get("fcf")
    return [LadderRow(bar, bar == target, scores["ebitda"] - bar,
                      None if fcf is None else fcf - bar, LADDER_SOURCES[bar])
            for bar in TARGETS]


def _reference_lines(
    nrr: Optional[Fraction], gross_margin: Optional[Fraction], months_of_revenue: Optional[int]
) -> List[str]:
    """The Reference Lines as a list of "<label>: <rest>" (spec section 4).

    The list is joined by newlines in the JSON.

    Under the age gate (12 months or less) the NRR line says it is not available,
    whether `nrr` is given or not. No reference line enters the score or the status.
    """
    lines = []
    if months_of_revenue is not None and months_of_revenue <= 12:
        lines.append("NRR: not available before the thirteenth month of revenue.")
    elif nrr is not None:
        lines.append(f"NRR: {shown(nrr, 1):.1f}%")
    if gross_margin is not None:
        lines.append(f"Gross Margin: {shown(gross_margin, 1):.1f}%. {GROSS_MARGIN_SOURCE}")
    return lines


@dataclass
class RuleOf40Result:
    """Result of Rule of 40 calculation.

    Attributes:
        rule_of_40_score: Classic Rule of 40 score (Growth % + EBITDA Margin %)
        weighted_rule_of_40: Weighted Rule of 40 (1.33 × Growth + 0.67 × EBITDA)
        revenue_growth_rate: Revenue growth rate percentage
        ebitda_margin: EBITDA margin percentage
        fcf_margin: Free cash flow margin percentage, or None when not given. The
            markdown prints it; the JSON does not (spec section 5)
        health_status: Overall health assessment
        target: The target graded against: 40, 50 or 60
        target_source: "default" when no target was given, else "chosen"
        target_status: "met", "short", "split" or "not_graded"
        target_lines: One line per given margin, EBITDA first
        target_notes: The Target section's split, age and size lines, without "- ",
            joined by newlines, or "" (spec section 5)
        ladder: One row per bar, 40, 50 and 60: each score minus the bar
        reference_lines: The Reference Lines, "<label>: <rest>", or [] (spec section 4);
            joined by newlines in the JSON
        benchmark_notes: Benchmark comparison and context
        balance_analysis: Analysis of growth vs. profitability balance
        recommendations: List of actionable recommendations
        trend_analysis: Optional trend analysis if previous period data provided
        magic_number: Optional Magic Number analysis dict if quarterly inputs provided
    """

    rule_of_40_score: Number
    weighted_rule_of_40: Number
    revenue_growth_rate: Number
    ebitda_margin: Number
    fcf_margin: Optional[Number]
    health_status: MetricHealth
    target: int
    target_source: str
    target_status: str
    target_lines: List[TargetLine]
    target_notes: str
    ladder: List[LadderRow]
    reference_lines: List[str]
    benchmark_notes: str
    balance_analysis: str
    recommendations: list[str]
    trend_analysis: Optional[str] = None
    magic_number: Optional[dict] = None


def calculate_rule_of_40(data: RuleOf40Input) -> RuleOf40Result:
    """Calculate Rule of 40 and weighted Rule of 40.

    Classic Rule of 40 Formula:
        Rule of 40 = Revenue Growth Rate (%) + EBITDA Margin (%)

    Weighted Rule of 40 Formula:
        Weighted Rule of 40 = 1.33 × Revenue Growth Rate (%) + 0.67 × EBITDA Margin (%)

    In valuation studies, growth outweighs FCF margin: 2–3 times for late-stage cloud
    companies (Bessemer, The Rule of X, 2024) and 3.8 times on ARR multiples (Meritech
    Software Pulse, 14-August-2026). This score uses EBITDA margin; the weights are a
    plugin convention.

    The target rule: each margin given is scored as growth + margin against the target
    (40 by default, or 50 or 60 as chosen), and a score equal to the target meets it. A
    product with 12 or fewer months of revenue is not graded (`target_status_for`).

    Args:
        data: Input data for Rule of 40 calculation

    Returns:
        RuleOf40Result with calculated scores and comprehensive analysis

    Example:
        >>> from scripts.input_check import build
        >>> input_data = build(
        ...     RuleOf40Input,
        ...     revenue_growth_rate=50.0,
        ...     ebitda_margin=-5.0,
        ...     company_stage=GrowthStage.GROWTH
        ... )
        >>> result = calculate_rule_of_40(input_data)
        >>> print(f"Rule of 40: {shown(result.rule_of_40_score, 1):.1f}%")
        Rule of 40: 45.0%
    """
    # Every input is read as written, so 32.3 + -12.3 is 20, not 19.999...
    growth = as_written(data.revenue_growth_rate)
    margin = as_written(data.ebitda_margin)
    arr = None if data.arr is None else as_written(data.arr)

    # Calculate classic Rule of 40
    rule_of_40_score = growth + margin

    # Calculate weighted Rule of 40. In valuation studies, growth outweighs FCF margin:
    # 2–3 times for late-stage cloud companies (Bessemer, The Rule of X, 2024) and 3.8
    # times on ARR multiples (Meritech Software Pulse, 14-August-2026). This score uses
    # EBITDA margin; the weights are a plugin convention.
    weighted_rule_of_40 = (Fraction("1.33") * growth) + (Fraction("0.67") * margin)

    # Assess health status
    health_status = _assess_health(rule_of_40_score, data.company_stage)

    # Grade against the target, on each given margin (spec section 2)
    target = DEFAULT_TARGET if data.target is None else data.target
    fcf_margin = None if data.fcf_margin is None else as_written(data.fcf_margin)
    target_status, target_lines = target_status_for(
        growth, margin, fcf_margin, target, data.months_of_revenue)
    target_notes = _target_notes(target, target_status, data.months_of_revenue, arr)
    ladder = _ladder(target_lines, target)
    reference_lines = _reference_lines(
        None if data.nrr is None else as_written(data.nrr),
        None if data.gross_margin is None else as_written(data.gross_margin),
        data.months_of_revenue)

    # Generate benchmark notes
    benchmark_notes = _generate_benchmark_notes(rule_of_40_score, weighted_rule_of_40, arr)

    # State growth and profitability side by side
    balance_analysis = _analyze_balance(growth, margin)

    # Generate recommendations
    recommendations = _generate_recommendations(target_status, target, target_lines)

    # Generate trend analysis if previous period data provided
    trend_analysis = None
    if data.previous_period_growth is not None and data.previous_period_margin is not None:
        trend_analysis = _analyze_trends(
            growth,
            margin,
            as_written(data.previous_period_growth),
            as_written(data.previous_period_margin),
            rule_of_40_score,
        )

    # Calculate Magic Number if quarterly inputs were provided (delegates to the
    # canonical scripts.utils.magic_number helper; adapts MagicNumberOutcome → dict).
    magic_number_result = None
    if data.quarterly_net_new_arr is not None and data.prior_quarter_sm_spend is not None:
        _mn = calculate_magic_number(
            quarterly_net_new_arr=data.quarterly_net_new_arr,
            prior_quarter_sm_spend=data.prior_quarter_sm_spend,
        )
        magic_number_result = {
            "magic_number": _mn.magic_number,
            "health": _mn.health.value,
            "interpretation": _mn.interpretation,
        }

    return RuleOf40Result(
        rule_of_40_score=rule_of_40_score,
        weighted_rule_of_40=weighted_rule_of_40,
        revenue_growth_rate=growth,
        ebitda_margin=margin,
        fcf_margin=fcf_margin,
        health_status=health_status,
        target=target,
        target_source="default" if data.target is None else "chosen",
        target_status=target_status,
        target_lines=target_lines,
        target_notes=target_notes,
        ladder=ladder,
        reference_lines=reference_lines,
        benchmark_notes=benchmark_notes,
        balance_analysis=balance_analysis,
        recommendations=recommendations,
        trend_analysis=trend_analysis,
        magic_number=magic_number_result,
    )


def _target_notes(
    target: int, status: str, months_of_revenue: Optional[int], arr: Optional[Fraction]
) -> str:
    """The Target section's lines 4 to 6 (spec section 4), without "- ", joined by newlines."""
    notes = []
    if status == "split":
        # str.replace, not .format: the source guard refuses every .format( call
        notes.append(SPLIT_LINE.replace("{target}", str(target)))
    if months_of_revenue is None:
        notes.append("Age not checked: months_of_revenue was not given.")
    elif months_of_revenue <= 12:
        notes.append(
            f"Not graded: months of revenue: {months_of_revenue}. "
            "Growth is not a year-on-year rate before the thirteenth month."
        )
    if arr is None:
        notes.append("Size not checked: arr was not given.")
    elif arr < 25_000_000:
        notes.append(ICONIQ_CAUTION)
    return "\n".join(notes)


def _assess_health(score: Number, stage: Optional[GrowthStage]) -> MetricHealth:
    """Assess health status based on Rule of 40 score and company stage.

    These stage bands have no published source. They are kept only so that
    health_status does not change.

    Args:
        score: Rule of 40 score
        stage: Company growth stage (optional)

    Returns:
        MetricHealth enum value
    """
    # Stage-adjusted thresholds
    if stage == GrowthStage.EARLY:
        # Early stage: more lenient (focus on growth)
        if score >= 30:
            return MetricHealth.EXCELLENT
        elif score >= 20:
            return MetricHealth.GOOD
        elif score >= 10:
            return MetricHealth.WARNING
        else:
            return MetricHealth.CRITICAL
    elif stage == GrowthStage.GROWTH:
        # Growth stage: standard thresholds
        if score >= 40:
            return MetricHealth.EXCELLENT
        elif score >= 30:
            return MetricHealth.GOOD
        elif score >= 20:
            return MetricHealth.WARNING
        else:
            return MetricHealth.CRITICAL
    elif stage in (GrowthStage.SCALE, GrowthStage.MATURE):
        # Scale/Mature: higher expectations
        if score >= 50:
            return MetricHealth.EXCELLENT
        elif score >= 40:
            return MetricHealth.GOOD
        elif score >= 30:
            return MetricHealth.WARNING
        else:
            return MetricHealth.CRITICAL
    else:
        # Default thresholds (stage unknown)
        if score >= 40:
            return MetricHealth.EXCELLENT
        elif score >= 30:
            return MetricHealth.GOOD
        elif score >= 20:
            return MetricHealth.WARNING
        else:
            return MetricHealth.CRITICAL


def _generate_benchmark_notes(
    score: Fraction, weighted_score: Fraction, arr: Optional[Fraction]
) -> str:
    """The Benchmark Comparison lines (spec section 4): the person's own figures only.

    Args:
        score: Rule of 40 score
        weighted_score: Weighted Rule of 40 score
        arr: Annual Recurring Revenue (optional)

    Returns:
        The classic and weighted scores, and the ARR when given, one per line
    """
    notes = [
        f"Classic Rule of 40: {shown(score, 1):.1f}%",
        f"Weighted Rule of 40: {shown(weighted_score, 1):.1f}% ({WEIGHTED_LABEL})",
    ]
    if arr is not None:
        notes.append(f"ARR: ${shown(arr, 0):,.0f}")
    return "\n".join(notes)


def _analyze_balance(growth: Fraction, margin: Fraction) -> str:
    """The Growth vs. Profitability Balance lines (spec section 4): the two figures.

    Args:
        growth: Revenue growth rate
        margin: EBITDA margin

    Returns:
        The growth rate and the EBITDA margin, one per line
    """
    return "\n".join([
        f"Growth Rate: {shown(growth, 1):.1f}%",
        f"EBITDA Margin: {shown(margin, 1):.1f}%",
    ])


def _gap_text(gap: Fraction) -> str:
    """The gap to the target score, for a recommendation.

    It is `gap` at 1 place, rounded half away from zero, with a trailing `.0`
    dropped. A gap above 0 that prints as 0 reads "less than 0.1".
    """
    text = str(shown(gap, 1))
    if text.endswith(".0"):
        text = text[:-2]
    if gap > 0 and text == "0":
        return "less than 0.1"
    return text


def _generate_recommendations(status: str, target: int, lines: List[TargetLine]) -> List[str]:
    """The Recommendations of spec section 4. The plugin names no lever.

    Short or split: one item per short line, EBITDA first, with its gap. Met: one item.
    Not graded: one item, whatever the line scores say.
    """
    if status == "not_graded":
        return ["No verdict before the thirteenth month of revenue. Run it again then."]
    if status == "met":
        return [f"Meets the target of {target} on every margin given."]
    recommendations = []
    for line in lines:
        if line.status != "short":
            continue
        name, gap = line.basis.upper(), _gap_text(line.short_by)
        recommendations.append(
            f"The {name} basis is short of {target} by {gap}: closes with {gap} points of "
            f"growth or {gap} points of {name} margin."
        )
    return recommendations


def _analyze_trends(
    current_growth: Number,
    current_margin: Number,
    previous_growth: Number,
    previous_margin: Number,
    current_score: Number,
) -> str:
    """Analyze trends from previous period to current period.

    Args:
        current_growth: Current period growth rate
        current_margin: Current period EBITDA margin
        previous_growth: Previous period growth rate
        previous_margin: Previous period EBITDA margin
        current_score: Current Rule of 40 score

    Returns:
        Trend analysis string
    """
    previous_score = previous_growth + previous_margin
    score_change = current_score - previous_score
    growth_change = current_growth - previous_growth
    margin_change = current_margin - previous_margin

    analysis = []

    # Overall trend
    analysis.append("TREND ANALYSIS (vs. Previous Period)")
    analysis.append("=" * 50)

    if score_change > 0:
        analysis.append(f"Rule of 40 improved by {shown(score_change, 1):.1f} points ({shown(previous_score, 1):.1f}% → {shown(current_score, 1):.1f}%) - Positive trend!")  # noqa: E501
    elif score_change < 0:
        analysis.append(f"Rule of 40 declined by {shown(abs(score_change), 1):.1f} points ({shown(previous_score, 1):.1f}% → {shown(current_score, 1):.1f}%) - Negative trend.")  # noqa: E501
    else:
        analysis.append(f"Rule of 40 unchanged at {shown(current_score, 1):.1f}%.")

    # Growth trend
    if abs(growth_change) > Fraction("0.1"):
        direction = "increased" if growth_change > 0 else "decreased"
        analysis.append(f"Growth {direction} by {shown(abs(growth_change), 1):.1f} points ({shown(previous_growth, 1):.1f}% → {shown(current_growth, 1):.1f}%)")  # noqa: E501

    # Margin trend
    if abs(margin_change) > Fraction("0.1"):
        direction = "improved" if margin_change > 0 else "declined"
        analysis.append(f"EBITDA margin {direction} by {shown(abs(margin_change), 1):.1f} points ({shown(previous_margin, 1):.1f}% → {shown(current_margin, 1):.1f}%)")  # noqa: E501

    return "\n".join(analysis)


def format_result_as_json(result: RuleOf40Result) -> str:
    """Format Rule of 40 result as JSON.

    Args:
        result: RuleOf40Result to format

    Returns:
        JSON string representation
    """
    output = {
        "rule_of_40_score": float(shown(result.rule_of_40_score, 2)),
        "weighted_rule_of_40": float(shown(result.weighted_rule_of_40, 2)),
        "revenue_growth_rate": float(shown(result.revenue_growth_rate, 2)),
        "ebitda_margin": float(shown(result.ebitda_margin, 2)),
        "health_status": result.health_status.value,
        "target": result.target,
        "target_source": result.target_source,
        "target_status": result.target_status,
        "target_lines": [
            {
                "basis": line.basis,
                "margin": _json2(line.margin),
                "score": _json2(line.score),
                "status": line.status,
                "short_by": None if line.short_by is None else _json2(line.short_by),
            }
            for line in result.target_lines
        ],
        "target_notes": result.target_notes,
        "ladder": [
            {
                "bar": row.bar,
                "target": row.target,
                "ebitda": _json2(row.ebitda),
                "fcf": None if row.fcf is None else _json2(row.fcf),
                "source": row.source,
            }
            for row in result.ladder
        ],
        "reference_lines": "\n".join(result.reference_lines),
        "benchmark_notes": result.benchmark_notes,
        "balance_analysis": result.balance_analysis,
        "recommendations": result.recommendations,
    }

    if result.trend_analysis:
        output["trend_analysis"] = result.trend_analysis

    if result.magic_number:
        mn = dict(result.magic_number)
        if mn["magic_number"] is not None:
            mn["magic_number"] = float(shown(mn["magic_number"], 2))
        output["magic_number"] = mn

    return json.dumps(output, indent=2)


def format_result_as_markdown(result: RuleOf40Result) -> str:
    """Format Rule of 40 result as Markdown.

    Args:
        result: RuleOf40Result to format

    Returns:
        Markdown string representation
    """
    lines = []

    lines.append("# Rule of 40 Analysis")
    lines.append("")
    lines.append("## Key Metrics")
    lines.append("")
    lines.append(f"- **Rule of 40 Score**: {shown(result.rule_of_40_score, 1):.1f}%")
    lines.append(f"- **Weighted Rule of 40**: {shown(result.weighted_rule_of_40, 1):.1f}% "
                 f"({WEIGHTED_LABEL})")
    lines.append(f"- **Revenue Growth Rate**: {shown(result.revenue_growth_rate, 1):.1f}%")
    lines.append(f"- **EBITDA Margin**: {shown(result.ebitda_margin, 1):.1f}%")
    if result.fcf_margin is not None:
        lines.append(f"- **FCF Margin**: {shown(result.fcf_margin, 1):.1f}%")
    lines.append("")

    lines.append("## Target")
    lines.append("")
    source = "default" if result.target_source == "default" else "your choice"
    lines.append(f"- **Target**: {result.target} ({source})")
    for line in result.target_lines:
        if line.status == "met":
            verdict = "met"
        elif line.status == "short":
            verdict = f"short by {_gap_text(line.short_by)}"
        else:
            verdict = "not graded"
        lines.append(f"- **{line.basis.upper()} basis**: {shown(line.score, 1):.1f} "
                     f"against {result.target}: {verdict}")
    lines.append(f"- **Status**: {result.target_status.replace('_', ' ').upper()}")
    if result.target_notes:
        for note in result.target_notes.split("\n"):
            lines.append(f"- {note}")
    lines.append("")

    # The ladder (spec section 4): an FCF column only when fcf_margin is given
    with_fcf = result.fcf_margin is not None
    lines.append("## Ladder")
    lines.append("")
    if with_fcf:
        lines.append("| Bar | EBITDA basis | FCF basis | Source |")
        lines.append("|---|---|---|---|")
    else:
        lines.append("| Bar | EBITDA basis | Source |")
        lines.append("|---|---|---|")
    for row in result.ladder:
        cells = [f"{row.bar} (target)" if row.target else str(row.bar),
                 _ladder_cell(row.ebitda)]
        if with_fcf:
            cells.append(_ladder_cell(row.fcf))
        cells.append(row.source)
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")

    if result.reference_lines:
        lines.append("## Reference Lines")
        lines.append("")
        for line in result.reference_lines:
            label, rest = line.split(": ", 1)
            lines.append(f"- **{label}**: {rest}")
        lines.append("")

    lines.append("## Benchmark Comparison")
    lines.append("")
    for line in result.benchmark_notes.split("\n"):
        lines.append(line)
    lines.append("")

    lines.append("## Growth vs. Profitability Balance")
    lines.append("")
    for line in result.balance_analysis.split("\n"):
        lines.append(line)
    lines.append("")

    if result.trend_analysis:
        lines.append("## Trend Analysis")
        lines.append("")
        for line in result.trend_analysis.split("\n"):
            lines.append(line)
        lines.append("")

    if result.magic_number is not None:
        lines.append("## Magic Number (Sales Efficiency)")
        lines.append("")
        mn = result.magic_number
        if mn.get("magic_number") is not None:
            lines.append(f"- **Magic Number**: {shown(mn['magic_number'], 2):.2f}")
        else:
            lines.append("- **Magic Number**: N/A")
        lines.append(f"- **Health**: {mn['health'].upper()}")
        lines.append(f"- **Interpretation**: {mn['interpretation']}")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    for i, rec in enumerate(result.recommendations, 1):
        lines.append(f"{i}. {rec}")
    lines.append("")

    lines.append("---")
    lines.append("*Analysis based on Brad Feld's Rule of 40 framework*")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Command-line interface for Rule of 40 calculator.

    Reads JSON input from `--input <file>`, else from stdin, else asks
    for each value with interactive prompts. Prints the report.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Rule of 40 Calculator for SaaS Financial Health",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Interactive mode
  python rule_of_40.py

  # JSON input from stdin
  echo '{{"revenue_growth_rate": 50, "ebitda_margin": -5}}' | python rule_of_40.py

  # JSON file input
  python rule_of_40.py < input.json
  python rule_of_40.py --input input.json

  # Output formats
  python rule_of_40.py --format json
  python rule_of_40.py --format markdown

Inputs beyond growth and EBITDA margin (all optional; percentages as 12.5, not 0.125):
  target             40, 50 or 60 (default 40). 40 is Feld's 2015 rule; 50 has no
                     published benchmark; Vista (2026) calls 60 "{VISTA_SHORT}".
  fcf_margin         Free cash flow margin, %: (operating cash flow - capital spending)
                     / revenue x 100. Stock-based pay is not cash, so it is not subtracted.
  months_of_revenue  Months since first revenue. 12 or less: no verdict.
  nrr, gross_margin  Percentages, printed as reference lines, never scored.

ebitda_margin is EBITDA / revenue x 100. Plain EBITDA counts stock-based pay as a
cost; adjusted EBITDA adds it back.
        """,
    )

    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    parser.add_argument(
        "--input",
        type=Path,
        help="Read the JSON input from this file instead of stdin",
    )

    args = parser.parse_args()

    # Check if input is from a file or stdin
    if args.input is not None or not sys.stdin.isatty():
        # Read JSON from the file, else from stdin
        data = checked_input(RuleOf40Input, read_json_input(args.input))
    else:
        # Interactive mode
        print("Rule of 40 Calculator")
        print("=" * 50)
        print()

        try:
            answers: Dict[str, Any] = {
                "revenue_growth_rate": float(input("Revenue growth rate (%): ")),
                "ebitda_margin": float(input("EBITDA margin (%): ")),
            }

            stage_input = input(
                "Company stage (early/growth/scale/mature, or press Enter to skip): "
            ).strip().lower()
            if stage_input:
                answers["company_stage"] = stage_input

            arr_input = input("Annual Recurring Revenue ($ or press Enter to skip): ").strip()
            if arr_input:
                answers["arr"] = float(arr_input)

            target_input = input(
                "Target Rule of 40 score (40, 50 or 60, or press Enter for 40): "
            ).strip()
            if target_input:
                answers["target"] = float(target_input)
            fcf_input = input("FCF margin (% or press Enter to skip): ").strip()
            if fcf_input:
                answers["fcf_margin"] = float(fcf_input)
            months_input = input("Months of revenue (or press Enter to skip): ").strip()
            if months_input:
                answers["months_of_revenue"] = float(months_input)
            nrr_input = input("NRR (% or press Enter to skip): ").strip()
            if nrr_input:
                answers["nrr"] = float(nrr_input)
            gross_margin_input = input("Gross margin (% or press Enter to skip): ").strip()
            if gross_margin_input:
                answers["gross_margin"] = float(gross_margin_input)

            # Optional trend data
            print()
            print("Optional: Provide previous period data for trend analysis")
            prev_growth_input = input(
                "Previous period revenue growth rate (% or press Enter to skip): "
            ).strip()
            prev_margin_input = input(
                "Previous period EBITDA margin (% or press Enter to skip): "
            ).strip()
            if prev_growth_input:
                answers["previous_period_growth"] = float(prev_growth_input)
            if prev_margin_input:
                answers["previous_period_margin"] = float(prev_margin_input)

            # Optional Magic Number data: the spend is asked only after a net new ARR answer
            print()
            print("Optional: Magic Number inputs")
            net_new_arr_input = input(
                "Quarterly net new ARR, most recent quarter ($ or press Enter to skip): "
            ).strip()
            if net_new_arr_input:
                answers["quarterly_net_new_arr"] = float(net_new_arr_input)
                spend_input = input("Sales & Marketing spend in the prior quarter ($): ").strip()
                if spend_input:
                    answers["prior_quarter_sm_spend"] = float(spend_input)
        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)

        data = checked_input(RuleOf40Input, answers)

    # Calculate Rule of 40
    try:
        result = calculate_rule_of_40(data)
    except Exception as e:
        print(f"Error calculating Rule of 40: {e}", file=sys.stderr)
        sys.exit(1)

    # Output results
    print()
    if args.format == "json":
        print(format_result_as_json(result))
    else:
        print(format_result_as_markdown(result))


if __name__ == "__main__":
    main()
