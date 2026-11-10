# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Unit Economics Calculator for SaaS Financial Analysis.

This module provides comprehensive unit economics calculations including:
- CAC (Customer Acquisition Cost)
- LTV (Lifetime Value)
- LTV:CAC Ratio
- CAC Payback Period
- Magic Number

Based on industry-standard formulas from:
- David Skok (Matrix Partners) - SaaS Playbook
- Brad Feld (Foundry Group) - SaaS Metrics
- Tomasz Tunguz (Theory Ventures) - Growth benchmarks

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from scripts.input_check import checked_input, limits, read_json_input  # noqa: E402
from scripts.utils.enums import MetricHealth  # noqa: E402
from scripts.utils.exact import Number, as_written, shown  # noqa: E402
from scripts.utils.magic_number import (
    calculate_magic_number as _canonical_magic_number,  # noqa: E402
)

# Printed with a Magic Number whose prior-quarter spend was estimated (ADR-005).
ESTIMATE_NOTE = (
    "The prior quarter's S&M spend was not given, so the Magic Number cannot be calculated "
    "reliably. This figure estimates that spend as (sales costs + marketing costs) × 3 / "
    "period months. Recalculate it with the prior quarter's S&M spend before anyone uses "
    "it as fact."
)


def calculate_ltv_safe(arpu: Number, gross_margin: Number, monthly_churn_rate: Number) -> Optional[Number]:  # noqa: E501
    """
    Calculate LTV safely, returning None if churn rate is 0.

    Formula: ARPU * gross_margin / monthly_churn_rate
    Returns None if monthly_churn_rate == 0 (infinite lifetime is not representable).
    The result is exact (a Fraction).
    """
    from scripts.utils.calculators import safe_divide
    monthly_gp = as_written(arpu) * as_written(gross_margin)
    return safe_divide(monthly_gp, as_written(monthly_churn_rate))


def calculate_cac_safe(total_spend: Number, new_customers: int) -> Optional[Number]:
    """
    Calculate CAC safely, returning None if new_customers is 0.

    Formula: total_spend / new_customers
    The result is exact (a Fraction).
    """
    from scripts.utils.calculators import safe_divide
    return safe_divide(as_written(total_spend), as_written(new_customers))


def calculate_cac_payback_safe(cac: Number, arpu: Number, gross_margin: Number) -> Optional[Number]:  # noqa: E501
    """
    Calculate CAC payback period in months, returning None if gross margin is 0.

    Formula: cac / (arpu * gross_margin)
    The result is exact (a Fraction).
    """
    from scripts.utils.calculators import safe_divide
    monthly_gp = as_written(arpu) * as_written(gross_margin)
    return safe_divide(as_written(cac), monthly_gp)


@dataclass
class CACInput:
    """Input data for Customer Acquisition Cost calculation.

    Attributes:
        sales_costs: Total sales team costs including salaries, commissions, benefits
        marketing_costs: Total marketing spend including advertising, content, events
        new_customers: Number of new customers acquired in the period
        period_months: Number of months over which costs were incurred (default: 12)
    """

    sales_costs: float = limits(gt=0, le=1_000_000_000)
    marketing_costs: float = limits(ge=0, le=1_000_000_000)
    new_customers: int = limits(gt=0)
    period_months: int = limits(gt=0, le=60, default=12)


@dataclass
class LTVInput:
    """Input data for Lifetime Value calculation.

    Attributes:
        arpu: Average Revenue Per User per month
        gross_margin_percent: Gross margin as a percentage (0-100)
        churn_rate_percent: Monthly churn rate as a percentage (0-100)
    """

    arpu: float = limits(gt=0, le=1_000_000)
    gross_margin_percent: float = limits(gt=0, le=100)
    churn_rate_percent: float = limits(gt=0, le=100)


@dataclass
class CACPaybackInput:
    """Input data for CAC Payback Period calculation.

    Attributes:
        cac: Customer Acquisition Cost
        arpu: Average Revenue Per User per month
        gross_margin_percent: Gross margin as a percentage (0-100)
    """

    cac: float = limits(gt=0)
    arpu: float = limits(gt=0)
    gross_margin_percent: float = limits(gt=0, le=100)


@dataclass
class MagicNumberInput:
    """Input data for Magic Number calculation.

    Attributes:
        quarterly_net_new_arr: Net new ARR added in the most recent quarter (can be negative)
        prior_quarter_sm_spend: Sales & Marketing spend in the prior quarter (must be > 0)
    """

    quarterly_net_new_arr: float
    prior_quarter_sm_spend: float = limits(gt=0, le=1_000_000_000)


@dataclass
class UnitEconomicsInput:
    """Comprehensive input for full unit economics analysis.

    Attributes:
        sales_costs: Total sales team costs
        marketing_costs: Total marketing spend
        new_customers: Number of new customers acquired
        arpu: Average Revenue Per User per month
        gross_margin_percent: Gross margin as a percentage (0-100)
        churn_rate_percent: Monthly churn rate as a percentage (0-100)
        net_new_arr: Quarterly net new ARR for Magic Number (×4 annualization applied
            internally; pass a quarterly figure, not annual)
        prior_quarter_sm_spend: S&M spend of the quarter before the quarterly net_new_arr (optional; estimated when absent)
        period_months: Number of months over which metrics were measured (default: 12)
    """  # noqa: E501

    sales_costs: float = limits(gt=0, le=1_000_000_000)
    marketing_costs: float = limits(ge=0, le=1_000_000_000)
    new_customers: int = limits(gt=0)
    arpu: float = limits(gt=0, le=1_000_000)
    gross_margin_percent: float = limits(gt=0, le=100)
    churn_rate_percent: float = limits(gt=0, le=100)
    net_new_arr: Optional[float] = None
    prior_quarter_sm_spend: Optional[float] = limits(gt=0, le=1_000_000_000, default=None)
    period_months: int = limits(gt=0, le=60, default=12)


# The classes input_check reads, in the order fields.json recorded them.
INPUT_CLASSES = (CACInput, LTVInput, CACPaybackInput, MagicNumberInput, UnitEconomicsInput)


@dataclass
class CACResult:
    """Result of CAC calculation.

    Attributes:
        cac: Customer Acquisition Cost in dollars
        total_acquisition_costs: Total sales and marketing costs
        new_customers: Number of new customers acquired
        health_status: Health assessment of CAC value
        benchmark_notes: Benchmark comparison notes
    """

    cac: Number
    total_acquisition_costs: Number
    new_customers: int
    health_status: MetricHealth
    benchmark_notes: str


@dataclass
class LTVResult:
    """Result of LTV calculation.

    Attributes:
        ltv: Lifetime Value in dollars
        arpu: Average Revenue Per User per month
        gross_margin_percent: Gross margin percentage
        churn_rate_percent: Monthly churn rate percentage
        average_customer_lifespan_months: Expected customer lifespan
        health_status: Health assessment of LTV value
        benchmark_notes: Benchmark comparison notes
    """

    ltv: Number
    arpu: Number
    gross_margin_percent: Number
    churn_rate_percent: Number
    average_customer_lifespan_months: Number
    health_status: MetricHealth
    benchmark_notes: str


@dataclass
class LTVCACRatioResult:
    """Result of LTV:CAC Ratio calculation.

    Attributes:
        ratio: LTV:CAC ratio
        ltv: Lifetime Value
        cac: Customer Acquisition Cost
        health_status: Health assessment of ratio
        benchmark_notes: Benchmark comparison notes
    """

    ratio: Number
    ltv: Number
    cac: Number
    health_status: MetricHealth
    benchmark_notes: str


@dataclass
class CACPaybackResult:
    """Result of CAC Payback Period calculation.

    Attributes:
        payback_months: Months to recover CAC
        cac: Customer Acquisition Cost
        monthly_gross_profit: Monthly gross profit per customer
        health_status: Health assessment of payback period
        benchmark_notes: Benchmark comparison notes
    """

    payback_months: Number
    cac: Number
    monthly_gross_profit: Number
    health_status: MetricHealth
    benchmark_notes: str


@dataclass
class MagicNumberResult:
    """Result of Magic Number calculation.

    Attributes:
        magic_number: Magic Number value
        quarterly_net_new_arr: Quarterly net new ARR
        prior_quarter_sm_spend: Prior quarter sales & marketing spend
        efficiency_interpretation: Interpretation of efficiency
        health_status: Health assessment
        benchmark_notes: Benchmark comparison notes, or None for an estimate
        is_estimate: True when the prior quarter's spend was estimated, not given
        estimate_note: ESTIMATE_NOTE for an estimate, else None
    """

    magic_number: Number
    quarterly_net_new_arr: Number
    prior_quarter_sm_spend: Number
    efficiency_interpretation: str
    health_status: MetricHealth
    benchmark_notes: Optional[str]
    is_estimate: bool = False
    estimate_note: Optional[str] = None


@dataclass
class UnitEconomicsResult:
    """Comprehensive unit economics analysis result.

    Attributes:
        cac_result: CAC calculation result
        ltv_result: LTV calculation result
        ltv_cac_ratio_result: LTV:CAC ratio result
        payback_result: CAC Payback Period result
        magic_number_result: Magic Number result (optional)
        overall_health: Overall unit economics health
        recommendations: List of actionable recommendations
    """

    cac_result: CACResult
    ltv_result: LTVResult
    ltv_cac_ratio_result: LTVCACRatioResult
    payback_result: CACPaybackResult
    magic_number_result: Optional[MagicNumberResult]
    overall_health: MetricHealth
    recommendations: list[str]


def calculate_cac(data: CACInput) -> CACResult:
    """Calculate Customer Acquisition Cost (CAC).

    Formula: CAC = (Sales Costs + Marketing Costs) / New Customers

    Industry benchmarks:
    - B2B SaaS: $200-$1,500+ depending on ACV
    - B2C SaaS: $50-$500
    - Enterprise SaaS: $10,000-$50,000+

    Args:
        data: Input data for CAC calculation

    Returns:
        CACResult with calculated CAC and health assessment

    Example:
        >>> from scripts.input_check import build
        >>> input_data = build(
        ...     CACInput,
        ...     sales_costs=500000,
        ...     marketing_costs=300000,
        ...     new_customers=100
        ... )
        >>> result = calculate_cac(input_data)
        >>> print(f"CAC: ${shown(result.cac, 2):,.2f}")
        CAC: $8,000.00
    """
    total_costs = as_written(data.sales_costs) + as_written(data.marketing_costs)
    cac = total_costs / as_written(data.new_customers)

    # Assess health based on general benchmarks
    # Note: Real assessment should consider ACV and business model
    if cac < 100:
        health = MetricHealth.EXCELLENT
        notes = "Very efficient acquisition (CAC < $100). Common for viral B2C products."
    elif cac < 500:
        health = MetricHealth.GOOD
        notes = "Healthy CAC ($100-$500). Typical for SMB B2C/B2B SaaS."
    elif cac < 2000:
        health = MetricHealth.WARNING
        notes = "Moderate CAC ($500-$2,000). Ensure LTV:CAC ratio is healthy (>3:1)."
    elif cac < 10000:
        health = MetricHealth.WARNING
        notes = "High CAC ($2,000-$10,000). Acceptable only for high-ACV enterprise deals."
    else:
        health = MetricHealth.CRITICAL
        notes = "Very high CAC (>$10,000). Requires very high ACV and long customer lifetime."

    return CACResult(
        cac=cac,
        total_acquisition_costs=total_costs,
        new_customers=data.new_customers,
        health_status=health,
        benchmark_notes=notes,
    )


def calculate_ltv(data: LTVInput) -> LTVResult:
    """Calculate Customer Lifetime Value (LTV).

    Formula: LTV = ARPU × (Gross Margin % / 100) / (Churn Rate % / 100)

    Industry benchmarks:
    - B2B SaaS: $5,000-$50,000+ depending on segment
    - B2C SaaS: $200-$2,000
    - Enterprise SaaS: $50,000-$500,000+

    Args:
        data: Input data for LTV calculation

    Returns:
        LTVResult with calculated LTV and health assessment

    Example:
        >>> from scripts.input_check import build
        >>> input_data = build(
        ...     LTVInput,
        ...     arpu=100,
        ...     gross_margin_percent=80,
        ...     churn_rate_percent=2
        ... )
        >>> result = calculate_ltv(input_data)
        >>> print(f"LTV: ${shown(result.ltv, 2):,.2f}")
        LTV: $4,000.00
    """
    arpu = as_written(data.arpu)
    gross_margin_percent = as_written(data.gross_margin_percent)
    churn_rate_percent = as_written(data.churn_rate_percent)
    gross_margin_decimal = gross_margin_percent / 100
    churn_rate_decimal = churn_rate_percent / 100

    ltv = arpu * gross_margin_decimal / churn_rate_decimal

    # Calculate average customer lifespan in months
    average_lifespan = 1 / churn_rate_decimal

    # Assess health based on general benchmarks
    if ltv < 500:
        health = MetricHealth.WARNING
        notes = "Low LTV (<$500). Difficult to sustain healthy unit economics."
    elif ltv < 2000:
        health = MetricHealth.GOOD
        notes = "Moderate LTV ($500-$2,000). Common for SMB B2C SaaS."
    elif ltv < 10000:
        health = MetricHealth.GOOD
        notes = "Healthy LTV ($2,000-$10,000). Typical for B2B SaaS."
    else:
        health = MetricHealth.EXCELLENT
        notes = "Excellent LTV (>$10,000). Strong foundation for growth."

    return LTVResult(
        ltv=ltv,
        arpu=arpu,
        gross_margin_percent=gross_margin_percent,
        churn_rate_percent=churn_rate_percent,
        average_customer_lifespan_months=average_lifespan,
        health_status=health,
        benchmark_notes=notes,
    )


def calculate_ltv_cac_ratio(ltv: Number, cac: Number) -> LTVCACRatioResult:
    """Calculate LTV:CAC Ratio.

    Formula: LTV:CAC Ratio = LTV / CAC

    Industry benchmarks:
    - < 1:1 - Critical: Losing money on each customer
    - 1:1 to 3:1 - Warning: Marginally viable, need improvement
    - 3:1 to 5:1 - Good: Healthy unit economics
    - > 5:1 - Excellent: Very efficient, but may indicate under-investment in growth

    Args:
        ltv: Customer Lifetime Value
        cac: Customer Acquisition Cost

    Returns:
        LTVCACRatioResult with ratio and health assessment

    Raises:
        ValueError: If CAC is zero or negative

    Example:
        >>> result = calculate_ltv_cac_ratio(ltv=4000, cac=1000)
        >>> print(f"LTV:CAC Ratio: {shown(result.ratio, 2):.2f}:1")
        LTV:CAC Ratio: 4.00:1
    """
    ltv = as_written(ltv)
    cac = as_written(cac)
    if cac <= 0:
        raise ValueError("CAC must be positive")

    ratio = ltv / cac

    # Assess health based on industry benchmarks
    if ratio < 1:
        health = MetricHealth.CRITICAL
        notes = "Critical: LTV < CAC. Losing money on each customer. Need to reduce CAC or increase LTV."  # noqa: E501
    elif ratio < 3:
        health = MetricHealth.WARNING
        notes = "Warning: LTV:CAC < 3:1. Marginally viable. Focus on improving unit economics."
    elif ratio <= 5:
        health = MetricHealth.GOOD
        notes = "Good: LTV:CAC 3:1 to 5:1. Healthy unit economics. This is the target range."
    elif ratio <= 8:
        health = MetricHealth.EXCELLENT
        notes = "Excellent: LTV:CAC 5:1 to 8:1. Very efficient. Strong growth potential."
    else:
        health = MetricHealth.WARNING
        notes = "Very high ratio (>8:1). May indicate under-investment in growth. Consider increasing CAC to accelerate."  # noqa: E501

    return LTVCACRatioResult(
        ratio=ratio,
        ltv=ltv,
        cac=cac,
        health_status=health,
        benchmark_notes=notes,
    )


def calculate_cac_payback(data: CACPaybackInput) -> CACPaybackResult:
    """Calculate CAC Payback Period.

    Formula: CAC Payback Period = CAC / (ARPU × Gross Margin %)

    Industry benchmarks:
    - < 6 months - Excellent: Very efficient, enables rapid scaling
    - 6-12 months - Good: Acceptable for most SaaS businesses
    - 12-18 months - Warning: Long payback, limits growth
    - > 18 months - Critical: Too long, difficult to scale profitably

    Args:
        data: Input data for CAC Payback calculation

    Returns:
        CACPaybackResult with payback period and health assessment

    Example:
        >>> from scripts.input_check import build
        >>> input_data = build(
        ...     CACPaybackInput,
        ...     cac=1000,
        ...     arpu=100,
        ...     gross_margin_percent=80
        ... )
        >>> result = calculate_cac_payback(input_data)
        >>> print(f"Payback: {shown(result.payback_months, 1):.1f} months")
        Payback: 12.5 months
    """
    cac = as_written(data.cac)
    gross_margin_decimal = as_written(data.gross_margin_percent) / 100
    monthly_gross_profit = as_written(data.arpu) * gross_margin_decimal

    payback_months = cac / monthly_gross_profit

    # Assess health based on industry benchmarks
    if payback_months < 6:
        health = MetricHealth.EXCELLENT
        notes = "Excellent: Payback < 6 months. Very efficient, enables rapid scaling."
    elif payback_months <= 12:
        health = MetricHealth.GOOD
        notes = "Good: Payback 6-12 months. Acceptable for most SaaS businesses."
    elif payback_months <= 18:
        health = MetricHealth.WARNING
        notes = "Warning: Payback 12-18 months. Long payback limits growth velocity."
    else:
        health = MetricHealth.CRITICAL
        notes = "Critical: Payback > 18 months. Too long to scale profitably. Need to reduce CAC or increase ARPU."  # noqa: E501

    return CACPaybackResult(
        payback_months=payback_months,
        cac=cac,
        monthly_gross_profit=monthly_gross_profit,
        health_status=health,
        benchmark_notes=notes,
    )


def calculate_magic_number(data: MagicNumberInput) -> MagicNumberResult:
    """Calculate Magic Number (Sales Efficiency).

    Formula: Magic Number = (Quarterly Net New ARR × 4) / Prior Quarter S&M Spend

    Delegates to the canonical scripts.utils.magic_number.calculate_magic_number helper
    (single source of truth) and adapts its MagicNumberOutcome into MagicNumberResult.

    Args:
        data: Input data for Magic Number calculation

    Returns:
        MagicNumberResult with Magic Number and efficiency assessment

    Example:
        >>> from scripts.input_check import build
        >>> input_data = build(
        ...     MagicNumberInput,
        ...     quarterly_net_new_arr=1000000,
        ...     prior_quarter_sm_spend=800000,
        ... )
        >>> result = calculate_magic_number(input_data)
        >>> print(f"Magic Number: {shown(result.magic_number, 2):.2f}")
        Magic Number: 5.00
    """
    return _magic_number_result(data.quarterly_net_new_arr, data.prior_quarter_sm_spend)


def _magic_number_result(quarterly_net_new_arr: Number,
                         prior_quarter_sm_spend: Number) -> MagicNumberResult:
    """The MagicNumberResult for a spend above zero: a checked float, or an exact estimate."""
    outcome = _canonical_magic_number(quarterly_net_new_arr, prior_quarter_sm_spend)
    assert outcome.magic_number is not None, (
        "prior_quarter_sm_spend gt=0 guarantees a non-None magic number"
    )
    return MagicNumberResult(
        magic_number=outcome.magic_number,
        quarterly_net_new_arr=as_written(quarterly_net_new_arr),
        prior_quarter_sm_spend=as_written(prior_quarter_sm_spend),
        efficiency_interpretation=f"Magic Number: {shown(outcome.magic_number, 2):.2f}",
        health_status=outcome.health,
        benchmark_notes=outcome.interpretation,
    )


def calculate_unit_economics(data: UnitEconomicsInput) -> UnitEconomicsResult:
    """Perform comprehensive unit economics analysis.

    Calculates and analyzes:
    - Customer Acquisition Cost (CAC)
    - Lifetime Value (LTV)
    - LTV:CAC Ratio
    - CAC Payback Period
    - Magic Number (if net_new_arr provided)

    Args:
        data: Comprehensive unit economics input data

    Returns:
        UnitEconomicsResult with all metrics and recommendations

    Example:
        >>> from scripts.input_check import build
        >>> input_data = build(
        ...     UnitEconomicsInput,
        ...     sales_costs=500000,
        ...     marketing_costs=300000,
        ...     new_customers=100,
        ...     arpu=100,
        ...     gross_margin_percent=80,
        ...     churn_rate_percent=2,
        ...     net_new_arr=1000000
        ... )
        >>> result = calculate_unit_economics(input_data)
        >>> print(f"Overall Health: {result.overall_health}")
    """
    # Calculate CAC
    cac_input = CACInput(
        sales_costs=data.sales_costs,
        marketing_costs=data.marketing_costs,
        new_customers=data.new_customers,
        period_months=data.period_months,
    )
    cac_result = calculate_cac(cac_input)

    # Calculate LTV
    ltv_input = LTVInput(
        arpu=data.arpu,
        gross_margin_percent=data.gross_margin_percent,
        churn_rate_percent=data.churn_rate_percent,
    )
    ltv_result = calculate_ltv(ltv_input)

    # Calculate LTV:CAC Ratio
    ltv_cac_result = calculate_ltv_cac_ratio(ltv_result.ltv, cac_result.cac)

    # Calculate CAC Payback
    payback_input = CACPaybackInput(
        cac=cac_result.cac,
        arpu=data.arpu,
        gross_margin_percent=data.gross_margin_percent,
    )
    payback_result = calculate_cac_payback(payback_input)

    # Calculate Magic Number if data provided. LOCK-POINT B: the spend is one quarter's
    # S&M spend, prior_quarter_sm_spend when given. Otherwise it is estimated, exactly,
    # as (sales_costs + marketing_costs) × 3 / period_months, and the result is labelled
    # an estimate. The estimate is a Fraction, so it goes to _magic_number_result
    # directly, never through MagicNumberInput (whose float field is the checked input)
    # or check(): the given spend's limits do not apply to it. It can exceed
    # 1,000,000,000, and the inputs it comes from are already limited.
    magic_number_result = None
    if data.net_new_arr is not None:
        is_estimate = data.prior_quarter_sm_spend is None
        if is_estimate:
            pm = as_written(data.period_months)
            spend = (as_written(data.sales_costs) + as_written(data.marketing_costs)) * 3 / pm
        else:
            spend = data.prior_quarter_sm_spend
        magic_number_result = _magic_number_result(data.net_new_arr, spend)
        if is_estimate:  # an estimate prints no Notes sentence (ADR-005)
            magic_number_result.is_estimate = True
            magic_number_result.estimate_note = ESTIMATE_NOTE
            magic_number_result.benchmark_notes = None

    # Determine overall health (most conservative assessment)
    health_values = [
        cac_result.health_status,
        ltv_result.health_status,
        ltv_cac_result.health_status,
        payback_result.health_status,
    ]

    # An estimated Magic Number is not used as fact: it stays out of overall health.
    if magic_number_result and not magic_number_result.is_estimate:
        health_values.append(magic_number_result.health_status)

    # Overall health is the worst of all metrics
    if MetricHealth.CRITICAL in health_values:
        overall_health = MetricHealth.CRITICAL
    elif MetricHealth.WARNING in health_values:
        overall_health = MetricHealth.WARNING
    elif MetricHealth.GOOD in health_values:
        overall_health = MetricHealth.GOOD
    else:
        overall_health = MetricHealth.EXCELLENT

    # Generate recommendations
    recommendations = _generate_recommendations(
        cac_result,
        ltv_result,
        ltv_cac_result,
        payback_result,
        magic_number_result,
    )

    return UnitEconomicsResult(
        cac_result=cac_result,
        ltv_result=ltv_result,
        ltv_cac_ratio_result=ltv_cac_result,
        payback_result=payback_result,
        magic_number_result=magic_number_result,
        overall_health=overall_health,
        recommendations=recommendations,
    )


def _generate_recommendations(
    cac_result: CACResult,
    ltv_result: LTVResult,
    ltv_cac_result: LTVCACRatioResult,
    payback_result: CACPaybackResult,
    magic_number_result: Optional[MagicNumberResult],
) -> list[str]:
    """Generate actionable recommendations based on unit economics.

    Args:
        cac_result: CAC calculation result
        ltv_result: LTV calculation result
        ltv_cac_result: LTV:CAC ratio result
        payback_result: CAC Payback result
        magic_number_result: Magic Number result (optional)

    Returns:
        List of actionable recommendations
    """
    recommendations = []

    # CAC recommendations
    if cac_result.health_status in [MetricHealth.WARNING, MetricHealth.CRITICAL]:
        recommendations.append(
            f"High CAC (${shown(cac_result.cac, 2):,.2f}): Optimize acquisition channels, improve conversion rates, "  # noqa: E501
            "or focus on organic/referral growth."
        )

    # LTV recommendations
    if ltv_result.health_status in [MetricHealth.WARNING, MetricHealth.CRITICAL]:
        recommendations.append(
            f"Low LTV (${shown(ltv_result.ltv, 2):,.2f}): Reduce churn through better onboarding, increase ARPU via "  # noqa: E501
            "upsells/cross-sells, or improve product value."
        )

    # LTV:CAC recommendations
    if ltv_cac_result.health_status == MetricHealth.CRITICAL:
        recommendations.append(
            f"Critical LTV:CAC ratio ({shown(ltv_cac_result.ratio, 2):.2f}:1): Urgently need to reduce CAC or increase LTV. "  # noqa: E501
            "Current unit economics are not sustainable."
        )
    elif ltv_cac_result.health_status == MetricHealth.WARNING:
        if ltv_cac_result.ratio > 8:
            recommendations.append(
                f"Very high LTV:CAC ratio ({shown(ltv_cac_result.ratio, 2):.2f}:1): Consider increasing sales/marketing "  # noqa: E501
                "investment to accelerate growth while maintaining healthy economics."
            )
        else:
            recommendations.append(
                f"Suboptimal LTV:CAC ratio ({shown(ltv_cac_result.ratio, 2):.2f}:1): Target 3:1 or better. "  # noqa: E501
                "Balance CAC reduction with LTV improvement initiatives."
            )

    # Payback recommendations
    if payback_result.health_status in [MetricHealth.WARNING, MetricHealth.CRITICAL]:
        recommendations.append(
            f"Long CAC payback ({shown(payback_result.payback_months, 1):.1f} months): Target <12 months. "  # noqa: E501
            "Consider annual contracts, upfront payment discounts, or increase pricing."
        )

    # Magic Number recommendations. An estimate asks for the quarter's spend instead.
    if magic_number_result:
        if magic_number_result.is_estimate:
            recommendations.append(
                "Recalculate the Magic Number with the prior quarter's S&M spend: "
                f"{shown(magic_number_result.magic_number, 2):.2f} is an estimate."
            )
        elif magic_number_result.health_status in [MetricHealth.WARNING, MetricHealth.CRITICAL]:
            recommendations.append(
                f"Low Magic Number ({shown(magic_number_result.magic_number, 2):.2f}): Sales/marketing efficiency needs "  # noqa: E501
                "improvement. Optimize go-to-market strategy, improve sales productivity, or refine ICP."  # noqa: E501
            )

    # Churn-specific recommendations
    if ltv_result.churn_rate_percent > 5:
        recommendations.append(
            f"High monthly churn ({shown(ltv_result.churn_rate_percent, 1):.1f}%): Target <2-3% for B2B SaaS. "  # noqa: E501
            "Focus on product-market fit, customer success, and user onboarding."
        )

    # Gross margin recommendations
    if ltv_result.gross_margin_percent < 70:
        recommendations.append(
            f"Low gross margin ({shown(ltv_result.gross_margin_percent, 1):.1f}%): Target >80% for SaaS. "  # noqa: E501
            "Optimize infrastructure costs, improve operational efficiency, or increase pricing."
        )

    # General recommendations if everything is healthy
    if not recommendations:
        recommendations.append(
            "Unit economics are healthy! Focus on scaling efficiently while maintaining these metrics."  # noqa: E501
        )
        recommendations.append(
            "Continue monitoring cohort performance and segment-level unit economics for optimization opportunities."  # noqa: E501
        )

    return recommendations


def format_result_as_json(result: UnitEconomicsResult) -> str:
    """Format unit economics result as JSON.

    Args:
        result: Unit economics calculation result

    Returns:
        JSON string representation of the result
    """
    data = {
        "cac": {
            "value": float(shown(result.cac_result.cac, 2)),
            "total_acquisition_costs": float(shown(result.cac_result.total_acquisition_costs, 2)),
            "new_customers": result.cac_result.new_customers,
            "health_status": result.cac_result.health_status.value,
            "benchmark_notes": result.cac_result.benchmark_notes,
        },
        "ltv": {
            "value": float(shown(result.ltv_result.ltv, 2)),
            "arpu": float(shown(result.ltv_result.arpu, 2)),
            "gross_margin_percent": float(shown(result.ltv_result.gross_margin_percent, 2)),
            "churn_rate_percent": float(shown(result.ltv_result.churn_rate_percent, 2)),
            "average_customer_lifespan_months": float(shown(result.ltv_result.average_customer_lifespan_months, 1)),  # noqa: E501
            "health_status": result.ltv_result.health_status.value,
            "benchmark_notes": result.ltv_result.benchmark_notes,
        },
        "ltv_cac_ratio": {
            "ratio": float(shown(result.ltv_cac_ratio_result.ratio, 2)),
            "formatted": f"{shown(result.ltv_cac_ratio_result.ratio, 2):.2f}:1",
            "health_status": result.ltv_cac_ratio_result.health_status.value,
            "benchmark_notes": result.ltv_cac_ratio_result.benchmark_notes,
        },
        "cac_payback": {
            "payback_months": float(shown(result.payback_result.payback_months, 1)),
            "monthly_gross_profit": float(shown(result.payback_result.monthly_gross_profit, 2)),
            "health_status": result.payback_result.health_status.value,
            "benchmark_notes": result.payback_result.benchmark_notes,
        },
        "overall_health": result.overall_health.value,
        "recommendations": result.recommendations,
    }

    if result.magic_number_result:
        data["magic_number"] = {
            "value": float(shown(result.magic_number_result.magic_number, 2)),
            "quarterly_net_new_arr": float(shown(result.magic_number_result.quarterly_net_new_arr, 2)),  # noqa: E501
            "prior_quarter_sm_spend": float(shown(result.magic_number_result.prior_quarter_sm_spend, 2)),  # noqa: E501
            "efficiency_interpretation": result.magic_number_result.efficiency_interpretation,
            "health_status": result.magic_number_result.health_status.value,
            "benchmark_notes": result.magic_number_result.benchmark_notes,
            "is_estimate": result.magic_number_result.is_estimate,
            "estimate_note": result.magic_number_result.estimate_note,
        }

    return json.dumps(data, indent=2)


def format_result_as_markdown(result: UnitEconomicsResult) -> str:
    """Format unit economics result as Markdown.

    Args:
        result: Unit economics calculation result

    Returns:
        Markdown string representation of the result
    """
    lines = [
        "# Unit Economics Analysis",
        "",
        f"**Overall Health:** {result.overall_health.value.upper()}",
        "",
        "## Customer Acquisition Cost (CAC)",
        f"- **CAC:** ${shown(result.cac_result.cac, 2):,.2f}",
        f"- **Total Acquisition Costs:** ${shown(result.cac_result.total_acquisition_costs, 2):,.2f}",  # noqa: E501
        f"- **New Customers:** {result.cac_result.new_customers:,}",
        f"- **Health:** {result.cac_result.health_status.value}",
        f"- **Notes:** {result.cac_result.benchmark_notes}",
        "",
        "## Lifetime Value (LTV)",
        f"- **LTV:** ${shown(result.ltv_result.ltv, 2):,.2f}",
        f"- **ARPU:** ${shown(result.ltv_result.arpu, 2):,.2f}/month",
        f"- **Gross Margin:** {shown(result.ltv_result.gross_margin_percent, 1):.1f}%",
        f"- **Monthly Churn:** {shown(result.ltv_result.churn_rate_percent, 2):.2f}%",
        f"- **Average Customer Lifespan:** {shown(result.ltv_result.average_customer_lifespan_months, 1):.1f} months",  # noqa: E501
        f"- **Health:** {result.ltv_result.health_status.value}",
        f"- **Notes:** {result.ltv_result.benchmark_notes}",
        "",
        "## LTV:CAC Ratio",
        f"- **Ratio:** {shown(result.ltv_cac_ratio_result.ratio, 2):.2f}:1",
        f"- **Health:** {result.ltv_cac_ratio_result.health_status.value}",
        f"- **Notes:** {result.ltv_cac_ratio_result.benchmark_notes}",
        "",
        "## CAC Payback Period",
        f"- **Payback:** {shown(result.payback_result.payback_months, 1):.1f} months",
        f"- **Monthly Gross Profit:** ${shown(result.payback_result.monthly_gross_profit, 2):,.2f}",
        f"- **Health:** {result.payback_result.health_status.value}",
        f"- **Notes:** {result.payback_result.benchmark_notes}",
        "",
    ]

    mn = result.magic_number_result
    if mn:
        value_label = " (estimate)" if mn.is_estimate else ""
        spend_label = " (estimated from the period's spend)" if mn.is_estimate else ""
        lines.extend([
            "## Magic Number (Sales Efficiency)",
            f"- **Magic Number:** {shown(mn.magic_number, 2):.2f}{value_label}",
            f"- **Quarterly Net New ARR:** ${shown(mn.quarterly_net_new_arr, 2):,.2f}",
            f"- **Prior Quarter S&M Spend:** ${shown(mn.prior_quarter_sm_spend, 2):,.2f}{spend_label}",  # noqa: E501
            f"- **Interpretation:** {mn.efficiency_interpretation}",
            f"- **Health:** {mn.health_status.value}",
        ])
        if mn.benchmark_notes is not None:
            lines.append(f"- **Notes:** {mn.benchmark_notes}")
        if mn.is_estimate:
            lines.append(f"- **Estimate:** {mn.estimate_note}")
        lines.append("")

    lines.extend([
        "## Recommendations",
        "",
    ])

    for i, rec in enumerate(result.recommendations, 1):
        lines.append(f"{i}. {rec}")

    return "\n".join(lines)


def main() -> None:
    """CLI entry point for unit economics calculator.

    Reads JSON input from `--input <file>`, else from stdin, else asks
    for each value with interactive prompts. Prints the report.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Unit Economics Calculator for SaaS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python unit_economics.py

  # JSON input from stdin
  echo '{"sales_costs": 500000, "marketing_costs": 300000, ...}' | python unit_economics.py

  # JSON file input
  python unit_economics.py < input.json
  python unit_economics.py --input input.json

  # Output formats
  python unit_economics.py --format json
  python unit_economics.py --format markdown
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
        data = checked_input(UnitEconomicsInput, read_json_input(args.input))
    else:
        # Interactive mode
        print("Unit Economics Calculator")
        print("=" * 50)
        print()

        try:
            answers: Dict[str, Any] = {
                "sales_costs": float(input("Sales costs ($): ")),
                "marketing_costs": float(input("Marketing costs ($): ")),
                "new_customers": int(input("Number of new customers: ")),
                "arpu": float(input("Average Revenue Per User per month ($): ")),
                "gross_margin_percent": float(input("Gross margin (%): ")),
                "churn_rate_percent": float(input("Monthly churn rate (%): ")),
            }

            net_new_arr_input = input("Quarterly net new ARR ($ or press Enter to skip): ").strip()
            if net_new_arr_input:
                answers["net_new_arr"] = float(net_new_arr_input)
                spend_input = input(
                    "Sales & Marketing spend in the prior quarter "
                    "($ or press Enter to estimate it): "
                ).strip()
                if spend_input:
                    answers["prior_quarter_sm_spend"] = float(spend_input)
                else:
                    print(
                        "Without the prior quarter's S&M spend the Magic Number cannot be "
                        "calculated reliably; it will be estimated from the period's spend "
                        "and marked as an estimate."
                    )

            period_months_input = input("Period in months (default 12): ").strip()
            if period_months_input:
                answers["period_months"] = int(period_months_input)

        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)

        data = checked_input(UnitEconomicsInput, answers)

    # Calculate unit economics
    try:
        result = calculate_unit_economics(data)
    except Exception as e:
        print(f"Error calculating unit economics: {e}", file=sys.stderr)
        sys.exit(1)

    # Output results
    print()
    if args.format == "json":
        print(format_result_as_json(result))
    else:
        print(format_result_as_markdown(result))


if __name__ == "__main__":
    main()
