# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic>=2.5,<2.14"]
# ///
"""AI ROI Calculator for AI Economics Analysis.

This module provides comprehensive AI economics analysis including:
- AI cost tracking (per interaction, per user, % of revenue)
- AI value attribution (revenue, productivity, retention)
- AI ROI calculation and break-even analysis
- Cost optimization opportunities
- CFO-ready output format

Based on emerging AI economics frameworks and product-led growth principles.

The AI ROI Calculator is the critical differentiator for this plugin, enabling
teams to:
- Justify AI investments with clear ROI
- Track AI costs across models/providers
- Attribute business value to AI capabilities
- Identify cost optimization opportunities
- Make data-driven decisions about AI features

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from pydantic import BaseModel, Field, field_validator, model_validator  # noqa: E402

# AIProvider re-exported (not used internally) for tests/consumers importing it here.
from scripts.utils.enums import AIProvider, MetricHealth  # noqa: E402, F401


def calculate_roi_percentage_safe(value: float, cost: float) -> Optional[float]:
    """
    Calculate ROI percentage safely, returning None if cost is 0.

    Formula: (value - cost) / cost * 100
    Returns None if cost == 0.
    """
    from scripts.utils.calculators import safe_divide
    net = value - cost
    ratio = safe_divide(net, cost)
    if ratio is None:
        return None
    return ratio * 100


class AICostInput(BaseModel):
    """Input data for AI cost tracking.

    Attributes:
        total_ai_cost: Total AI costs for the period
        ai_interactions: Total number of AI interactions/API calls
        active_users: Number of active users during the period
        total_revenue: Total revenue for the period
        period_months: Number of months (default: 1)
        provider_breakdown: Optional breakdown by provider (dict of provider: cost)
        infrastructure_cost: Optional AI infrastructure costs (hosting, storage)
    """

    total_ai_cost: float = Field(gt=0, description="Total AI costs for the period")
    ai_interactions: int = Field(gt=0, description="Total AI interactions/API calls")
    active_users: int = Field(gt=0, description="Number of active users")
    total_revenue: float = Field(gt=0, description="Total revenue for the period")
    period_months: int = Field(default=1, gt=0, le=60, description="Period in months")
    provider_breakdown: Optional[dict[str, float]] = Field(
        default=None, description="Breakdown of costs by provider"
    )
    infrastructure_cost: Optional[float] = Field(
        default=None, ge=0, description="AI infrastructure costs"
    )

    @field_validator("total_ai_cost", "total_revenue")
    @classmethod
    def validate_amounts(cls, v: float) -> float:
        """Ensure amounts are reasonable."""
        if v > 1_000_000_000:  # $1B sanity check
            raise ValueError("Amount seems unreasonably high (>$1B)")
        return v

    @field_validator("provider_breakdown")
    @classmethod
    def validate_provider_breakdown(cls, v: Optional[dict]) -> Optional[dict]:
        """Validate provider breakdown if provided."""
        if v is not None:
            total = sum(v.values())
            if total < 0:
                raise ValueError("Provider breakdown costs cannot be negative")
        return v


class AIValueInput(BaseModel):
    """Input data for AI value attribution.

    Attributes:
        ai_enabled_revenue: Revenue from AI-powered features
        non_ai_revenue: Revenue from non-AI features
        premium_pricing_uplift: Price premium for AI capabilities (percentage)
        time_saved_hours: Total hours saved through AI automation
        employee_fully_loaded_cost: Fully-loaded cost per employee hour
        ai_feature_churn_rate: Churn rate for users with AI features (%)
        non_ai_churn_rate: Churn rate for users without AI features (%)
        ai_expansion_revenue: Expansion revenue driven by AI adoption
        time_to_value_reduction_days: Days reduced in time-to-value due to AI
    """

    ai_enabled_revenue: float = Field(ge=0, description="Revenue from AI-powered features")
    non_ai_revenue: float = Field(ge=0, description="Revenue from non-AI features")
    premium_pricing_uplift: Optional[float] = Field(
        default=None, ge=0, le=1000, description="Premium pricing percentage for AI"
    )
    time_saved_hours: Optional[float] = Field(
        default=None, ge=0, description="Hours saved through AI automation"
    )
    employee_fully_loaded_cost: Optional[float] = Field(
        default=None, gt=0, description="Fully-loaded cost per employee hour"
    )
    ai_feature_churn_rate: Optional[float] = Field(
        default=None, ge=0, le=100, description="Churn rate with AI features (%)"
    )
    non_ai_churn_rate: Optional[float] = Field(
        default=None, ge=0, le=100, description="Churn rate without AI features (%)"
    )
    ai_expansion_revenue: Optional[float] = Field(
        default=None, ge=0, description="Expansion revenue from AI adoption"
    )
    time_to_value_reduction_days: Optional[float] = Field(
        default=None, ge=0, description="Time-to-value reduction in days"
    )

    @model_validator(mode="after")
    def validate_productivity_data(self) -> "AIValueInput":
        """Ensure productivity calculation has complete data."""
        has_time_saved = self.time_saved_hours is not None
        has_employee_cost = self.employee_fully_loaded_cost is not None

        if has_time_saved != has_employee_cost:
            raise ValueError(
                "Both time_saved_hours and employee_fully_loaded_cost must be provided for productivity value calculation"  # noqa: E501
            )

        return self

    @model_validator(mode="after")
    def validate_retention_data(self) -> "AIValueInput":
        """Ensure retention calculation has complete data."""
        has_ai_churn = self.ai_feature_churn_rate is not None
        has_non_ai_churn = self.non_ai_churn_rate is not None

        if has_ai_churn != has_non_ai_churn:
            raise ValueError(
                "Both ai_feature_churn_rate and non_ai_churn_rate must be provided for retention impact calculation"  # noqa: E501
            )

        return self


class AIROIInput(BaseModel):
    """Comprehensive input for AI ROI calculation.

    Combines cost tracking and value attribution data.

    Attributes:
        cost_data: AI cost tracking data
        value_data: AI value attribution data
    """

    cost_data: AICostInput
    value_data: AIValueInput


@dataclass
class AICostResult:
    """Result of AI cost tracking analysis.

    Attributes:
        cost_per_interaction: Cost per AI interaction/API call
        cost_per_user_per_month: AI cost per active user per month
        ai_cost_percentage_of_revenue: AI costs as percentage of revenue
        total_ai_cost: Total AI costs
        annualized_ai_cost: Annualized AI cost projection
        cost_trend_analysis: Analysis of cost trends
        provider_breakdown_analysis: Optional provider cost breakdown
        health_status: Health assessment of AI costs
        optimization_opportunities: List of cost optimization opportunities
    """

    cost_per_interaction: float
    cost_per_user_per_month: float
    ai_cost_percentage_of_revenue: float
    total_ai_cost: float
    annualized_ai_cost: float
    cost_trend_analysis: str
    provider_breakdown_analysis: Optional[dict[str, float]]
    health_status: MetricHealth
    optimization_opportunities: list[str]


@dataclass
class AIValueResult:
    """Result of AI value attribution analysis.

    Attributes:
        ai_enabled_revenue: Revenue from AI-powered features
        ai_revenue_percentage: AI-enabled revenue as % of total revenue
        premium_pricing_value: Value captured through premium pricing
        productivity_value: Value from time saved (productivity multiplier)
        retention_value: Value from improved retention
        expansion_value: Value from expansion revenue
        time_to_value_acceleration: Value from faster time-to-value
        total_ai_value: Total attributed AI value
        value_breakdown: Breakdown of value sources
        health_status: Health assessment of AI value
    """

    ai_enabled_revenue: float
    ai_revenue_percentage: float
    premium_pricing_value: Optional[float]
    productivity_value: Optional[float]
    retention_value: Optional[float]
    expansion_value: Optional[float]
    time_to_value_acceleration: Optional[float]
    total_ai_value: float
    value_breakdown: dict[str, float]
    health_status: MetricHealth


@dataclass
class AIROIResult:
    """Result of comprehensive AI ROI analysis.

    Attributes:
        ai_roi: AI ROI percentage ((Value - Cost) / Cost × 100)
        ai_roi_ratio: AI ROI ratio (Value / Cost)
        net_ai_value: Net AI value (Value - Cost)
        break_even_months: Months to break even on AI investment
        payback_period: Payback period for AI investment
        cost_result: AI cost analysis
        value_result: AI value attribution
        overall_health: Overall AI economics health
        recommendations: Actionable recommendations
        roi_by_feature: Optional ROI breakdown by feature
    """

    ai_roi: float
    ai_roi_ratio: float
    net_ai_value: float
    break_even_months: Optional[float]
    payback_period: Optional[float]
    cost_result: AICostResult
    value_result: AIValueResult
    overall_health: MetricHealth
    recommendations: list[str]
    roi_by_feature: Optional[dict[str, float]]


def calculate_ai_costs(data: AICostInput) -> AICostResult:
    """Calculate AI cost metrics.

    Analyzes AI costs across multiple dimensions:
    - Cost per interaction
    - Cost per user per month
    - AI costs as percentage of revenue
    - Provider breakdown
    - Optimization opportunities

    Args:
        data: Input data for AI cost calculation

    Returns:
        AICostResult with detailed cost analysis

    Example:
        >>> input_data = AICostInput(
        ...     total_ai_cost=50000,
        ...     ai_interactions=1000000,
        ...     active_users=5000,
        ...     total_revenue=500000,
        ...     period_months=1
        ... )
        >>> result = calculate_ai_costs(input_data)
        >>> print(f"Cost per interaction: ${result.cost_per_interaction:.4f}")
        Cost per interaction: $0.0500
    """
    # Calculate cost per interaction
    cost_per_interaction = data.total_ai_cost / data.ai_interactions

    # Calculate cost per user per month
    cost_per_user_per_month = data.total_ai_cost / data.active_users / data.period_months

    # Calculate AI cost as percentage of revenue
    ai_cost_percentage = (data.total_ai_cost / data.total_revenue) * 100

    # Annualize costs
    annualized_ai_cost = data.total_ai_cost * (12 / data.period_months)

    # Include infrastructure costs if provided
    total_cost = data.total_ai_cost
    if data.infrastructure_cost:
        total_cost += data.infrastructure_cost
        annualized_ai_cost += data.infrastructure_cost * (12 / data.period_months)

    # Assess health based on AI cost as % of revenue
    if ai_cost_percentage < 5:
        health = MetricHealth.EXCELLENT
        cost_assessment = "Excellent: AI costs < 5% of revenue. Very efficient."
    elif ai_cost_percentage < 10:
        health = MetricHealth.GOOD
        cost_assessment = "Good: AI costs 5-10% of revenue. Healthy range for AI-powered products."
    elif ai_cost_percentage < 20:
        health = MetricHealth.WARNING
        cost_assessment = "Warning: AI costs 10-20% of revenue. Monitor closely and optimize."
    else:
        health = MetricHealth.CRITICAL
        cost_assessment = "Critical: AI costs > 20% of revenue. Urgent optimization needed."

    # Cost trend analysis
    cost_trend = []
    cost_trend.append(cost_assessment)
    cost_trend.append(f"Cost per interaction: ${cost_per_interaction:.4f}")
    cost_trend.append(f"Cost per user per month: ${cost_per_user_per_month:.2f}")
    cost_trend.append(f"Annualized AI cost: ${annualized_ai_cost:,.2f}")

    # Provider breakdown analysis
    provider_breakdown_analysis = None
    if data.provider_breakdown:
        provider_breakdown_analysis = {}
        for provider, cost in data.provider_breakdown.items():
            percentage = (cost / data.total_ai_cost) * 100
            provider_breakdown_analysis[provider] = {
                "cost": cost,
                "percentage": percentage,
                "cost_per_interaction": cost / data.ai_interactions,
            }
        cost_trend.append("\nProvider Breakdown:")
        for provider, metrics in provider_breakdown_analysis.items():
            cost_trend.append(
                f"  - {provider}: ${metrics['cost']:,.2f} ({metrics['percentage']:.1f}% of total)"
            )

    # Generate optimization opportunities
    optimization_opportunities = _generate_cost_optimizations(
        cost_per_interaction, ai_cost_percentage, data.provider_breakdown
    )

    return AICostResult(
        cost_per_interaction=cost_per_interaction,
        cost_per_user_per_month=cost_per_user_per_month,
        ai_cost_percentage_of_revenue=ai_cost_percentage,
        total_ai_cost=total_cost,
        annualized_ai_cost=annualized_ai_cost,
        cost_trend_analysis="\n".join(cost_trend),
        provider_breakdown_analysis=provider_breakdown_analysis,
        health_status=health,
        optimization_opportunities=optimization_opportunities,
    )


def calculate_ai_value(data: AIValueInput) -> AIValueResult:
    """Calculate AI value attribution.

    Attributes business value to AI capabilities across:
    - AI-enabled revenue
    - Premium pricing capture
    - Productivity multiplier
    - Retention impact
    - Expansion revenue
    - Time-to-value acceleration

    Args:
        data: Input data for AI value calculation

    Returns:
        AIValueResult with detailed value attribution

    Example:
        >>> input_data = AIValueInput(
        ...     ai_enabled_revenue=300000,
        ...     non_ai_revenue=200000,
        ...     premium_pricing_uplift=20,
        ...     time_saved_hours=1000,
        ...     employee_fully_loaded_cost=100
        ... )
        >>> result = calculate_ai_value(input_data)
        >>> print(f"Total AI value: ${result.total_ai_value:,.2f}")
        Total AI value: $400,000.00
    """
    total_revenue = data.ai_enabled_revenue + data.non_ai_revenue
    ai_revenue_percentage = (data.ai_enabled_revenue / total_revenue) * 100 if total_revenue > 0 else 0  # noqa: E501

    value_breakdown = {"ai_enabled_revenue": data.ai_enabled_revenue}
    total_value = data.ai_enabled_revenue

    # Calculate premium pricing value
    premium_pricing_value = None
    if data.premium_pricing_uplift is not None:
        # Premium pricing value = AI revenue without the premium
        baseline_revenue = data.ai_enabled_revenue / (1 + data.premium_pricing_uplift / 100)
        premium_pricing_value = data.ai_enabled_revenue - baseline_revenue
        value_breakdown["premium_pricing_value"] = premium_pricing_value
        total_value += premium_pricing_value

    # Calculate productivity value
    productivity_value = None
    if data.time_saved_hours is not None and data.employee_fully_loaded_cost is not None:
        productivity_value = data.time_saved_hours * data.employee_fully_loaded_cost
        value_breakdown["productivity_value"] = productivity_value
        total_value += productivity_value

    # Calculate retention value
    retention_value = None
    if data.ai_feature_churn_rate is not None and data.non_ai_churn_rate is not None:
        # Retention value = revenue saved from churn reduction
        churn_reduction = data.non_ai_churn_rate - data.ai_feature_churn_rate
        if churn_reduction > 0:
            # Estimate annual retention value
            retention_value = data.ai_enabled_revenue * (churn_reduction / 100)
            value_breakdown["retention_value"] = retention_value
            total_value += retention_value

    # Calculate expansion value
    expansion_value = None
    if data.ai_expansion_revenue is not None:
        expansion_value = data.ai_expansion_revenue
        value_breakdown["expansion_value"] = expansion_value
        total_value += expansion_value

    # Calculate time-to-value acceleration value
    time_to_value_acceleration = None
    if data.time_to_value_reduction_days is not None:
        # Estimate value based on faster revenue recognition
        # Assume 30 days = 1 month of revenue acceleration
        months_accelerated = data.time_to_value_reduction_days / 30
        time_to_value_acceleration = (data.ai_enabled_revenue / 12) * months_accelerated
        value_breakdown["time_to_value_acceleration"] = time_to_value_acceleration
        total_value += time_to_value_acceleration

    # Assess health based on AI revenue percentage and value diversity
    value_sources = len([v for v in value_breakdown.values() if v > 0])
    if ai_revenue_percentage > 50 and value_sources >= 3:
        health = MetricHealth.EXCELLENT
    elif ai_revenue_percentage > 30 and value_sources >= 2:
        health = MetricHealth.GOOD
    elif ai_revenue_percentage > 10:
        health = MetricHealth.WARNING
    else:
        health = MetricHealth.CRITICAL

    return AIValueResult(
        ai_enabled_revenue=data.ai_enabled_revenue,
        ai_revenue_percentage=ai_revenue_percentage,
        premium_pricing_value=premium_pricing_value,
        productivity_value=productivity_value,
        retention_value=retention_value,
        expansion_value=expansion_value,
        time_to_value_acceleration=time_to_value_acceleration,
        total_ai_value=total_value,
        value_breakdown=value_breakdown,
        health_status=health,
    )


def calculate_ai_roi(data: AIROIInput) -> AIROIResult:
    """Calculate comprehensive AI ROI.

    Formula:
        AI ROI = (AI Value - AI Costs) / AI Costs × 100

    Includes:
    - Full cost and value analysis
    - ROI calculation
    - Break-even analysis
    - Payback period
    - Recommendations

    Args:
        data: Comprehensive AI ROI input data

    Returns:
        AIROIResult with complete AI economics analysis

    Example:
        >>> cost_input = AICostInput(
        ...     total_ai_cost=50000,
        ...     ai_interactions=1000000,
        ...     active_users=5000,
        ...     total_revenue=500000,
        ...     period_months=1
        ... )
        >>> value_input = AIValueInput(
        ...     ai_enabled_revenue=300000,
        ...     non_ai_revenue=200000
        ... )
        >>> roi_input = AIROIInput(cost_data=cost_input, value_data=value_input)
        >>> result = calculate_ai_roi(roi_input)
        >>> print(f"AI ROI: {result.ai_roi:.1f}%")
        AI ROI: 500.0%
    """
    # Calculate costs and value
    cost_result = calculate_ai_costs(data.cost_data)
    value_result = calculate_ai_value(data.value_data)

    # Calculate ROI
    # Note: For recurring revenue, we annualize value for fair comparison
    annualized_value = value_result.total_ai_value * (12 / data.cost_data.period_months)
    annualized_cost = cost_result.annualized_ai_cost

    net_ai_value = annualized_value - annualized_cost
    ai_roi = (net_ai_value / annualized_cost) * 100
    ai_roi_ratio = annualized_value / annualized_cost

    # Calculate break-even and payback
    break_even_months = None
    payback_period = None

    if annualized_value > annualized_cost:
        # Calculate months to break even
        monthly_value = annualized_value / 12
        monthly_cost = annualized_cost / 12
        monthly_net = monthly_value - monthly_cost

        if monthly_net > 0:
            # Payback period in months
            payback_period = annualized_cost / monthly_net
            break_even_months = payback_period

    # Assess overall health
    if ai_roi > 200 and cost_result.health_status == MetricHealth.EXCELLENT:
        overall_health = MetricHealth.EXCELLENT
    elif ai_roi > 100 and cost_result.health_status in [MetricHealth.EXCELLENT, MetricHealth.GOOD]:
        overall_health = MetricHealth.GOOD
    elif ai_roi > 0:
        overall_health = MetricHealth.WARNING
    else:
        overall_health = MetricHealth.CRITICAL

    # Generate recommendations
    recommendations = _generate_roi_recommendations(
        ai_roi, cost_result, value_result, break_even_months
    )

    return AIROIResult(
        ai_roi=ai_roi,
        ai_roi_ratio=ai_roi_ratio,
        net_ai_value=net_ai_value,
        break_even_months=break_even_months,
        payback_period=payback_period,
        cost_result=cost_result,
        value_result=value_result,
        overall_health=overall_health,
        recommendations=recommendations,
        roi_by_feature=None,  # Future enhancement
    )


def _generate_cost_optimizations(
    cost_per_interaction: float,
    ai_cost_percentage: float,
    provider_breakdown: Optional[dict],
) -> list[str]:
    """Generate cost optimization opportunities.

    Args:
        cost_per_interaction: Cost per AI interaction
        ai_cost_percentage: AI costs as percentage of revenue
        provider_breakdown: Provider cost breakdown if available

    Returns:
        List of optimization opportunities
    """
    optimizations = []

    # Cost per interaction optimizations
    if cost_per_interaction > 0.10:
        optimizations.append(
            "High cost per interaction (>$0.10): Implement aggressive caching strategy for repeated queries."  # noqa: E501
        )
        optimizations.append(
            "Optimize prompts to reduce token usage - remove unnecessary context, use more concise instructions."  # noqa: E501
        )

    if cost_per_interaction > 0.05:
        optimizations.append(
            "Consider prompt compression techniques and semantic caching to reduce API calls."
        )

    # AI cost percentage optimizations
    if ai_cost_percentage > 15:
        optimizations.append(
            "AI costs exceed 15% of revenue: Evaluate model selection - consider switching to more cost-efficient models for non-critical use cases."  # noqa: E501
        )
        optimizations.append(
            "Implement tiered AI features: basic (cheaper models) vs. premium (advanced models)."
        )

    if ai_cost_percentage > 10:
        optimizations.append(
            "Consider implementing usage-based pricing to pass AI costs to customers proportionally."  # noqa: E501
        )

    # Provider-specific optimizations
    if provider_breakdown and len(provider_breakdown) > 1:
        optimizations.append(
            "Multi-provider setup: Optimize routing logic to use most cost-effective provider for each use case."  # noqa: E501
        )

    # General optimizations
    optimizations.append(
        "Implement response caching with TTL to reduce duplicate API calls for similar queries."
    )
    optimizations.append(
        "Use streaming responses where possible to reduce latency and improve perceived performance."  # noqa: E501
    )
    optimizations.append(
        "Monitor and set rate limits per user to prevent abuse and control costs."
    )
    optimizations.append(
        "Batch API calls where feasible to reduce overhead and potentially negotiate better rates."
    )

    if ai_cost_percentage < 5:
        optimizations.append(
            "AI costs are well-controlled (<5% of revenue). Focus on maximizing value rather than aggressive cost cutting."  # noqa: E501
        )

    return optimizations


def _generate_roi_recommendations(
    ai_roi: float,
    cost_result: AICostResult,
    value_result: AIValueResult,
    break_even_months: Optional[float],
) -> list[str]:
    """Generate actionable recommendations based on AI ROI analysis.

    Args:
        ai_roi: AI ROI percentage
        cost_result: AI cost analysis result
        value_result: AI value attribution result
        break_even_months: Months to break even

    Returns:
        List of actionable recommendations
    """
    recommendations = []

    # ROI-based recommendations
    if ai_roi > 200:
        recommendations.append(
            "Excellent AI ROI (>200%): Strong business case. Consider expanding AI features and increasing investment."  # noqa: E501
        )
        recommendations.append(
            "Document AI value attribution methodology for CFO and board presentations."
        )
    elif ai_roi > 100:
        recommendations.append(
            "Positive AI ROI (>100%): Good return on investment. Continue current strategy with optimizations."  # noqa: E501
        )
        recommendations.append(
            f"Break-even in {break_even_months:.1f} months - healthy payback period." if break_even_months else ""  # noqa: E501
        )
    elif ai_roi > 0:
        recommendations.append(
            "Marginal AI ROI: Need to improve either value capture or cost efficiency to justify continued investment."  # noqa: E501
        )
        recommendations.append(
            "Focus on increasing AI-enabled revenue and reducing churn before expanding AI features."  # noqa: E501
        )
    else:
        recommendations.append(
            "CRITICAL: Negative AI ROI. Urgently review AI strategy - current approach is not sustainable."  # noqa: E501
        )
        recommendations.append(
            "Consider: reducing AI feature scope, increasing pricing, or improving cost efficiency."
        )

    # Value attribution recommendations
    value_sources = len([v for v in value_result.value_breakdown.values() if v > 0])
    if value_sources == 1:
        recommendations.append(
            "Single value source: Diversify AI value attribution. Track productivity, retention, and expansion impact."  # noqa: E501
        )

    if value_result.ai_revenue_percentage < 20:
        recommendations.append(
            f"Low AI revenue contribution ({value_result.ai_revenue_percentage:.1f}%): Increase AI feature adoption or develop new AI capabilities."  # noqa: E501
        )

    # Cost-specific recommendations
    if cost_result.health_status in [MetricHealth.WARNING, MetricHealth.CRITICAL]:
        recommendations.append(
            "High AI costs: Implement cost optimization strategies from the cost analysis section."
        )

    # Break-even recommendations
    if break_even_months and break_even_months > 12:
        recommendations.append(
            f"Long payback period ({break_even_months:.1f} months): Accelerate value capture through pricing optimization or feature expansion."  # noqa: E501
        )
    elif break_even_months and break_even_months < 6:
        recommendations.append(
            "Fast payback period: Excellent. Use this as evidence to justify additional AI investments."  # noqa: E501
        )

    # Strategic recommendations
    recommendations.append(
        "Track AI ROI monthly and set quarterly OKRs for improvement through value increase or cost reduction."  # noqa: E501
    )
    recommendations.append(
        "Implement A/B testing to measure incremental value of AI features vs. non-AI alternatives."
    )
    recommendations.append(
        "Create AI economics dashboard for real-time monitoring of costs, value, and ROI trends."
    )

    return [r for r in recommendations if r]  # Filter empty strings


def format_result_as_json(result: AIROIResult) -> str:
    """Format AI ROI result as JSON.

    Args:
        result: AI ROI calculation result

    Returns:
        JSON string representation
    """
    output = {
        "ai_roi_summary": {
            "ai_roi_percentage": round(result.ai_roi, 2),
            "ai_roi_ratio": round(result.ai_roi_ratio, 2),
            "net_ai_value_annual": round(result.net_ai_value, 2),
            "break_even_months": round(result.break_even_months, 1) if result.break_even_months else None,  # noqa: E501
            "payback_period_months": round(result.payback_period, 1) if result.payback_period else None,  # noqa: E501
            "overall_health": result.overall_health.value,
        },
        "ai_costs": {
            "cost_per_interaction": round(result.cost_result.cost_per_interaction, 4),
            "cost_per_user_per_month": round(result.cost_result.cost_per_user_per_month, 2),
            "ai_cost_percentage_of_revenue": round(result.cost_result.ai_cost_percentage_of_revenue, 2),  # noqa: E501
            "total_ai_cost": round(result.cost_result.total_ai_cost, 2),
            "annualized_ai_cost": round(result.cost_result.annualized_ai_cost, 2),
            "health_status": result.cost_result.health_status.value,
            "provider_breakdown": result.cost_result.provider_breakdown_analysis,
            "optimization_opportunities": result.cost_result.optimization_opportunities,
        },
        "ai_value": {
            "ai_enabled_revenue": round(result.value_result.ai_enabled_revenue, 2),
            "ai_revenue_percentage": round(result.value_result.ai_revenue_percentage, 2),
            "total_ai_value": round(result.value_result.total_ai_value, 2),
            "value_breakdown": {
                k: round(v, 2) for k, v in result.value_result.value_breakdown.items()
            },
            "premium_pricing_value": (
                round(result.value_result.premium_pricing_value, 2)
                if result.value_result.premium_pricing_value
                else None
            ),
            "productivity_value": (
                round(result.value_result.productivity_value, 2)
                if result.value_result.productivity_value
                else None
            ),
            "retention_value": (
                round(result.value_result.retention_value, 2)
                if result.value_result.retention_value
                else None
            ),
            "expansion_value": (
                round(result.value_result.expansion_value, 2)
                if result.value_result.expansion_value
                else None
            ),
            "health_status": result.value_result.health_status.value,
        },
        "recommendations": result.recommendations,
    }

    return json.dumps(output, indent=2)


def format_result_as_markdown(result: AIROIResult) -> str:
    """Format AI ROI result as CFO-ready Markdown report.

    Args:
        result: AI ROI calculation result

    Returns:
        Markdown string representation
    """
    lines = []

    lines.append("# AI Economics Analysis")
    lines.append("")
    lines.append(f"**Overall Health:** {result.overall_health.value.upper()}")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **AI ROI:** {result.ai_roi:.1f}% ({result.ai_roi_ratio:.2f}x return)")
    lines.append(f"- **Net Annual Value:** ${result.net_ai_value:,.2f}")
    if result.break_even_months:
        lines.append(f"- **Break-Even Period:** {result.break_even_months:.1f} months")
    lines.append(
        f"- **AI Cost as % of Revenue:** {result.cost_result.ai_cost_percentage_of_revenue:.1f}%"
    )
    lines.append(
        f"- **AI-Enabled Revenue:** ${result.value_result.ai_enabled_revenue:,.2f} ({result.value_result.ai_revenue_percentage:.1f}% of total)"  # noqa: E501
    )
    lines.append("")

    # AI Cost Analysis
    lines.append("## AI Cost Analysis")
    lines.append("")
    lines.append(f"**Health Status:** {result.cost_result.health_status.value.upper()}")
    lines.append("")
    lines.append(f"- **Total Annual AI Cost:** ${result.cost_result.annualized_ai_cost:,.2f}")
    lines.append(f"- **Cost per Interaction:** ${result.cost_result.cost_per_interaction:.4f}")
    lines.append(
        f"- **Cost per User per Month:** ${result.cost_result.cost_per_user_per_month:.2f}"
    )
    lines.append(
        f"- **AI Cost % of Revenue:** {result.cost_result.ai_cost_percentage_of_revenue:.2f}%"
    )
    lines.append("")

    # Provider Breakdown
    if result.cost_result.provider_breakdown_analysis:
        lines.append("### Provider Cost Breakdown")
        lines.append("")
        for provider, metrics in result.cost_result.provider_breakdown_analysis.items():
            lines.append(f"- **{provider}:**")
            lines.append(f"  - Cost: ${metrics['cost']:,.2f} ({metrics['percentage']:.1f}% of total)")  # noqa: E501
            lines.append(f"  - Cost per interaction: ${metrics['cost_per_interaction']:.4f}")
        lines.append("")

    # Cost Optimization Opportunities
    lines.append("### Cost Optimization Opportunities")
    lines.append("")
    for i, opp in enumerate(result.cost_result.optimization_opportunities, 1):
        lines.append(f"{i}. {opp}")
    lines.append("")

    # AI Value Attribution
    lines.append("## AI Value Attribution")
    lines.append("")
    lines.append(f"**Health Status:** {result.value_result.health_status.value.upper()}")
    lines.append("")
    lines.append(f"- **Total AI Value (Annual):** ${result.value_result.total_ai_value:,.2f}")
    lines.append(
        f"- **AI-Enabled Revenue:** ${result.value_result.ai_enabled_revenue:,.2f}"
    )
    lines.append(
        f"- **AI Revenue %:** {result.value_result.ai_revenue_percentage:.1f}% of total revenue"
    )
    lines.append("")

    # Value Breakdown
    lines.append("### Value Sources")
    lines.append("")
    for source, value in result.value_result.value_breakdown.items():
        percentage = (value / result.value_result.total_ai_value) * 100
        source_name = source.replace("_", " ").title()
        lines.append(f"- **{source_name}:** ${value:,.2f} ({percentage:.1f}% of total)")
    lines.append("")

    if result.value_result.productivity_value:
        lines.append(
            f"**Productivity Multiplier:** ${result.value_result.productivity_value:,.2f} in time savings value"  # noqa: E501
        )
        lines.append("")

    if result.value_result.retention_value:
        lines.append(
            f"**Retention Impact:** ${result.value_result.retention_value:,.2f} in churn reduction value"  # noqa: E501
        )
        lines.append("")

    # ROI Calculation
    lines.append("## ROI Framework")
    lines.append("")
    lines.append("```")
    lines.append(f"AI Value (Annual):     ${result.value_result.total_ai_value:>15,.2f}")
    lines.append(f"AI Costs (Annual):   - ${result.cost_result.annualized_ai_cost:>15,.2f}")
    lines.append(f"                       {'=' * 30}")
    lines.append(f"Net AI Value:          ${result.net_ai_value:>15,.2f}")
    lines.append("")
    lines.append("AI ROI = (Value - Cost) / Cost × 100")
    lines.append(f"AI ROI = {result.ai_roi:.1f}%")
    lines.append(f"Return Ratio = {result.ai_roi_ratio:.2f}x")
    lines.append("```")
    lines.append("")

    # Break-Even Analysis
    if result.break_even_months:
        lines.append("## Break-Even Analysis")
        lines.append("")
        lines.append(f"- **Break-Even Period:** {result.break_even_months:.1f} months")
        lines.append(
            f"- **Monthly Net Value:** ${result.net_ai_value / 12:,.2f}"
        )
        lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")
    for i, rec in enumerate(result.recommendations, 1):
        lines.append(f"{i}. {rec}")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("*AI Economics Analysis - Product Finance Plugin*")
    lines.append(
        "*Based on industry-standard AI cost tracking and value attribution frameworks*"
    )
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    """CLI entry point for AI ROI calculator.

    Reads input from stdin (JSON) or prompts interactively,
    calculates AI ROI, and outputs CFO-ready results.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="AI ROI Calculator for AI Economics Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python ai_roi_calculator.py

  # JSON input from stdin
  echo '{"cost_data": {...}, "value_data": {...}}' | python ai_roi_calculator.py

  # JSON file input
  python ai_roi_calculator.py < ai_economics_input.json

  # Output formats
  python ai_roi_calculator.py --format json
  python ai_roi_calculator.py --format markdown
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
        try:
            if args.input is not None:
                input_data = json.loads(args.input.read_text(encoding="utf-8"))
            else:
                input_data = json.load(sys.stdin)
            data = AIROIInput(**input_data)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: Invalid input data: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Interactive mode
        print("AI ROI Calculator")
        print("=" * 50)
        print()
        print("AI COST DATA")
        print("-" * 50)

        try:
            total_ai_cost = float(input("Total AI costs ($): "))
            ai_interactions = int(input("Total AI interactions/API calls: "))
            active_users = int(input("Number of active users: "))
            total_revenue = float(input("Total revenue ($): "))
            period_months_input = input("Period in months (default 1): ").strip()
            period_months = int(period_months_input) if period_months_input else 1

            cost_data = AICostInput(
                total_ai_cost=total_ai_cost,
                ai_interactions=ai_interactions,
                active_users=active_users,
                total_revenue=total_revenue,
                period_months=period_months,
            )

            print()
            print("AI VALUE DATA")
            print("-" * 50)

            ai_enabled_revenue = float(input("AI-enabled revenue ($): "))
            non_ai_revenue = float(input("Non-AI revenue ($): "))

            # Optional value attribution
            print()
            print("Optional: Additional value attribution (press Enter to skip)")
            print()

            premium_uplift_input = input("Premium pricing uplift for AI (%): ").strip()
            premium_pricing_uplift = float(premium_uplift_input) if premium_uplift_input else None

            time_saved_input = input("Time saved through AI (hours): ").strip()
            time_saved_hours = float(time_saved_input) if time_saved_input else None

            employee_cost_input = None
            if time_saved_hours:
                employee_cost_input = input("Fully-loaded employee cost per hour ($): ").strip()
            employee_fully_loaded_cost = (
                float(employee_cost_input) if employee_cost_input else None
            )

            ai_churn_input = input("Churn rate with AI features (%): ").strip()
            ai_feature_churn_rate = float(ai_churn_input) if ai_churn_input else None

            non_ai_churn_input = None
            if ai_feature_churn_rate is not None:
                non_ai_churn_input = input("Churn rate without AI features (%): ").strip()
            non_ai_churn_rate = float(non_ai_churn_input) if non_ai_churn_input else None

            expansion_input = input("Expansion revenue from AI ($): ").strip()
            ai_expansion_revenue = float(expansion_input) if expansion_input else None

            ttv_input = input("Time-to-value reduction (days): ").strip()
            time_to_value_reduction_days = float(ttv_input) if ttv_input else None

            value_data = AIValueInput(
                ai_enabled_revenue=ai_enabled_revenue,
                non_ai_revenue=non_ai_revenue,
                premium_pricing_uplift=premium_pricing_uplift,
                time_saved_hours=time_saved_hours,
                employee_fully_loaded_cost=employee_fully_loaded_cost,
                ai_feature_churn_rate=ai_feature_churn_rate,
                non_ai_churn_rate=non_ai_churn_rate,
                ai_expansion_revenue=ai_expansion_revenue,
                time_to_value_reduction_days=time_to_value_reduction_days,
            )

            data = AIROIInput(cost_data=cost_data, value_data=value_data)

        except KeyboardInterrupt:
            print("\n\nCancelled by user.")
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)

    # Calculate AI ROI
    try:
        result = calculate_ai_roi(data)
    except Exception as e:
        print(f"Error calculating AI ROI: {e}", file=sys.stderr)
        sys.exit(1)

    # Output results
    print()
    if args.format == "json":
        print(format_result_as_json(result))
    else:
        print(format_result_as_markdown(result))


if __name__ == "__main__":
    main()
