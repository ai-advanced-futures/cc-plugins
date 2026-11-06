"""SDE-based valuation calculator with stress testing.

This module provides tools for calculating business valuations based on
Seller's Discretionary Earnings (SDE) and performing stress tests to evaluate
financial safety margins under debt service.
"""

from typing import Dict


class ValuationCalculator:
    """Calculator for SDE-based valuations and stress testing."""

    def calculate_purchase_price(self, sde: float, multiple: float) -> float:
        """Calculate purchase price from SDE and multiple.

        Args:
            sde: Seller's Discretionary Earnings
            multiple: Valuation multiple to apply

        Returns:
            Purchase price (SDE × multiple)

        Example:
            >>> calc = ValuationCalculator()
            >>> calc.calculate_purchase_price(sde=100000, multiple=3.0)
            300000.0
        """
        return sde * multiple

    def calculate_sde(self, purchase_price: float, multiple: float) -> float:
        """Calculate SDE from purchase price and multiple.

        Args:
            purchase_price: Target purchase price
            multiple: Valuation multiple used

        Returns:
            Required SDE (purchase_price / multiple)

        Example:
            >>> calc = ValuationCalculator()
            >>> calc.calculate_sde(purchase_price=300000, multiple=3.0)
            100000.0
        """
        return purchase_price / multiple

    def stress_test(self, params: Dict) -> Dict:
        """Perform stress test on acquisition financing.

        Calculates debt service burden, safety margins, and determines how much
        SDE can drop before cash flow becomes problematic.

        Args:
            params: Dictionary containing:
                - sde: Current Seller's Discretionary Earnings
                - purchase_price: Target purchase price
                - down_payment: Down payment amount
                - interest_rate: Annual interest rate (decimal, e.g., 0.08 for 8%)
                - loan_term_years: Loan term in years
                - manager_salary: Annual manager salary if owner steps back
                - working_capital_buffer: Cash buffer for operations

        Returns:
            Dictionary containing:
                - debt_service_annual: Annual debt payment
                - remaining_sde: SDE after debt service
                - total_burden: Manager salary + working capital buffer
                - safety_margin: Remaining SDE - total burden
                - sde_drop_tolerance: Percentage SDE can drop before trouble
                - break_even_sde: SDE level where safety margin = 0

        Example:
            >>> calc = ValuationCalculator()
            >>> result = calc.stress_test({
            ...     'sde': 150000,
            ...     'purchase_price': 500000,
            ...     'down_payment': 100000,
            ...     'interest_rate': 0.08,
            ...     'loan_term_years': 10,
            ...     'manager_salary': 50000,
            ...     'working_capital_buffer': 20000
            ... })
            >>> result['sde_drop_tolerance']  # doctest: +SKIP
            14.0
        """
        # Calculate loan amount
        loan_amount = params['purchase_price'] - params['down_payment']

        # Calculate annual debt service using amortization formula
        # Formula: P × [r(1+r)^n] / [(1+r)^n - 1]
        # where P = principal, r = monthly rate, n = number of payments
        monthly_rate = params['interest_rate'] / 12
        num_payments = params['loan_term_years'] * 12

        # Amortization formula
        monthly_payment = loan_amount * (
            (monthly_rate * (1 + monthly_rate) ** num_payments) /
            ((1 + monthly_rate) ** num_payments - 1)
        )

        debt_service_annual = monthly_payment * 12

        # Calculate remaining SDE after debt service
        remaining_sde = params['sde'] - debt_service_annual

        # Calculate total burden (manager salary + working capital)
        total_burden = params['manager_salary'] + params['working_capital_buffer']

        # Calculate safety margin
        safety_margin = remaining_sde - total_burden

        # Calculate SDE drop tolerance (as percentage)
        sde_drop_tolerance = (safety_margin / params['sde']) * 100

        # Calculate break-even SDE (where safety margin = 0)
        break_even_sde = debt_service_annual + total_burden

        return {
            'debt_service_annual': debt_service_annual,
            'remaining_sde': remaining_sde,
            'total_burden': total_burden,
            'safety_margin': safety_margin,
            'sde_drop_tolerance': sde_drop_tolerance,
            'break_even_sde': break_even_sde
        }
