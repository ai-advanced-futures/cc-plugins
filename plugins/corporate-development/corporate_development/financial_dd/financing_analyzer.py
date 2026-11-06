"""
Financing analyzer for M&A transactions.

Implements book's debt capacity formulas and leverage scenario modeling
using 1.25x/1.5x debt-to-earnings thresholds.

All calculations are deterministic mathematical formulas - no AI estimation.
"""

from typing import List

from corporate_development.financial_dd.types import (
    DebtCapacity,
    FinancingAssumptions,
    LeverageScenario,
)


def calculate_debt_capacity(
    sde: float,
    assumptions: FinancingAssumptions,
) -> DebtCapacity:
    """
    Calculate maximum debt capacity using book's threshold ratios.

    Book standards:
    - Conservative (minimum bankable): 1.25x debt-to-earnings
    - Preferred (safer margin): 1.5x debt-to-earnings

    Args:
        sde: Seller's discretionary earnings (annual)
        assumptions: Financing terms (interest rate, term)

    Returns:
        DebtCapacity with conservative and preferred scenarios

    Example:
        >>> sde = 300_000.0
        >>> assumptions = FinancingAssumptions(interest_rate=0.07, term_years=10)
        >>> capacity = calculate_debt_capacity(sde, assumptions)
        >>> capacity.max_debt_conservative
        375000.0
        >>> capacity.debt_to_earnings_conservative
        1.25
    """
    # Book standard thresholds
    CONSERVATIVE_RATIO = 1.25  # Minimum bankable
    PREFERRED_RATIO = 1.5  # Safer margin

    # Calculate maximum debt at each threshold
    max_debt_conservative = sde * CONSERVATIVE_RATIO
    max_debt_preferred = sde * PREFERRED_RATIO

    # Calculate monthly payments using standard amortization formula
    monthly_payment_conservative = _calculate_monthly_payment(
        principal=max_debt_conservative,
        annual_rate=assumptions.interest_rate,
        term_years=assumptions.term_years,
    )

    monthly_payment_preferred = _calculate_monthly_payment(
        principal=max_debt_preferred,
        annual_rate=assumptions.interest_rate,
        term_years=assumptions.term_years,
    )

    return DebtCapacity(
        max_debt_conservative=max_debt_conservative,
        max_debt_preferred=max_debt_preferred,
        debt_to_earnings_conservative=CONSERVATIVE_RATIO,
        debt_to_earnings_preferred=PREFERRED_RATIO,
        monthly_payment_conservative=monthly_payment_conservative,
        monthly_payment_preferred=monthly_payment_preferred,
        annual_debt_service_conservative=monthly_payment_conservative * 12,
        annual_debt_service_preferred=monthly_payment_preferred * 12,
    )


def _calculate_monthly_payment(
    principal: float,
    annual_rate: float,
    term_years: int,
) -> float:
    """
    Calculate monthly payment using standard amortization formula.

    Formula: P * [r(1+r)^n] / [(1+r)^n - 1]
    where:
        P = principal (loan amount)
        r = monthly interest rate
        n = number of monthly payments

    Args:
        principal: Loan amount
        annual_rate: Annual interest rate (e.g., 0.07 for 7%)
        term_years: Loan term in years

    Returns:
        Monthly payment amount

    Example:
        >>> # $375k @ 7% for 10 years
        >>> payment = _calculate_monthly_payment(375_000, 0.07, 10)
        >>> round(payment, 2)
        4354.03
    """
    if principal == 0:
        return 0.0

    # Convert to monthly values
    monthly_rate = annual_rate / 12
    num_payments = term_years * 12

    # Standard amortization formula
    # payment = P * [r(1+r)^n] / [(1+r)^n - 1]
    factor = (1 + monthly_rate) ** num_payments
    numerator = monthly_rate * factor
    denominator = factor - 1

    monthly_payment = principal * (numerator / denominator)

    return monthly_payment


def model_leverage_scenarios(
    purchase_price: float,
    sde: float,
    assumptions: FinancingAssumptions,
) -> List[LeverageScenario]:
    """
    Model standard leverage scenarios with ROI calculations.

    Generates 4 scenarios:
    1. 0% leverage (all cash)
    2. 50% leverage
    3. 80% leverage
    4. 90% leverage

    Each scenario includes:
    - Debt amount and equity required
    - Monthly debt service
    - Cash-on-cash ROI
    - Debt-to-earnings ratio
    - Threshold compliance (1.25x and 1.5x)

    Args:
        purchase_price: Total acquisition price
        sde: Seller's discretionary earnings (annual)
        assumptions: Financing terms

    Returns:
        List of 4 leverage scenarios with detailed metrics

    Example:
        >>> # Book example: $1.5M purchase with $300k SDE
        >>> scenarios = model_leverage_scenarios(1_500_000, 300_000,
        ...     FinancingAssumptions(interest_rate=0.07, term_years=10))
        >>> len(scenarios)
        4
        >>> scenarios[0].leverage_percentage
        0.0
        >>> scenarios[1].leverage_percentage
        0.5
    """
    # Standard leverage percentages to model
    LEVERAGE_PERCENTAGES = [0.0, 0.5, 0.8, 0.9]

    # Book's debt-to-earnings thresholds
    CONSERVATIVE_THRESHOLD = 1.25
    PREFERRED_THRESHOLD = 1.5

    scenarios = []

    for leverage_pct in LEVERAGE_PERCENTAGES:
        # Calculate debt and equity
        debt_amount = purchase_price * leverage_pct
        equity_required = purchase_price - debt_amount

        # Calculate monthly debt service
        monthly_debt_service = _calculate_monthly_payment(
            principal=debt_amount,
            annual_rate=assumptions.interest_rate,
            term_years=assumptions.term_years,
        )

        # Calculate annual debt service
        annual_debt_service = monthly_debt_service * 12

        # Calculate cash flow after debt service
        annual_cash_flow = sde - annual_debt_service

        # Calculate cash-on-cash ROI
        # ROI = annual cash flow / equity invested
        if equity_required > 0:
            cash_on_cash_roi = annual_cash_flow / equity_required
        else:
            # Edge case: 100% leverage (theoretical)
            cash_on_cash_roi = float("inf") if annual_cash_flow > 0 else 0.0

        # Calculate debt-to-earnings ratio
        debt_to_earnings = debt_amount / sde if sde > 0 else 0.0

        # Check threshold compliance
        meets_conservative = debt_to_earnings <= CONSERVATIVE_THRESHOLD
        meets_preferred = debt_to_earnings <= PREFERRED_THRESHOLD

        scenario = LeverageScenario(
            leverage_percentage=leverage_pct,
            debt_amount=debt_amount,
            equity_required=equity_required,
            monthly_debt_service=monthly_debt_service,
            annual_debt_service=annual_debt_service,
            annual_cash_flow=annual_cash_flow,
            cash_on_cash_roi=cash_on_cash_roi,
            debt_to_earnings=debt_to_earnings,
            meets_conservative_threshold=meets_conservative,
            meets_preferred_threshold=meets_preferred,
        )

        scenarios.append(scenario)

    return scenarios


class FinancingAnalyzer:
    """
    Wrapper class for financing analysis functions.

    This class provides a convenient interface to the module's calculation functions
    while maintaining backward compatibility with code that expects a class interface.
    """

    @staticmethod
    def calculate_debt_capacity(
        sde: float,
        assumptions: FinancingAssumptions,
    ) -> DebtCapacity:
        """Calculate debt capacity. See module-level calculate_debt_capacity() for details."""
        return calculate_debt_capacity(sde, assumptions)

    @staticmethod
    def model_leverage_scenarios(
        purchase_price: float,
        sde: float,
        assumptions: FinancingAssumptions,
    ) -> List[LeverageScenario]:
        """Model leverage scenarios. See module-level model_leverage_scenarios() for details."""
        return model_leverage_scenarios(purchase_price, sde, assumptions)
