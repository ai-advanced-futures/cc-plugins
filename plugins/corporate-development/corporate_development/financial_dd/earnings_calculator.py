"""
Earnings calculator for Financial Due Diligence.

This module implements deterministic calculations for EBITDA and SDE based on
Chapter 7 ("Buy for the Future, Pay for the Past") of "Buy Then Build".

Key principles:
- 100% deterministic Python arithmetic (zero AI in calculations)
- Size-aware SDE context (same formula, different interpretation)
- Complete calculation audit trails for transparency

All formulas are pure functions that take FinancialMetrics and return results
with step-by-step breakdowns.
"""

from typing import List
from corporate_development.financial_dd.types import (
    FinancialMetrics,
    CompanySize,
    CalculationResult,
)


def calculate_ebitda(metrics: FinancialMetrics) -> CalculationResult:
    """
    Calculate EBITDA using the formula from "Buy Then Build" Chapter 7.

    Formula: EBITDA = Net Income + Interest + Taxes + Depreciation + Amortization + One-time Expenses

    This is the foundational earnings metric that:
    1. Removes financing decisions (interest)
    2. Removes tax jurisdictions (taxes)
    3. Removes non-cash charges (D&A)
    4. Removes non-recurring items (one-time expenses)

    Args:
        metrics: Financial metrics from statements

    Returns:
        CalculationResult with EBITDA value and detailed steps
    """
    steps: List[str] = []

    # Start with Net Income
    net_income = metrics.net_income.value if metrics.net_income else 0
    steps.append(f"Net Income: ${net_income:,.2f}")

    # Add back Interest
    interest = metrics.interest_expense.value if metrics.interest_expense else 0
    steps.append(f"Interest: +${interest:,.2f}")

    # Add back Taxes
    taxes = metrics.tax_expense.value if metrics.tax_expense else 0
    steps.append(f"Taxes: +${taxes:,.2f}")

    # Add back Depreciation
    depreciation = metrics.depreciation.value if metrics.depreciation else 0
    steps.append(f"Depreciation: +${depreciation:,.2f}")

    # Add back Amortization
    amortization = metrics.amortization.value if metrics.amortization else 0
    steps.append(f"Amortization: +${amortization:,.2f}")

    # Add back One-time Expenses (if present)
    one_time = metrics.one_time_expenses.value if metrics.one_time_expenses else 0
    if one_time > 0:
        steps.append(f"One-time expenses: +${one_time:,.2f}")

    # Calculate EBITDA
    ebitda = net_income + interest + taxes + depreciation + amortization + one_time
    steps.append(f"EBITDA: ${ebitda:,.2f}")

    return CalculationResult(
        value=ebitda,
        calculation_steps="\n".join(steps),
        data_sources=[
            metrics.net_income.source if metrics.net_income else "unknown",
            metrics.interest_expense.source if metrics.interest_expense else "unknown",
            metrics.tax_expense.source if metrics.tax_expense else "unknown",
            metrics.depreciation.source if metrics.depreciation else "unknown",
            metrics.amortization.source if metrics.amortization else "unknown",
        ],
        notes="EBITDA calculated per 'Buy Then Build' Chapter 7 formula",
    )


def calculate_sde(metrics: FinancialMetrics, company_size: CompanySize) -> CalculationResult:
    """
    Calculate Seller's Discretionary Earnings with size-aware context.

    Formula: SDE = EBITDA + Owner Compensation + Owner Benefits

    The formula is the same for all company sizes, but the interpretation changes:

    Small/Medium businesses:
    - Owner compensation = actual owner salary
    - Owner benefits = personal expenses run through business

    Mid-market/Enterprise:
    - Owner compensation = excess executive compensation above market rate
    - Owner benefits = investor returns/distributions (if applicable)

    This is the "total economic benefit" metric that shows what a new owner
    could extract from the business.

    Args:
        metrics: Financial metrics from statements
        company_size: Size of company (affects interpretation, not math)

    Returns:
        CalculationResult with SDE value and context-appropriate steps
    """
    steps: List[str] = []

    # Start with EBITDA
    ebitda_result = calculate_ebitda(metrics)
    ebitda = ebitda_result.value
    steps.append(f"EBITDA: ${ebitda:,.2f}")

    # Add owner compensation (context-aware label)
    owner_comp = metrics.owner_compensation.value if metrics.owner_compensation else 0
    if company_size in [CompanySize.SMALL, CompanySize.MEDIUM]:
        comp_label = "Owner compensation"
    else:
        comp_label = "Excess executive compensation"
    steps.append(f"{comp_label}: +${owner_comp:,.2f}")

    # Add owner benefits (context-aware label and calculation)
    if company_size in [CompanySize.SMALL, CompanySize.MEDIUM]:
        owner_benefits = _calculate_owner_personal_benefits(metrics)
        steps.append(f"Owner personal benefits: +${owner_benefits:,.2f}")
    else:
        # For larger companies, use investor returns if available
        owner_benefits = _calculate_investor_returns(metrics)
        if owner_benefits > 0:
            steps.append(f"Investor returns/distributions: +${owner_benefits:,.2f}")

    # Calculate SDE
    sde = ebitda + owner_comp + owner_benefits
    steps.append(f"SDE: ${sde:,.2f}")

    # Build context notes
    context_notes = _get_sde_context_notes(company_size)

    return CalculationResult(
        value=sde,
        calculation_steps="\n".join(steps),
        data_sources=ebitda_result.data_sources + [
            metrics.owner_compensation.source if metrics.owner_compensation else "unknown",
        ],
        notes=context_notes,
    )


def _calculate_owner_personal_benefits(metrics: FinancialMetrics) -> float:
    """
    Calculate owner personal benefits for small/medium businesses.

    This includes personal expenses run through the business:
    - Auto expenses (personal use)
    - Travel/entertainment (personal portion)
    - Home office expenses
    - Health insurance for family
    - Other personal benefits

    Args:
        metrics: Financial metrics

    Returns:
        Total owner personal benefits
    """
    return metrics.owner_benefits.value if metrics.owner_benefits else 0


def _calculate_investor_returns(metrics: FinancialMetrics) -> float:
    """
    Calculate investor returns for mid-market/enterprise companies.

    For larger companies, this represents distributions to investors that
    a new owner could redirect to themselves.

    Note: This is often $0 for actively managed companies where profits
    are reinvested rather than distributed.

    Args:
        metrics: Financial metrics

    Returns:
        Total investor returns/distributions
    """
    # For now, use owner_benefits field with enterprise context
    # In future, this could pull from separate distribution tracking
    return metrics.owner_benefits.value if metrics.owner_benefits else 0


def _get_sde_context_notes(company_size: CompanySize) -> str:
    """
    Get context-appropriate notes for SDE calculation.

    Args:
        company_size: Size of company

    Returns:
        Context notes explaining SDE interpretation
    """
    if company_size == CompanySize.SMALL:
        return (
            "SDE for small business: Represents total economic benefit to owner, "
            "including salary, personal benefits, and business profits. "
            "Used for valuation multiples in small business acquisitions."
        )
    elif company_size == CompanySize.MEDIUM:
        return (
            "SDE for medium business: Represents owner's total compensation "
            "including salary, benefits, and discretionary expenses. "
            "Useful for owner-operator transition planning."
        )
    elif company_size == CompanySize.MID_MARKET:
        return (
            "SDE for mid-market company: Same formula as EBITDA plus any "
            "excess executive compensation above market rates. "
            "Less relevant than EBITDA at this scale."
        )
    else:  # ENTERPRISE
        return (
            "SDE for enterprise: Typically equivalent to EBITDA as executive "
            "compensation is already at market rates. "
            "Included for completeness but EBITDA is the primary metric."
        )


class EarningsCalculator:
    """
    Wrapper class for earnings calculation functions.

    This class provides a convenient interface to the module's calculation functions
    while maintaining backward compatibility with code that expects a class interface.
    """

    @staticmethod
    def calculate_ebitda(metrics: FinancialMetrics) -> CalculationResult:
        """Calculate EBITDA. See module-level calculate_ebitda() for details."""
        return calculate_ebitda(metrics)

    @staticmethod
    def calculate_sde(metrics: FinancialMetrics, company_size: CompanySize) -> CalculationResult:
        """Calculate SDE. See module-level calculate_sde() for details."""
        return calculate_sde(metrics, company_size)
