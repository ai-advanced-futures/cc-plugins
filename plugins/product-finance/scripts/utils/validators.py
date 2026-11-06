"""Input validation utilities for financial calculations.

This module provides comprehensive validation functions for financial data inputs
including numeric ranges, percentages, currencies, dates/periods, and sanity checks.

These validators are used across all financial calculation scripts to ensure data
quality and prevent calculation errors.

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT
"""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from pydantic import ValidationInfo


def validate_positive_number(
    value: Union[int, float, Decimal],
    field_name: str = "value",
    allow_zero: bool = False,
) -> Union[int, float, Decimal]:
    """Validate that a number is positive.

    Args:
        value: Number to validate
        field_name: Name of field for error messages
        allow_zero: Whether to allow zero as a valid value

    Returns:
        The validated value

    Raises:
        ValueError: If value is not positive

    Example:
        >>> validate_positive_number(100, "revenue")
        100
        >>> validate_positive_number(0, "revenue", allow_zero=True)
        0
        >>> validate_positive_number(-100, "revenue")
        Traceback (most recent call last):
        ValueError: revenue must be positive (got -100)
    """
    if allow_zero:
        if value < 0:
            raise ValueError(f"{field_name} must be non-negative (got {value})")
    else:
        if value <= 0:
            raise ValueError(f"{field_name} must be positive (got {value})")
    return value


def validate_percentage(
    value: float,
    field_name: str = "percentage",
    min_value: float = 0.0,
    max_value: float = 100.0,
    allow_negative: bool = False,
) -> float:
    """Validate percentage value.

    Args:
        value: Percentage value to validate
        field_name: Name of field for error messages
        min_value: Minimum allowed value (default: 0.0)
        max_value: Maximum allowed value (default: 100.0)
        allow_negative: Whether to allow negative percentages

    Returns:
        The validated percentage value

    Raises:
        ValueError: If percentage is out of valid range

    Example:
        >>> validate_percentage(50.5, "growth_rate")
        50.5
        >>> validate_percentage(-10, "margin", allow_negative=True)
        -10.0
        >>> validate_percentage(150, "margin")
        Traceback (most recent call last):
        ValueError: margin must be between 0.0% and 100.0% (got 150.0%)
    """
    if not allow_negative and value < 0:
        raise ValueError(f"{field_name} cannot be negative (got {value}%)")

    if allow_negative:
        # For negative percentages, check against extended range
        actual_min = min(min_value, -500.0)  # Allow up to -500% for extreme cases
        if value < actual_min:
            raise ValueError(
                f"{field_name} is unreasonably low (got {value}%, minimum: {actual_min}%)"
            )

    if value < min_value or value > max_value:
        raise ValueError(
            f"{field_name} must be between {min_value}% and {max_value}% (got {value}%)"
        )

    return value


def validate_rate_decimal(
    value: float,
    field_name: str = "rate",
    min_value: float = 0.0,
    max_value: float = 1.0,
) -> float:
    """Validate rate as decimal (0.0 to 1.0).

    Args:
        value: Rate value as decimal to validate
        field_name: Name of field for error messages
        min_value: Minimum allowed value (default: 0.0)
        max_value: Maximum allowed value (default: 1.0)

    Returns:
        The validated rate value

    Raises:
        ValueError: If rate is out of valid range

    Example:
        >>> validate_rate_decimal(0.05, "churn_rate")
        0.05
        >>> validate_rate_decimal(1.5, "churn_rate")
        Traceback (most recent call last):
        ValueError: churn_rate must be between 0.0 and 1.0 (got 1.5)
    """
    if value < min_value or value > max_value:
        raise ValueError(
            f"{field_name} must be between {min_value} and {max_value} (got {value})"
        )
    return value


def validate_currency_amount(
    value: Union[int, float, Decimal],
    field_name: str = "amount",
    allow_negative: bool = False,
    max_amount: Optional[float] = None,
) -> Union[int, float, Decimal]:
    """Validate currency amount with sanity checks.

    Args:
        value: Currency amount to validate
        field_name: Name of field for error messages
        allow_negative: Whether to allow negative amounts (e.g., refunds)
        max_amount: Maximum allowed amount for sanity check (default: $1B)

    Returns:
        The validated currency amount

    Raises:
        ValueError: If amount is invalid or unreasonable

    Example:
        >>> validate_currency_amount(1000.50, "revenue")
        1000.5
        >>> validate_currency_amount(-100, "revenue")
        Traceback (most recent call last):
        ValueError: revenue cannot be negative (got -100)
        >>> validate_currency_amount(2000000000, "revenue")
        Traceback (most recent call last):
        ValueError: revenue seems unreasonably high (got $2,000,000,000.00, max: $1,000,000,000.00)
    """
    if not allow_negative and value < 0:
        raise ValueError(f"{field_name} cannot be negative (got {value})")

    # Sanity check: default max is $1B
    if max_amount is None:
        max_amount = 1_000_000_000.0

    if abs(value) > max_amount:
        raise ValueError(
            f"{field_name} seems unreasonably high "
            f"(got ${abs(value):,.2f}, max: ${max_amount:,.2f})"
        )

    return value


def validate_period_months(
    value: int,
    field_name: str = "period_months",
    min_months: int = 1,
    max_months: int = 60,
) -> int:
    """Validate period in months.

    Args:
        value: Number of months to validate
        field_name: Name of field for error messages
        min_months: Minimum allowed months (default: 1)
        max_months: Maximum allowed months (default: 60 / 5 years)

    Returns:
        The validated period in months

    Raises:
        ValueError: If period is out of valid range

    Example:
        >>> validate_period_months(12, "analysis_period")
        12
        >>> validate_period_months(0, "analysis_period")
        Traceback (most recent call last):
        ValueError: analysis_period must be between 1 and 60 months (got 0)
    """
    if value < min_months or value > max_months:
        raise ValueError(
            f"{field_name} must be between {min_months} and {max_months} months (got {value})"
        )
    return value


def validate_date_string(
    value: str,
    field_name: str = "date",
    date_format: str = "%Y-%m-%d",
) -> str:
    """Validate date string format.

    Args:
        value: Date string to validate
        field_name: Name of field for error messages
        date_format: Expected date format (default: YYYY-MM-DD)

    Returns:
        The validated date string

    Raises:
        ValueError: If date string is invalid format

    Example:
        >>> validate_date_string("2024-01-15", "start_date")
        '2024-01-15'
        >>> validate_date_string("15-01-2024", "start_date")
        Traceback (most recent call last):
        ValueError: start_date must be in format %Y-%m-%d (got 15-01-2024)
    """
    try:
        datetime.strptime(value, date_format)
        return value
    except ValueError:
        raise ValueError(
            f"{field_name} must be in format {date_format} (got {value})"
        )


def validate_date_range(
    start_date: Union[str, datetime, date],
    end_date: Union[str, datetime, date],
    field_name: str = "date_range",
) -> tuple[Union[str, datetime, date], Union[str, datetime, date]]:
    """Validate that end_date is after start_date.

    Args:
        start_date: Start date (string, datetime, or date)
        end_date: End date (string, datetime, or date)
        field_name: Name of field for error messages

    Returns:
        Tuple of (start_date, end_date)

    Raises:
        ValueError: If end_date is before or equal to start_date

    Example:
        >>> validate_date_range("2024-01-01", "2024-12-31")
        ('2024-01-01', '2024-12-31')
        >>> validate_date_range("2024-12-31", "2024-01-01")
        Traceback (most recent call last):
        ValueError: date_range: end_date must be after start_date
    """
    # Convert to datetime for comparison if needed
    if isinstance(start_date, str):
        start_dt = datetime.fromisoformat(start_date)
    elif isinstance(start_date, date):
        start_dt = datetime.combine(start_date, datetime.min.time())
    else:
        start_dt = start_date

    if isinstance(end_date, str):
        end_dt = datetime.fromisoformat(end_date)
    elif isinstance(end_date, date):
        end_dt = datetime.combine(end_date, datetime.min.time())
    else:
        end_dt = end_date

    if end_dt <= start_dt:
        raise ValueError(f"{field_name}: end_date must be after start_date")

    return start_date, end_date


def validate_count(
    value: int,
    field_name: str = "count",
    min_count: int = 1,
    max_count: Optional[int] = None,
) -> int:
    """Validate count/quantity values.

    Args:
        value: Count value to validate
        field_name: Name of field for error messages
        min_count: Minimum allowed count (default: 1)
        max_count: Maximum allowed count for sanity check (optional)

    Returns:
        The validated count value

    Raises:
        ValueError: If count is out of valid range

    Example:
        >>> validate_count(100, "customers")
        100
        >>> validate_count(0, "customers")
        Traceback (most recent call last):
        ValueError: customers must be at least 1 (got 0)
    """
    if value < min_count:
        raise ValueError(f"{field_name} must be at least {min_count} (got {value})")

    if max_count is not None and value > max_count:
        raise ValueError(
            f"{field_name} seems unreasonably high (got {value:,}, max: {max_count:,})"
        )

    return value


def validate_ratio(
    numerator: Union[int, float],
    denominator: Union[int, float],
    field_name: str = "ratio",
    allow_zero_denominator: bool = False,
) -> tuple[Union[int, float], Union[int, float]]:
    """Validate ratio components.

    Args:
        numerator: Ratio numerator
        denominator: Ratio denominator
        field_name: Name of field for error messages
        allow_zero_denominator: Whether to allow zero denominator

    Returns:
        Tuple of (numerator, denominator)

    Raises:
        ValueError: If denominator is zero (when not allowed)

    Example:
        >>> validate_ratio(3, 1, "ltv_cac_ratio")
        (3, 1)
        >>> validate_ratio(3, 0, "ltv_cac_ratio")
        Traceback (most recent call last):
        ValueError: ltv_cac_ratio: denominator cannot be zero
    """
    if not allow_zero_denominator and denominator == 0:
        raise ValueError(f"{field_name}: denominator cannot be zero")

    return numerator, denominator


def validate_growth_rate(
    value: float,
    field_name: str = "growth_rate",
) -> float:
    """Validate growth rate percentage with sanity checks.

    Args:
        value: Growth rate percentage to validate
        field_name: Name of field for error messages

    Returns:
        The validated growth rate

    Raises:
        ValueError: If growth rate is unreasonable

    Example:
        >>> validate_growth_rate(50.0, "revenue_growth")
        50.0
        >>> validate_growth_rate(1500.0, "revenue_growth")
        Traceback (most recent call last):
        ValueError: revenue_growth seems unreasonably high (got 1500.0%, max: 1000.0%)
    """
    # Growth can be negative (decline)
    if value < -100:
        raise ValueError(
            f"{field_name} cannot be less than -100% (complete loss) (got {value}%)"
        )

    # Very high growth is suspicious (>1000%)
    if value > 1000:
        raise ValueError(
            f"{field_name} seems unreasonably high (got {value}%, max: 1000.0%)"
        )

    return value


def validate_churn_rate(
    value: float,
    field_name: str = "churn_rate",
    period: str = "monthly",
) -> float:
    """Validate churn rate with period-specific sanity checks.

    Args:
        value: Churn rate percentage to validate
        field_name: Name of field for error messages
        period: Period type ("monthly", "annual")

    Returns:
        The validated churn rate

    Raises:
        ValueError: If churn rate is unreasonable for the period

    Example:
        >>> validate_churn_rate(2.0, "monthly_churn", "monthly")
        2.0
        >>> validate_churn_rate(50.0, "monthly_churn", "monthly")
        Traceback (most recent call last):
        ValueError: monthly_churn seems unreasonably high for monthly period
    """
    # Churn cannot be negative
    if value < 0:
        raise ValueError(f"{field_name} cannot be negative (got {value}%)")

    # Churn cannot exceed 100%
    if value > 100:
        raise ValueError(
            f"{field_name} cannot exceed 100% (got {value}%)"
        )

    # Period-specific sanity checks
    if period == "monthly":
        # Monthly churn > 20% is extreme
        if value > 20:
            raise ValueError(
                f"{field_name} seems unreasonably high for monthly period "
                f"(got {value}%, typical max: 20.0%)"
            )
    elif period == "annual":
        # Annual churn > 100% would mean losing more than entire customer base
        if value > 100:
            raise ValueError(
                f"{field_name} cannot exceed 100% for annual period (got {value}%)"
            )

    return value


def validate_arpu(
    value: float,
    field_name: str = "arpu",
    min_arpu: float = 0.01,
    max_arpu: float = 1_000_000.0,
) -> float:
    """Validate Average Revenue Per User with sanity checks.

    Args:
        value: ARPU value to validate
        field_name: Name of field for error messages
        min_arpu: Minimum reasonable ARPU (default: $0.01)
        max_arpu: Maximum reasonable ARPU (default: $1M/month)

    Returns:
        The validated ARPU value

    Raises:
        ValueError: If ARPU is unreasonable

    Example:
        >>> validate_arpu(100.0, "monthly_arpu")
        100.0
        >>> validate_arpu(2000000.0, "monthly_arpu")
        Traceback (most recent call last):
        ValueError: monthly_arpu seems unreasonably high (got $2,000,000.00, max: $1,000,000.00)
    """
    if value < min_arpu:
        raise ValueError(
            f"{field_name} must be at least ${min_arpu:.2f} (got ${value:.2f})"
        )

    if value > max_arpu:
        raise ValueError(
            f"{field_name} seems unreasonably high (got ${value:,.2f}, max: ${max_arpu:,.2f})"
        )

    return value


def validate_margin(
    value: float,
    field_name: str = "margin",
    margin_type: str = "gross",
) -> float:
    """Validate margin percentage with type-specific checks.

    Args:
        value: Margin percentage to validate
        field_name: Name of field for error messages
        margin_type: Type of margin ("gross", "net", "operating", "ebitda")

    Returns:
        The validated margin value

    Raises:
        ValueError: If margin is unreasonable for the type

    Example:
        >>> validate_margin(80.0, "gross_margin", "gross")
        80.0
        >>> validate_margin(150.0, "gross_margin", "gross")
        Traceback (most recent call last):
        ValueError: gross_margin (gross) cannot exceed 100% (got 150.0%)
    """
    # Margin cannot exceed 100% (unless specific types allow it)
    if margin_type in ["gross", "operating"] and value > 100:
        raise ValueError(
            f"{field_name} ({margin_type}) cannot exceed 100% (got {value}%)"
        )

    # EBITDA margin can be negative but should have reasonable bounds
    if margin_type == "ebitda":
        if value < -500:
            raise ValueError(
                f"{field_name} (ebitda) seems unreasonably low (got {value}%, min: -500%)"
            )
        if value > 100:
            raise ValueError(
                f"{field_name} (ebitda) cannot exceed 100% (got {value}%)"
            )

    # Net margin typically has tighter bounds
    if margin_type == "net":
        if value < -200:
            raise ValueError(
                f"{field_name} (net) seems unreasonably low (got {value}%, min: -200%)"
            )
        if value > 100:
            raise ValueError(
                f"{field_name} (net) cannot exceed 100% (got {value}%)"
            )

    return value


def validate_cac_ltv_ratio(
    ltv: float,
    cac: float,
) -> tuple[float, float]:
    """Validate LTV:CAC ratio components with sanity checks.

    Args:
        ltv: Lifetime Value
        cac: Customer Acquisition Cost

    Returns:
        Tuple of (ltv, cac)

    Raises:
        ValueError: If LTV or CAC values are unreasonable

    Example:
        >>> validate_cac_ltv_ratio(4000, 1000)
        (4000, 1000)
        >>> validate_cac_ltv_ratio(100, 0)
        Traceback (most recent call last):
        ValueError: CAC cannot be zero for LTV:CAC ratio calculation
    """
    if cac <= 0:
        raise ValueError("CAC cannot be zero for LTV:CAC ratio calculation")

    if ltv < 0:
        raise ValueError(f"LTV cannot be negative (got ${ltv:,.2f})")

    # Warn if ratio would be unreasonable
    ratio = ltv / cac
    if ratio > 100:
        raise ValueError(
            f"LTV:CAC ratio seems unreasonably high ({ratio:.1f}:1). "
            "Verify LTV and CAC calculations."
        )

    return ltv, cac


def validate_financial_data_consistency(
    revenue: float,
    costs: float,
    margin_percent: Optional[float] = None,
) -> tuple[float, float, Optional[float]]:
    """Validate consistency between revenue, costs, and margin.

    Args:
        revenue: Total revenue
        costs: Total costs
        margin_percent: Margin percentage (optional)

    Returns:
        Tuple of (revenue, costs, margin_percent)

    Raises:
        ValueError: If data is inconsistent

    Example:
        >>> validate_financial_data_consistency(100000, 30000, 70.0)
        (100000, 30000, 70.0)
        >>> validate_financial_data_consistency(100000, 30000, 50.0)
        Traceback (most recent call last):
        ValueError: Margin inconsistency: calculated margin is 70.0% but provided margin is 50.0%
    """
    if revenue < 0:
        raise ValueError(f"Revenue cannot be negative (got ${revenue:,.2f})")

    if costs < 0:
        raise ValueError(f"Costs cannot be negative (got ${costs:,.2f})")

    if costs > revenue:
        # This is allowed (negative margin) but worth noting
        pass

    if margin_percent is not None:
        # Calculate actual margin and compare
        calculated_margin = ((revenue - costs) / revenue * 100) if revenue > 0 else 0
        margin_diff = abs(calculated_margin - margin_percent)

        # Allow small rounding differences (0.5%)
        if margin_diff > 0.5:
            raise ValueError(
                f"Margin inconsistency: calculated margin is {calculated_margin:.1f}% "
                f"but provided margin is {margin_percent:.1f}%"
            )

    return revenue, costs, margin_percent


def validate_ai_cost_data(
    total_cost: float,
    interactions: int,
    revenue: float,
) -> tuple[float, int, float]:
    """Validate AI cost data with sanity checks.

    Args:
        total_cost: Total AI costs
        interactions: Number of AI interactions
        revenue: Total revenue for context

    Returns:
        Tuple of (total_cost, interactions, revenue)

    Raises:
        ValueError: If AI cost data is unreasonable

    Example:
        >>> validate_ai_cost_data(50000, 1000000, 500000)
        (50000, 1000000, 500000)
        >>> validate_ai_cost_data(600000, 1000000, 500000)
        Traceback (most recent call last):
        ValueError: AI costs (120.0% of revenue) seem unreasonably high - verify data
    """
    if total_cost < 0:
        raise ValueError(f"AI costs cannot be negative (got ${total_cost:,.2f})")

    if interactions <= 0:
        raise ValueError(f"AI interactions must be positive (got {interactions})")

    if revenue <= 0:
        raise ValueError(f"Revenue must be positive for AI cost validation (got ${revenue:,.2f})")

    # Check cost per interaction
    cost_per_interaction = total_cost / interactions
    if cost_per_interaction > 1.0:
        raise ValueError(
            f"Cost per AI interaction (${cost_per_interaction:.2f}) seems very high - verify pricing data"  # noqa: E501
        )

    # Check AI cost as percentage of revenue
    ai_cost_percentage = (total_cost / revenue) * 100
    if ai_cost_percentage > 50:
        raise ValueError(
            f"AI costs ({ai_cost_percentage:.1f}% of revenue) seem unreasonably high - verify data"
        )

    return total_cost, interactions, revenue


# Pydantic field validators for use in models
def create_positive_validator(allow_zero: bool = False):
    """Create a Pydantic field validator for positive numbers.

    Args:
        allow_zero: Whether to allow zero as valid

    Returns:
        Validator function for Pydantic models

    Example:
        class MyModel(BaseModel):
            revenue: float = Field(gt=0)

            @field_validator("revenue")
            @classmethod
            def validate_revenue(cls, v: float) -> float:
                return validate_positive_number(v, "revenue")
    """
    def validator(cls, v: float, info: "ValidationInfo") -> float:
        field_name = info.field_name if info else "value"
        return validate_positive_number(v, field_name, allow_zero)
    return validator


def create_percentage_validator(min_val: float = 0.0, max_val: float = 100.0, allow_negative: bool = False):  # noqa: E501
    """Create a Pydantic field validator for percentages.

    Args:
        min_val: Minimum percentage value
        max_val: Maximum percentage value
        allow_negative: Whether to allow negative percentages

    Returns:
        Validator function for Pydantic models
    """
    def validator(cls, v: float, info: "ValidationInfo") -> float:
        field_name = info.field_name if info else "percentage"
        return validate_percentage(v, field_name, min_val, max_val, allow_negative)
    return validator


def create_currency_validator(allow_negative: bool = False, max_amount: Optional[float] = None):
    """Create a Pydantic field validator for currency amounts.

    Args:
        allow_negative: Whether to allow negative amounts
        max_amount: Maximum allowed amount

    Returns:
        Validator function for Pydantic models
    """
    def validator(cls, v: float, info: "ValidationInfo") -> float:
        field_name = info.field_name if info else "amount"
        return validate_currency_amount(v, field_name, allow_negative, max_amount)
    return validator
