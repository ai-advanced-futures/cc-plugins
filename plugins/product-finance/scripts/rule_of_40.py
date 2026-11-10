# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Rule of 40 Calculator for SaaS Financial Health Analysis.

This module provides comprehensive Rule of 40 calculations including:
- Classic Rule of 40 (Revenue Growth % + EBITDA Margin % ≥ 40%)
- Weighted Rule of 40 (1.33 × Growth + 0.67 × EBITDA Margin)
- Growth vs. profitability analysis
- Benchmark comparison and recommendations

Based on Brad Feld's Rule of 40 framework and industry best practices from:
- Brad Feld (Foundry Group) - Rule of 40 framework
- Ben Murray (The SaaS CFO) - SaaS financial benchmarks
- McKinsey & Company - Software company performance analysis
- Tomasz Tunguz (Theory Ventures) - Growth and profitability balance

The Rule of 40 is a key metric for SaaS company health:
- Score ≥ 40: Excellent (healthy balance of growth and profitability)
- Score 30-40: Good (solid performance)
- Score 20-30: Warning (needs attention)
- Score < 20: Critical (significant issues)

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Dict, Optional, Tuple

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from scripts.input_check import checked_input, limits, read_json_input  # noqa: E402
from scripts.utils.enums import GrowthStage, MetricHealth  # noqa: E402
from scripts.utils.magic_number import calculate_magic_number  # noqa: E402


@dataclass
class RuleOf40Input:
    """Input data for Rule of 40 calculation.

    Attributes:
        revenue_growth_rate: Revenue growth rate as a percentage (can be negative)
        ebitda_margin: EBITDA margin as a percentage (can be negative)
        company_stage: Growth stage for contextualized analysis (optional)
        previous_period_growth: Previous period's growth rate for trend analysis (optional)
        previous_period_margin: Previous period's EBITDA margin for trend analysis (optional)
        arr: Annual Recurring Revenue for context (optional)
        quarterly_net_new_arr: Net new ARR added in most recent quarter, for Magic Number (optional)
        prior_quarter_sm_spend: S&M spend in prior quarter, for Magic Number (optional)
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


# The classes input_check reads, in the order fields.json recorded them.
INPUT_CLASSES = (RuleOf40Input,)


@dataclass
class RuleOf40Result:
    """Result of Rule of 40 calculation.

    Attributes:
        rule_of_40_score: Classic Rule of 40 score (Growth % + EBITDA Margin %)
        weighted_rule_of_40: Weighted Rule of 40 (1.33 × Growth + 0.67 × EBITDA)
        revenue_growth_rate: Revenue growth rate percentage
        ebitda_margin: EBITDA margin percentage
        health_status: Overall health assessment
        benchmark_notes: Benchmark comparison and context
        balance_analysis: Analysis of growth vs. profitability balance
        recommendations: List of actionable recommendations
        trend_analysis: Optional trend analysis if previous period data provided
        magic_number: Optional Magic Number analysis dict if quarterly inputs provided
    """

    rule_of_40_score: float
    weighted_rule_of_40: float
    revenue_growth_rate: float
    ebitda_margin: float
    health_status: MetricHealth
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

    The weighted formula reflects that growth is typically valued ~2x more than profitability
    in the public markets, especially for high-growth SaaS companies.

    Health Thresholds:
    - ≥ 40: Excellent (healthy balance, IPO-ready)
    - 30-40: Good (solid performance, improving toward excellence)
    - 20-30: Warning (needs improvement, below market expectations)
    - < 20: Critical (significant issues, requires urgent action)

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
        >>> print(f"Rule of 40: {result.rule_of_40_score:.1f}%")
        Rule of 40: 45.0%
    """
    # Calculate classic Rule of 40
    rule_of_40_score = data.revenue_growth_rate + data.ebitda_margin

    # Calculate weighted Rule of 40 (growth weighted 2x profitability)
    weighted_rule_of_40 = (1.33 * data.revenue_growth_rate) + (0.67 * data.ebitda_margin)

    # Assess health status
    health_status = _assess_health(rule_of_40_score, data.company_stage)

    # Generate benchmark notes
    benchmark_notes = _generate_benchmark_notes(
        rule_of_40_score, weighted_rule_of_40, data.company_stage, data.arr
    )

    # Analyze growth vs. profitability balance
    balance_analysis = _analyze_balance(data.revenue_growth_rate, data.ebitda_margin, data.company_stage)  # noqa: E501

    # Generate recommendations
    recommendations = _generate_recommendations(
        rule_of_40_score, data.revenue_growth_rate, data.ebitda_margin, data.company_stage
    )

    # Generate trend analysis if previous period data provided
    trend_analysis = None
    if data.previous_period_growth is not None and data.previous_period_margin is not None:
        trend_analysis = _analyze_trends(
            data.revenue_growth_rate,
            data.ebitda_margin,
            data.previous_period_growth,
            data.previous_period_margin,
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
        revenue_growth_rate=data.revenue_growth_rate,
        ebitda_margin=data.ebitda_margin,
        health_status=health_status,
        benchmark_notes=benchmark_notes,
        balance_analysis=balance_analysis,
        recommendations=recommendations,
        trend_analysis=trend_analysis,
        magic_number=magic_number_result,
    )


def _assess_health(score: float, stage: Optional[GrowthStage]) -> MetricHealth:
    """Assess health status based on Rule of 40 score and company stage.

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
    score: float,
    weighted_score: float,
    stage: Optional[GrowthStage],
    arr: Optional[float],
) -> str:
    """Generate benchmark comparison notes.

    Args:
        score: Rule of 40 score
        weighted_score: Weighted Rule of 40 score
        stage: Company growth stage
        arr: Annual Recurring Revenue (optional)

    Returns:
        Formatted benchmark notes string
    """
    notes = []

    # Overall benchmark
    notes.append(f"Classic Rule of 40: {score:.1f}%")
    notes.append(f"Weighted Rule of 40: {weighted_score:.1f}%")

    # Industry benchmarks
    if score >= 40:
        notes.append(
            "Exceeds the Rule of 40 threshold - indicates excellent balance of growth and profitability."  # noqa: E501
        )
        notes.append("Top quartile performance for public SaaS companies.")
    elif score >= 30:
        notes.append("Good performance, approaching Rule of 40 excellence.")
        notes.append("Second quartile performance - above median for public SaaS companies.")
    elif score >= 20:
        notes.append("Below expectations for healthy SaaS companies.")
        notes.append("Third quartile performance - improvement needed.")
    else:
        notes.append("Critical - significantly below Rule of 40 threshold.")
        notes.append("Bottom quartile performance - urgent action required.")

    # Stage-specific context
    if stage == GrowthStage.EARLY:
        notes.append(
            "Early stage: Prioritize growth and product-market fit. Profitability can come later."
        )
    elif stage == GrowthStage.GROWTH:
        notes.append("Growth stage: Balance rapid expansion with improving unit economics.")
    elif stage == GrowthStage.SCALE:
        notes.append(
            "Scale stage: Optimize for efficient growth - every dollar should drive measurable growth or profit improvement."  # noqa: E501
        )
    elif stage == GrowthStage.MATURE:
        notes.append("Mature stage: Emphasize profitability while maintaining sustainable growth.")

    # ARR-specific context
    if arr is not None:
        if arr < 1_000_000:
            notes.append(f"ARR: ${arr:,.0f} - Pre-$1M ARR, focus on finding product-market fit.")
        elif arr < 10_000_000:
            notes.append(
                f"ARR: ${arr:,.0f} - $1M-$10M ARR range, focus on scaling go-to-market efficiently."
            )
        elif arr < 100_000_000:
            notes.append(
                f"ARR: ${arr:,.0f} - $10M-$100M ARR range, optimize for efficient growth at scale."
            )
        else:
            notes.append(
                f"ARR: ${arr:,.0f} - $100M+ ARR, public market expectations for balanced performance."  # noqa: E501
            )

    return "\n".join(notes)


def _analyze_balance(
    growth: float, margin: float, stage: Optional[GrowthStage]
) -> str:
    """Analyze the balance between growth and profitability.

    Args:
        growth: Revenue growth rate
        margin: EBITDA margin
        stage: Company growth stage

    Returns:
        Analysis of growth vs. profitability balance
    """
    analysis = []

    # Determine balance type
    if growth > 40 and margin < 0:
        balance_type = "Hypergrowth with investment (growth-first strategy)"
    elif growth > 30 and margin < 10:
        balance_type = "Growth-focused with moderate burn"
    elif growth < 20 and margin > 20:
        balance_type = "Profitability-focused (mature/efficient growth)"
    elif abs(growth - margin) < 10:
        balance_type = "Balanced growth and profitability"
    elif growth > margin:
        balance_type = "Growth-prioritized"
    else:
        balance_type = "Profitability-prioritized"

    analysis.append(f"Balance Type: {balance_type}")
    analysis.append(f"Growth Rate: {growth:.1f}%")
    analysis.append(f"EBITDA Margin: {margin:.1f}%")

    # Stage appropriateness
    if stage == GrowthStage.EARLY:
        if growth > 50:
            analysis.append("Appropriate for early stage - strong growth focus.")
        else:
            analysis.append("Consider: Early stage companies should prioritize high growth.")
    elif stage == GrowthStage.GROWTH:
        if growth > 30 and margin > -20:
            analysis.append("Good balance for growth stage - scaling efficiently.")
        elif margin < -30:
            analysis.append("Warning: Burn rate may be unsustainable for growth stage.")
        elif growth < 30:
            analysis.append("Consider: Growth stage companies should aim for >30% growth.")
    elif stage == GrowthStage.SCALE:
        if 20 <= growth <= 50 and margin > 0:
            analysis.append("Excellent balance for scale stage - efficient growth with profitability.")  # noqa: E501
        elif margin < 0:
            analysis.append("Consider: Scale stage companies should aim for profitability.")
    elif stage == GrowthStage.MATURE:
        if margin > 20:
            analysis.append("Strong profitability appropriate for mature companies.")
        if growth < 10:
            analysis.append("Note: Low growth typical for mature businesses, but ensure it's sustainable.")  # noqa: E501

    # Growth vs. margin trade-off analysis
    if growth < 10 and margin < 10:
        analysis.append("CRITICAL: Neither growth nor profitability are strong - requires urgent review.")  # noqa: E501
    elif growth > 100 and margin < -50:
        analysis.append(
            "Warning: Hypergrowth with very high burn - ensure unit economics will improve at scale."  # noqa: E501
        )

    return "\n".join(analysis)


def _generate_recommendations(
    score: float, growth: float, margin: float, stage: Optional[GrowthStage]
) -> list[str]:
    """Generate actionable recommendations based on Rule of 40 analysis.

    Args:
        score: Rule of 40 score
        growth: Revenue growth rate
        margin: EBITDA margin
        stage: Company growth stage

    Returns:
        List of actionable recommendations
    """
    recommendations = []

    # Primary recommendations based on score
    if score >= 40:
        recommendations.append("Maintain excellent performance - you're in the top quartile of SaaS companies.")  # noqa: E501
        if growth > 50 and margin < 10:
            recommendations.append(
                "As growth naturally slows, begin gradually improving profitability to maintain Rule of 40 compliance."  # noqa: E501
            )
    elif score >= 30:
        recommendations.append(
            f"Improve score by {40 - score:.0f} points to reach Rule of 40 excellence (40+)."
        )
    else:
        recommendations.append(
            f"URGENT: Improve score by {40 - score:.0f} points to reach healthy levels. Consider both growth acceleration and cost optimization."  # noqa: E501
        )

    # Growth-specific recommendations
    if growth < 20:
        recommendations.append(
            "Low growth (<20%): Consider growth investments - increase sales/marketing, expand into new segments, or accelerate product innovation."  # noqa: E501
        )
        if stage in (GrowthStage.EARLY, GrowthStage.GROWTH):
            recommendations.append(
                "For your growth stage, aim for at least 50%+ growth. Evaluate product-market fit and go-to-market effectiveness."  # noqa: E501
            )
    elif growth > 100 and margin < -30:
        recommendations.append(
            "Hypergrowth with high burn: Validate unit economics improve at scale. Ensure CAC payback < 12 months."  # noqa: E501
        )

    # Margin-specific recommendations
    if margin < -20:
        recommendations.append(
            "Negative margin (<-20%): Implement cost optimization initiatives. Review headcount efficiency, infrastructure costs, and gross margins."  # noqa: E501
        )
        recommendations.append(
            "Create path to positive EBITDA margin. Target: reduce burn by 30-50% while maintaining growth."  # noqa: E501
        )
    elif margin < 0:
        recommendations.append(
            "Negative margin: Continue path to profitability. Focus on improving gross margins and sales efficiency."  # noqa: E501
        )
    elif margin > 30 and growth < 20:
        recommendations.append(
            "High profitability but low growth: Consider reinvesting profits into growth initiatives (product, sales, marketing)."  # noqa: E501
        )

    # Balance recommendations
    if growth < 10 and margin < 10:
        recommendations.append(
            "CRITICAL: Both metrics weak. Conduct comprehensive business review - evaluate product-market fit, unit economics, and organizational efficiency."  # noqa: E501
        )
        recommendations.append("Consider: product pivot, market repositioning, or strategic alternatives.")  # noqa: E501
    elif abs(growth) < abs(margin) and stage in (GrowthStage.EARLY, GrowthStage.GROWTH):
        recommendations.append(
            "For your stage, consider shifting from profitability focus to growth investments."
        )
    elif margin < 0 and growth < margin * -1:
        recommendations.append(
            "Burn exceeds growth rate - unsustainable. Reduce costs or accelerate revenue growth urgently."  # noqa: E501
        )

    # Stage-specific recommendations
    if stage == GrowthStage.EARLY:
        recommendations.append(
            "Early stage: Prioritize product-market fit and growth. Profitability can wait."
        )
        recommendations.append("Target: >50% growth rate, even with negative margins.")
    elif stage == GrowthStage.GROWTH:
        recommendations.append("Growth stage: Balance rapid expansion with improving unit economics.")  # noqa: E501
        recommendations.append("Target: 30-50% growth with path to profitability clear.")
    elif stage == GrowthStage.SCALE:
        recommendations.append("Scale stage: Optimize for efficient growth.")
        recommendations.append("Target: 20-40% growth with positive EBITDA margins.")
    elif stage == GrowthStage.MATURE:
        recommendations.append("Mature stage: Focus on profitability and sustainable growth.")
        recommendations.append("Target: 10-30% growth with 20%+ EBITDA margins.")

    # Tactical recommendations
    if score < 40:
        recommendations.append(
            "Track Rule of 40 monthly. Set quarterly OKRs to improve score through growth acceleration, margin improvement, or both."  # noqa: E501
        )
        recommendations.append(
            "Consider: Implement zero-based budgeting, optimize CAC payback, improve gross margins, or accelerate product-led growth."  # noqa: E501
        )

    return recommendations


def _analyze_trends(
    current_growth: float,
    current_margin: float,
    previous_growth: float,
    previous_margin: float,
    current_score: float,
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
        analysis.append(f"Rule of 40 improved by {score_change:.1f} points ({previous_score:.1f}% → {current_score:.1f}%) - Positive trend!")  # noqa: E501
    elif score_change < 0:
        analysis.append(f"Rule of 40 declined by {abs(score_change):.1f} points ({previous_score:.1f}% → {current_score:.1f}%) - Negative trend.")  # noqa: E501
    else:
        analysis.append(f"Rule of 40 unchanged at {current_score:.1f}%.")

    # Growth trend
    if abs(growth_change) > 0.1:
        direction = "increased" if growth_change > 0 else "decreased"
        analysis.append(f"Growth {direction} by {abs(growth_change):.1f} points ({previous_growth:.1f}% → {current_growth:.1f}%)")  # noqa: E501

    # Margin trend
    if abs(margin_change) > 0.1:
        direction = "improved" if margin_change > 0 else "declined"
        analysis.append(f"EBITDA margin {direction} by {abs(margin_change):.1f} points ({previous_margin:.1f}% → {current_margin:.1f}%)")  # noqa: E501

    # Interpretation
    if score_change > 5:
        analysis.append("Strong improvement - maintaining this momentum is critical.")
    elif score_change > 0:
        analysis.append("Modest improvement - continue executing on current strategy.")
    elif score_change > -5:
        analysis.append("Slight decline - monitor closely and identify root causes.")
    else:
        analysis.append("Significant decline - requires immediate attention and corrective action.")

    # Specific trend patterns
    if growth_change < 0 and margin_change < 0:
        analysis.append("WARNING: Both growth and profitability declining - urgent intervention needed.")  # noqa: E501
    elif growth_change > 0 and margin_change > 0:
        analysis.append("Excellent: Improving both growth and profitability simultaneously.")
    elif growth_change > 0 and margin_change < 0:
        analysis.append("Trading profitability for growth - ensure this is intentional and sustainable.")  # noqa: E501
    elif growth_change < 0 and margin_change > 0:
        analysis.append("Trading growth for profitability - ensure this is intentional and appropriate for stage.")  # noqa: E501

    return "\n".join(analysis)


def format_result_as_json(result: RuleOf40Result) -> str:
    """Format Rule of 40 result as JSON.

    Args:
        result: RuleOf40Result to format

    Returns:
        JSON string representation
    """
    output = {
        "rule_of_40_score": round(result.rule_of_40_score, 2),
        "weighted_rule_of_40": round(result.weighted_rule_of_40, 2),
        "revenue_growth_rate": round(result.revenue_growth_rate, 2),
        "ebitda_margin": round(result.ebitda_margin, 2),
        "health_status": result.health_status.value,
        "benchmark_notes": result.benchmark_notes,
        "balance_analysis": result.balance_analysis,
        "recommendations": result.recommendations,
    }

    if result.trend_analysis:
        output["trend_analysis"] = result.trend_analysis

    if result.magic_number:
        output["magic_number"] = result.magic_number

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
    lines.append(f"- **Rule of 40 Score**: {result.rule_of_40_score:.1f}%")
    lines.append(f"- **Weighted Rule of 40**: {result.weighted_rule_of_40:.1f}%")
    lines.append(f"- **Revenue Growth Rate**: {result.revenue_growth_rate:.1f}%")
    lines.append(f"- **EBITDA Margin**: {result.ebitda_margin:.1f}%")
    lines.append(f"- **Health Status**: {result.health_status.value.upper()}")
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
            lines.append(f"- **Magic Number**: {mn['magic_number']:.2f}")
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
        epilog="""
Examples:
  # Interactive mode
  python rule_of_40.py

  # JSON input from stdin
  echo '{"revenue_growth_rate": 50, "ebitda_margin": -5}' | python rule_of_40.py

  # JSON file input
  python rule_of_40.py < input.json
  python rule_of_40.py --input input.json

  # Output formats
  python rule_of_40.py --format json
  python rule_of_40.py --format markdown
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
