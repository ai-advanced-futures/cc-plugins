"""Common calculation utilities for financial analysis.

This module provides reusable calculation helpers for:
- Percentage calculations
- Growth rate calculations
- Ratio calculations
- Annualization helpers
- Period conversion utilities

These utilities are used across all financial calculation scripts to ensure
consistent methodology and reduce code duplication.

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, Optional, Union


def safe_divide(numerator: float, denominator: float) -> Optional[float]:
    """
    Divide numerator by denominator, returning None if denominator is zero.

    Use this instead of bare division in all financial formula functions
    to prevent ZeroDivisionError on edge-case inputs.

    Args:
        numerator: The dividend.
        denominator: The divisor. Returns None if this is 0.

    Returns:
        float result, or None if denominator is 0.

    Examples:
        safe_divide(10, 2)  -> 5.0
        safe_divide(10, 0)  -> None
        safe_divide(0, 5)   -> 0.0
    """
    if denominator == 0:
        return None
    return numerator / denominator


def calculate_percentage(
    numerator: Union[int, float, Decimal],
    denominator: Union[int, float, Decimal],
    decimal_places: int = 2,
) -> float:
    """Calculate percentage: (numerator / denominator) × 100.

    Args:
        numerator: Numerator value
        denominator: Denominator value
        decimal_places: Number of decimal places to round to

    Returns:
        Percentage value rounded to specified decimal places

    Raises:
        ValueError: If denominator is zero

    Example:
        >>> calculate_percentage(25, 100)
        25.0
        >>> calculate_percentage(1, 3)
        33.33
        >>> calculate_percentage(50, 0)
        Traceback (most recent call last):
        ValueError: Cannot calculate percentage with zero denominator
    """
    if denominator == 0:
        raise ValueError("Cannot calculate percentage with zero denominator")

    percentage = (numerator / denominator) * 100
    return round(percentage, decimal_places)


def calculate_percentage_change(
    old_value: Union[int, float, Decimal],
    new_value: Union[int, float, Decimal],
    decimal_places: int = 2,
) -> float:
    """Calculate percentage change between two values.

    Formula: ((new_value - old_value) / old_value) × 100

    Args:
        old_value: Original value
        new_value: New value
        decimal_places: Number of decimal places to round to

    Returns:
        Percentage change

    Raises:
        ValueError: If old_value is zero

    Example:
        >>> calculate_percentage_change(100, 150)
        50.0
        >>> calculate_percentage_change(100, 50)
        -50.0
        >>> calculate_percentage_change(0, 100)
        Traceback (most recent call last):
        ValueError: Cannot calculate percentage change from zero
    """
    if old_value == 0:
        raise ValueError("Cannot calculate percentage change from zero")

    change = ((new_value - old_value) / old_value) * 100
    return round(change, decimal_places)


def calculate_growth_rate(
    initial_value: Union[int, float, Decimal],
    final_value: Union[int, float, Decimal],
    periods: int = 1,
    decimal_places: int = 2,
) -> float:
    """Calculate growth rate between two values over a period.

    For single period: ((final - initial) / initial) × 100
    For multiple periods: CAGR formula

    Args:
        initial_value: Starting value
        final_value: Ending value
        periods: Number of periods (default: 1)
        decimal_places: Number of decimal places to round to

    Returns:
        Growth rate as percentage

    Raises:
        ValueError: If initial_value is zero or negative

    Example:
        >>> calculate_growth_rate(100, 150)
        50.0
        >>> calculate_growth_rate(100, 200, periods=2)
        41.42
    """
    if initial_value <= 0:
        raise ValueError("Initial value must be positive for growth rate calculation")

    if periods == 1:
        # Simple growth rate
        return calculate_percentage_change(initial_value, final_value, decimal_places)
    else:
        # Compound Annual Growth Rate (CAGR)
        cagr = (pow(final_value / initial_value, 1 / periods) - 1) * 100
        return round(cagr, decimal_places)


def calculate_compound_growth(
    initial_value: Union[int, float, Decimal],
    growth_rate_percent: float,
    periods: int,
    decimal_places: int = 2,
) -> float:
    """Calculate final value after compound growth.

    Formula: initial_value × (1 + growth_rate)^periods

    Args:
        initial_value: Starting value
        growth_rate_percent: Growth rate as percentage per period
        periods: Number of periods
        decimal_places: Number of decimal places to round to

    Returns:
        Final value after compound growth

    Example:
        >>> calculate_compound_growth(1000, 10, 3)
        1331.0
        >>> calculate_compound_growth(1000, -5, 2)
        902.5
    """
    growth_rate_decimal = growth_rate_percent / 100
    final_value = initial_value * pow(1 + growth_rate_decimal, periods)
    return round(final_value, decimal_places)


def calculate_ratio(
    numerator: Union[int, float, Decimal],
    denominator: Union[int, float, Decimal],
    decimal_places: int = 2,
    format_as_string: bool = False,
) -> Union[float, str]:
    """Calculate ratio between two values.

    Args:
        numerator: Numerator value
        denominator: Denominator value
        decimal_places: Number of decimal places to round to
        format_as_string: If True, return as "X:1" format

    Returns:
        Ratio as float or formatted string

    Raises:
        ValueError: If denominator is zero

    Example:
        >>> calculate_ratio(4000, 1000)
        4.0
        >>> calculate_ratio(4000, 1000, format_as_string=True)
        '4.00:1'
        >>> calculate_ratio(3000, 1000)
        3.0
    """
    if denominator == 0:
        raise ValueError("Cannot calculate ratio with zero denominator")

    ratio = numerator / denominator
    ratio_rounded = round(ratio, decimal_places)

    if format_as_string:
        return f"{ratio_rounded:.{decimal_places}f}:1"
    return ratio_rounded


def calculate_margin(
    revenue: Union[int, float, Decimal],
    costs: Union[int, float, Decimal],
    decimal_places: int = 2,
) -> float:
    """Calculate margin percentage.

    Formula: ((revenue - costs) / revenue) × 100

    Args:
        revenue: Total revenue
        costs: Total costs
        decimal_places: Number of decimal places to round to

    Returns:
        Margin as percentage

    Raises:
        ValueError: If revenue is zero

    Example:
        >>> calculate_margin(1000, 300)
        70.0
        >>> calculate_margin(1000, 1200)
        -20.0
    """
    if revenue == 0:
        raise ValueError("Cannot calculate margin with zero revenue")

    margin = ((revenue - costs) / revenue) * 100
    return round(margin, decimal_places)


def calculate_gross_margin(
    revenue: Union[int, float, Decimal],
    cogs: Union[int, float, Decimal],
    decimal_places: int = 2,
) -> float:
    """Calculate gross margin percentage.

    Formula: ((revenue - COGS) / revenue) × 100

    Args:
        revenue: Total revenue
        cogs: Cost of Goods Sold
        decimal_places: Number of decimal places to round to

    Returns:
        Gross margin as percentage

    Example:
        >>> calculate_gross_margin(1000, 200)
        80.0
    """
    return calculate_margin(revenue, cogs, decimal_places)


def annualize_value(
    value: Union[int, float, Decimal],
    period_months: int,
    decimal_places: int = 2,
) -> float:
    """Annualize a value from a shorter period.

    Formula: value × (12 / period_months)

    Args:
        value: Value to annualize
        period_months: Number of months in the period
        decimal_places: Number of decimal places to round to

    Returns:
        Annualized value

    Raises:
        ValueError: If period_months is zero or negative

    Example:
        >>> annualize_value(1000, 1)
        12000.0
        >>> annualize_value(3000, 3)
        12000.0
        >>> annualize_value(6000, 6)
        12000.0
    """
    if period_months <= 0:
        raise ValueError("Period must be positive")

    annualized = value * (12 / period_months)
    return round(annualized, decimal_places)


def calculate_monthly_from_annual(
    annual_value: Union[int, float, Decimal],
    decimal_places: int = 2,
) -> float:
    """Calculate monthly value from annual value.

    Formula: annual_value / 12

    Args:
        annual_value: Annual value
        decimal_places: Number of decimal places to round to

    Returns:
        Monthly value

    Example:
        >>> calculate_monthly_from_annual(12000)
        1000.0
        >>> calculate_monthly_from_annual(15000)
        1250.0
    """
    monthly = annual_value / 12
    return round(monthly, decimal_places)


def calculate_arr_from_mrr(
    mrr: Union[int, float, Decimal],
    decimal_places: int = 2,
) -> float:
    """Calculate Annual Recurring Revenue from Monthly Recurring Revenue.

    Formula: MRR × 12

    Args:
        mrr: Monthly Recurring Revenue
        decimal_places: Number of decimal places to round to

    Returns:
        Annual Recurring Revenue

    Example:
        >>> calculate_arr_from_mrr(10000)
        120000.0
    """
    return annualize_value(mrr, 1, decimal_places)


def calculate_mrr_from_arr(
    arr: Union[int, float, Decimal],
    decimal_places: int = 2,
) -> float:
    """Calculate Monthly Recurring Revenue from Annual Recurring Revenue.

    Formula: ARR / 12

    Args:
        arr: Annual Recurring Revenue
        decimal_places: Number of decimal places to round to

    Returns:
        Monthly Recurring Revenue

    Example:
        >>> calculate_mrr_from_arr(120000)
        10000.0
    """
    return calculate_monthly_from_annual(arr, decimal_places)


def convert_period(
    value: Union[int, float, Decimal],
    from_period_months: int,
    to_period_months: int,
    decimal_places: int = 2,
) -> float:
    """Convert a value from one period to another.

    Args:
        value: Value in original period
        from_period_months: Original period in months
        to_period_months: Target period in months
        decimal_places: Number of decimal places to round to

    Returns:
        Value converted to target period

    Example:
        >>> convert_period(1000, 1, 12)
        12000.0
        >>> convert_period(12000, 12, 1)
        1000.0
        >>> convert_period(3000, 3, 1)
        1000.0
    """
    if from_period_months <= 0 or to_period_months <= 0:
        raise ValueError("Periods must be positive")

    # Convert to monthly rate first, then to target period
    monthly_rate = value / from_period_months
    target_value = monthly_rate * to_period_months
    return round(target_value, decimal_places)


def calculate_average(
    values: list[Union[int, float, Decimal]],
    decimal_places: int = 2,
) -> float:
    """Calculate arithmetic average of a list of values.

    Args:
        values: List of values
        decimal_places: Number of decimal places to round to

    Returns:
        Average value

    Raises:
        ValueError: If values list is empty

    Example:
        >>> calculate_average([100, 200, 300])
        200.0
        >>> calculate_average([10, 20, 30, 40, 50])
        30.0
    """
    if not values:
        raise ValueError("Cannot calculate average of empty list")

    avg = sum(values) / len(values)
    return round(avg, decimal_places)


def calculate_weighted_average(
    values: list[Union[int, float, Decimal]],
    weights: list[Union[int, float, Decimal]],
    decimal_places: int = 2,
) -> float:
    """Calculate weighted average of values.

    Args:
        values: List of values
        weights: List of weights (must be same length as values)
        decimal_places: Number of decimal places to round to

    Returns:
        Weighted average

    Raises:
        ValueError: If lists are different lengths or empty

    Example:
        >>> calculate_weighted_average([100, 200], [1, 2])
        166.67
        >>> calculate_weighted_average([80, 90, 100], [0.2, 0.3, 0.5])
        92.0
    """
    if not values or not weights:
        raise ValueError("Cannot calculate weighted average of empty lists")

    if len(values) != len(weights):
        raise ValueError("Values and weights must be same length")

    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("Total weight cannot be zero")

    weighted_sum = sum(v * w for v, w in zip(values, weights))
    weighted_avg = weighted_sum / total_weight
    return round(weighted_avg, decimal_places)


def calculate_payback_period(
    investment: Union[int, float, Decimal],
    periodic_return: Union[int, float, Decimal],
    decimal_places: int = 2,
) -> float:
    """Calculate payback period in number of periods.

    Formula: investment / periodic_return

    Args:
        investment: Initial investment amount
        periodic_return: Return per period
        decimal_places: Number of decimal places to round to

    Returns:
        Number of periods to payback

    Raises:
        ValueError: If periodic_return is zero or negative

    Example:
        >>> calculate_payback_period(12000, 1000)
        12.0
        >>> calculate_payback_period(5000, 500)
        10.0
    """
    if periodic_return <= 0:
        raise ValueError("Periodic return must be positive")

    payback = investment / periodic_return
    return round(payback, decimal_places)


def calculate_cac(
    sales_costs: Union[int, float, Decimal],
    marketing_costs: Union[int, float, Decimal],
    new_customers: int,
    decimal_places: int = 2,
) -> float:
    """Calculate Customer Acquisition Cost.

    Formula: (sales_costs + marketing_costs) / new_customers

    Args:
        sales_costs: Total sales costs
        marketing_costs: Total marketing costs
        new_customers: Number of new customers acquired
        decimal_places: Number of decimal places to round to

    Returns:
        Customer Acquisition Cost

    Raises:
        ValueError: If new_customers is zero

    Example:
        >>> calculate_cac(500000, 300000, 100)
        8000.0
    """
    if new_customers <= 0:
        raise ValueError("Number of new customers must be positive")

    cac = (sales_costs + marketing_costs) / new_customers
    return round(cac, decimal_places)


def calculate_ltv(
    arpu: Union[int, float, Decimal],
    gross_margin_percent: float,
    churn_rate_percent: float,
    decimal_places: int = 2,
) -> float:
    """Calculate Customer Lifetime Value.

    Formula: ARPU × (Gross Margin % / 100) / (Churn Rate % / 100)

    Args:
        arpu: Average Revenue Per User per period
        gross_margin_percent: Gross margin as percentage
        churn_rate_percent: Churn rate as percentage per period
        decimal_places: Number of decimal places to round to

    Returns:
        Customer Lifetime Value

    Raises:
        ValueError: If churn_rate_percent is zero

    Example:
        >>> calculate_ltv(100, 80, 2)
        4000.0
        >>> calculate_ltv(50, 70, 5)
        700.0
    """
    if churn_rate_percent <= 0:
        raise ValueError("Churn rate must be positive")

    gross_margin_decimal = gross_margin_percent / 100
    churn_rate_decimal = churn_rate_percent / 100

    ltv = arpu * gross_margin_decimal / churn_rate_decimal
    return round(ltv, decimal_places)


def calculate_customer_lifetime(
    churn_rate_percent: float,
    period_name: str = "months",
    decimal_places: int = 1,
) -> float:
    """Calculate average customer lifetime from churn rate.

    Formula: 1 / (churn_rate_percent / 100)

    Args:
        churn_rate_percent: Churn rate as percentage per period
        period_name: Name of period (for documentation only)
        decimal_places: Number of decimal places to round to

    Returns:
        Average customer lifetime in periods

    Raises:
        ValueError: If churn_rate_percent is zero

    Example:
        >>> calculate_customer_lifetime(2.0)
        50.0
        >>> calculate_customer_lifetime(5.0)
        20.0
    """
    if churn_rate_percent <= 0:
        raise ValueError("Churn rate must be positive")

    churn_rate_decimal = churn_rate_percent / 100
    lifetime = 1 / churn_rate_decimal
    return round(lifetime, decimal_places)


def calculate_rule_of_40(
    growth_rate_percent: float,
    ebitda_margin_percent: float,
    decimal_places: int = 1,
) -> float:
    """Calculate Rule of 40 score.

    Formula: Growth Rate % + EBITDA Margin %

    Args:
        growth_rate_percent: Revenue growth rate as percentage
        ebitda_margin_percent: EBITDA margin as percentage
        decimal_places: Number of decimal places to round to

    Returns:
        Rule of 40 score

    Example:
        >>> calculate_rule_of_40(50, -5)
        45.0
        >>> calculate_rule_of_40(30, 15)
        45.0
    """
    score = growth_rate_percent + ebitda_margin_percent
    return round(score, decimal_places)


def calculate_burn_rate(
    starting_cash: Union[int, float, Decimal],
    ending_cash: Union[int, float, Decimal],
    period_months: int,
    decimal_places: int = 2,
) -> float:
    """Calculate monthly burn rate.

    Formula: (starting_cash - ending_cash) / period_months

    Args:
        starting_cash: Cash at start of period
        ending_cash: Cash at end of period
        period_months: Number of months in period
        decimal_places: Number of decimal places to round to

    Returns:
        Monthly burn rate (positive number indicates burn)

    Example:
        >>> calculate_burn_rate(1000000, 700000, 3)
        100000.0
        >>> calculate_burn_rate(500000, 800000, 1)
        -300000.0
    """
    if period_months <= 0:
        raise ValueError("Period must be positive")

    burn = (starting_cash - ending_cash) / period_months
    return round(burn, decimal_places)


def calculate_runway_months(
    current_cash: Union[int, float, Decimal],
    monthly_burn: Union[int, float, Decimal],
    decimal_places: int = 1,
) -> float:
    """Calculate runway in months.

    Formula: current_cash / monthly_burn

    Args:
        current_cash: Current cash balance
        monthly_burn: Monthly burn rate (positive number)
        decimal_places: Number of decimal places to round to

    Returns:
        Runway in months

    Raises:
        ValueError: If monthly_burn is zero or negative

    Example:
        >>> calculate_runway_months(1000000, 100000)
        10.0
        >>> calculate_runway_months(500000, 50000)
        10.0
    """
    if monthly_burn <= 0:
        raise ValueError("Monthly burn must be positive")

    runway = current_cash / monthly_burn
    return round(runway, decimal_places)


def calculate_roi(
    gain: Union[int, float, Decimal],
    cost: Union[int, float, Decimal],
    decimal_places: int = 2,
) -> float:
    """Calculate Return on Investment as percentage.

    Formula: ((gain - cost) / cost) × 100

    Args:
        gain: Total gain/return from investment
        cost: Cost of investment
        decimal_places: Number of decimal places to round to

    Returns:
        ROI as percentage

    Raises:
        ValueError: If cost is zero

    Example:
        >>> calculate_roi(15000, 10000)
        50.0
        >>> calculate_roi(8000, 10000)
        -20.0
    """
    if cost <= 0:
        raise ValueError("Cost must be positive")

    roi = ((gain - cost) / cost) * 100
    return round(roi, decimal_places)


def calculate_net_revenue_retention(
    starting_arr: Union[int, float, Decimal],
    expansion_arr: Union[int, float, Decimal],
    contraction_arr: Union[int, float, Decimal],
    churned_arr: Union[int, float, Decimal],
    decimal_places: int = 2,
) -> float:
    """Calculate Net Revenue Retention (NRR) percentage.

    Formula: ((Starting ARR + Expansion - Contraction - Churn) / Starting ARR) × 100

    Args:
        starting_arr: ARR at start of period
        expansion_arr: ARR gained from expansions
        contraction_arr: ARR lost from contractions
        churned_arr: ARR lost from churn
        decimal_places: Number of decimal places to round to

    Returns:
        Net Revenue Retention as percentage

    Raises:
        ValueError: If starting_arr is zero

    Example:
        >>> calculate_net_revenue_retention(1000000, 150000, 50000, 100000)
        100.0
        >>> calculate_net_revenue_retention(1000000, 200000, 30000, 50000)
        112.0
    """
    if starting_arr <= 0:
        raise ValueError("Starting ARR must be positive")

    ending_arr = starting_arr + expansion_arr - contraction_arr - churned_arr
    nrr = (ending_arr / starting_arr) * 100
    return round(nrr, decimal_places)


def prorate_value(
    annual_value: Union[int, float, Decimal],
    days: int,
    days_in_year: int = 365,
    decimal_places: int = 2,
) -> float:
    """Prorate an annual value for a specific number of days.

    Formula: annual_value × (days / days_in_year)

    Args:
        annual_value: Annual value to prorate
        days: Number of days to prorate for
        days_in_year: Days in year (default: 365)
        decimal_places: Number of decimal places to round to

    Returns:
        Prorated value

    Example:
        >>> prorate_value(12000, 30)
        986.3
        >>> prorate_value(12000, 365)
        12000.0
    """
    if days_in_year <= 0:
        raise ValueError("Days in year must be positive")

    prorated = annual_value * (days / days_in_year)
    return round(prorated, decimal_places)


def calculate_channel_economics(
    cac: float,
    arpu: float,
    gross_margin: float,
    monthly_churn_rate: float,
) -> Dict[str, Optional[float]]:
    """
    Calculate standard channel unit economics (LTV, LTV:CAC, payback).

    Use this function from all channel-specific methods — do not re-implement.

    Args:
        cac: Customer Acquisition Cost for this channel.
        arpu: Average Revenue Per User (monthly).
        gross_margin: Gross margin as decimal (e.g., 0.75 for 75%).
        monthly_churn_rate: Monthly churn as decimal (e.g., 0.03 for 3%).

    Returns:
        dict with: ltv, ltv_cac_ratio, payback_months, monthly_gross_profit
    """
    monthly_gp = arpu * gross_margin
    ltv = safe_divide(monthly_gp, monthly_churn_rate)
    ltv_cac_ratio = safe_divide(ltv, cac) if ltv is not None else None
    payback_months = safe_divide(cac, monthly_gp)

    return {
        "ltv": round(ltv, 2) if ltv is not None else None,
        "ltv_cac_ratio": round(ltv_cac_ratio, 2) if ltv_cac_ratio is not None else None,
        "payback_months": round(payback_months, 1) if payback_months is not None else None,
        "monthly_gross_profit": round(monthly_gp, 2),
    }


def round_currency(
    value: Union[int, float, Decimal],
    decimal_places: int = 2,
) -> Decimal:
    """Round currency value using banker's rounding.

    Args:
        value: Currency value to round
        decimal_places: Number of decimal places (default: 2)

    Returns:
        Rounded Decimal value

    Example:
        >>> float(round_currency(10.555))
        10.56
        >>> float(round_currency(10.554))
        10.55
    """
    decimal_value = Decimal(str(value))
    quantize_str = f"0.{'0' * decimal_places}"
    return decimal_value.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
