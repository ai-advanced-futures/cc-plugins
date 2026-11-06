# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
EVC Calculator - Economic Value to Customer

Calculates the economic value a solution creates for customers through multiple
value components: time savings, error reduction, revenue increase, and risk reduction.
Includes performance differentiation premium calculation.

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT

Usage:
    from scripts.evc_calculator import EVCCalculator

    calc = EVCCalculator()
    calc.add_time_savings(hours_saved=40, hourly_rate=75)
    calc.add_error_reduction(errors_avoided=2, cost_per_error=4000)
    result = calc.calculate_total_evc(differentiation_level='medium')
    print(f"Total EVC: ${result['total_evc']:,.2f}/month")
"""

from typing import Dict, Literal


class EVCCalculator:
    """
    Calculate Economic Value to Customer (EVC).

    Components:
        1. Time savings value (hours × hourly rate)
        2. Error reduction value (errors avoided × cost per error)
        3. Revenue increase value (additional revenue generated)
        4. Risk reduction value (probability × impact)
        5. Performance differentiation premium (percentage of total value)

    Performance Premium Benchmarks:
        - Low differentiation (5-10%): Minor improvements over alternatives
        - Medium differentiation (15-25%): Significant improvements in key areas
        - High differentiation (30-50%): Breakthrough innovation or unique capabilities

    Usage:
        calc = EVCCalculator()
        calc.add_time_savings(hours_saved=10, hourly_rate=75)
        calc.add_error_reduction(errors_avoided=5, cost_per_error=500)
        evc = calc.calculate_total_evc(differentiation_level='medium')
    """

    # Performance premium benchmarks
    PREMIUM_RANGES = {
        'low': (0.05, 0.10),       # 5-10% premium
        'medium': (0.15, 0.25),    # 15-25% premium
        'high': (0.30, 0.50)       # 30-50% premium
    }

    def __init__(self):
        """Initialize EVC calculator with empty components."""
        self.components = {
            'time_savings': 0.0,
            'error_reduction': 0.0,
            'revenue_increase': 0.0,
            'risk_reduction': 0.0
        }

    def add_time_savings(self, hours_saved: float, hourly_rate: float) -> None:
        """
        Add time savings component to EVC.

        Args:
            hours_saved: Number of hours saved per period (e.g., per month)
            hourly_rate: Hourly rate of the person/team saving time ($/hour)

        Example:
            # Save 40 hours/month at $75/hour
            calc.add_time_savings(hours_saved=40, hourly_rate=75)
            # Adds $3,000/month to EVC
        """
        if hours_saved < 0:
            raise ValueError("hours_saved must be non-negative")
        if hourly_rate < 0:
            raise ValueError("hourly_rate must be non-negative")

        self.components['time_savings'] = hours_saved * hourly_rate

    def add_error_reduction(self, errors_avoided: float, cost_per_error: float) -> None:
        """
        Add error reduction component to EVC.

        Args:
            errors_avoided: Number of errors prevented per period
            cost_per_error: Average cost to fix/handle each error ($)

        Example:
            # Avoid 2 errors/month at $4,000/error
            calc.add_error_reduction(errors_avoided=2, cost_per_error=4000)
            # Adds $8,000/month to EVC
        """
        if errors_avoided < 0:
            raise ValueError("errors_avoided must be non-negative")
        if cost_per_error < 0:
            raise ValueError("cost_per_error must be non-negative")

        self.components['error_reduction'] = errors_avoided * cost_per_error

    def add_revenue_increase(self, additional_revenue: float) -> None:
        """
        Add revenue increase component to EVC.

        Args:
            additional_revenue: Additional revenue generated per period ($)

        Example:
            # Generate $5,000/month additional revenue
            calc.add_revenue_increase(additional_revenue=5000)
            # Adds $5,000/month to EVC
        """
        if additional_revenue < 0:
            raise ValueError("additional_revenue must be non-negative")

        self.components['revenue_increase'] = additional_revenue

    def add_risk_reduction(self, probability: float, impact: float) -> None:
        """
        Add risk reduction component to EVC.

        Calculates expected value of risk mitigation using: probability × impact

        Args:
            probability: Probability of risk event (0.0 to 1.0)
            impact: Financial impact if risk occurs ($)

        Example:
            # 5% chance of $50,000 SLA penalty per month
            calc.add_risk_reduction(probability=0.05, impact=50000)
            # Adds $2,500/month to EVC (expected value)
        """
        if not 0 <= probability <= 1:
            raise ValueError("probability must be between 0 and 1")
        if impact < 0:
            raise ValueError("impact must be non-negative")

        self.components['risk_reduction'] = probability * impact

    def calculate_performance_premium(
        self,
        base_evc: float,
        differentiation_level: Literal['low', 'medium', 'high']
    ) -> Dict[str, float]:
        """
        Calculate performance differentiation premium.

        The premium reflects how much more customers will pay for superior performance
        or unique capabilities compared to alternatives.

        Args:
            base_evc: Total value from all components before premium
            differentiation_level: Level of differentiation vs competitors
                - 'low': Minor improvements (5-10% premium)
                - 'medium': Significant improvements (15-25% premium)
                - 'high': Breakthrough innovation (30-50% premium)

        Returns:
            Dictionary with:
                - premium_percentage: Percentage applied (0.0 to 0.5)
                - premium_amount: Dollar value of premium

        Example:
            >>> calc = EVCCalculator()
            >>> result = calc.calculate_performance_premium(10000, 'medium')
            >>> 0.15 <= result['premium_percentage'] <= 0.25
            True
        """
        if differentiation_level not in self.PREMIUM_RANGES:
            raise ValueError(
                f"Invalid differentiation_level '{differentiation_level}'. "
                f"Must be 'low', 'medium', or 'high'."
            )

        if base_evc < 0:
            raise ValueError("base_evc must be non-negative")

        # Use midpoint of range for premium calculation
        min_premium, max_premium = self.PREMIUM_RANGES[differentiation_level]
        premium_pct = (min_premium + max_premium) / 2

        premium_amount = base_evc * premium_pct

        return {
            'premium_percentage': premium_pct,
            'premium_amount': premium_amount
        }

    def calculate_total_evc(
        self,
        differentiation_level: Literal['low', 'medium', 'high'] = 'medium'
    ) -> Dict[str, float]:
        """
        Calculate total EVC with complete breakdown.

        Args:
            differentiation_level: Level of performance differentiation
                - 'low': 5-10% premium
                - 'medium': 15-25% premium (default)
                - 'high': 30-50% premium

        Returns:
            Dictionary containing:
                - time_savings: Value from time saved
                - error_reduction: Value from errors prevented
                - revenue_increase: Value from additional revenue
                - risk_reduction: Value from risk mitigation
                - subtotal: Sum of all components
                - performance_premium_pct: Premium percentage applied
                - performance_premium: Premium dollar amount
                - total_evc: Final EVC including premium

        Example:
            >>> calc = EVCCalculator()
            >>> calc.add_time_savings(hours_saved=10, hourly_rate=75)
            >>> result = calc.calculate_total_evc(differentiation_level='low')
            >>> result['time_savings']
            750.0
            >>> result['subtotal']
            750.0
            >>> result['total_evc'] > 750.0
            True
        """
        # Calculate subtotal from all components
        subtotal = sum(self.components.values())

        # Calculate performance premium
        if subtotal > 0:
            premium_info = self.calculate_performance_premium(
                base_evc=subtotal,
                differentiation_level=differentiation_level
            )
            premium_pct = premium_info['premium_percentage']
            premium_amount = premium_info['premium_amount']
        else:
            premium_pct = 0.0
            premium_amount = 0.0

        # Calculate total EVC
        total_evc = subtotal + premium_amount

        return {
            'time_savings': self.components['time_savings'],
            'error_reduction': self.components['error_reduction'],
            'revenue_increase': self.components['revenue_increase'],
            'risk_reduction': self.components['risk_reduction'],
            'subtotal': subtotal,
            'performance_premium_pct': premium_pct,
            'performance_premium': premium_amount,
            'total_evc': total_evc
        }

    def get_component_breakdown(self) -> Dict[str, Dict[str, float]]:
        """
        Get detailed breakdown of each component's contribution.

        Returns:
            Dictionary mapping component name to percentage and value

        Example:
            >>> calc = EVCCalculator()
            >>> calc.add_time_savings(hours_saved=10, hourly_rate=75)
            >>> calc.add_error_reduction(errors_avoided=1, cost_per_error=250)
            >>> breakdown = calc.get_component_breakdown()
            >>> breakdown['time_savings']['percentage']
            75.0
            >>> breakdown['error_reduction']['percentage']
            25.0
        """
        subtotal = sum(self.components.values())

        if subtotal == 0:
            return {
                name: {'value': 0.0, 'percentage': 0.0}
                for name in self.components.keys()
            }

        breakdown = {}
        for name, value in self.components.items():
            percentage = (value / subtotal) * 100
            breakdown[name] = {
                'value': value,
                'percentage': percentage
            }

        return breakdown

    def reset(self) -> None:
        """Reset all components to zero."""
        self.components = {
            'time_savings': 0.0,
            'error_reduction': 0.0,
            'revenue_increase': 0.0,
            'risk_reduction': 0.0
        }


if __name__ == "__main__":  # pragma: no cover
    print("EVC Calculator - Example Usage")
    print("=" * 60)

    # Example 1: Team coverage tool
    print("\nExample 1: Team Coverage Tool")
    print("-" * 60)

    calc = EVCCalculator()

    # Time savings from automated monitoring
    calc.add_time_savings(hours_saved=40, hourly_rate=75)
    print("Time Savings: 40 hours/month × $75/hour = $3,000/month")

    # Error reduction from preventing coverage gaps
    calc.add_error_reduction(errors_avoided=2, cost_per_error=4000)
    print("Error Reduction: 2 errors/month × $4,000/error = $8,000/month")

    # Risk reduction from avoiding SLA penalties
    calc.add_risk_reduction(probability=0.05, impact=50000)
    print("Risk Reduction: 5% chance × $50,000 penalty = $2,500/month")

    # Calculate total EVC with medium differentiation
    result = calc.calculate_total_evc(differentiation_level='medium')

    print("\nEVC Breakdown:")
    print(f"  Time Savings:        ${result['time_savings']:>10,.2f}")
    print(f"  Error Reduction:     ${result['error_reduction']:>10,.2f}")
    print(f"  Revenue Increase:    ${result['revenue_increase']:>10,.2f}")
    print(f"  Risk Reduction:      ${result['risk_reduction']:>10,.2f}")
    print("  " + "-" * 35)
    print(f"  Subtotal:            ${result['subtotal']:>10,.2f}")
    print(f"  Performance Premium ({result['performance_premium_pct']:.0%}): ${result['performance_premium']:>10,.2f}")
    print("  " + "=" * 35)
    print(f"  Total EVC:           ${result['total_evc']:>10,.2f}/month")

    # Component breakdown
    breakdown = calc.get_component_breakdown()
    print("\nComponent Contribution:")
    for component, info in breakdown.items():
        if info['value'] > 0:
            print(f"  {component.replace('_', ' ').title()}: {info['percentage']:.1f}%")

    # Example 2: Compare differentiation levels
    print("\n\nExample 2: Differentiation Level Comparison")
    print("-" * 60)

    calc2 = EVCCalculator()
    calc2.add_time_savings(hours_saved=100, hourly_rate=75)

    for level in ['low', 'medium', 'high']:
        result = calc2.calculate_total_evc(differentiation_level=level)
        print(f"\n{level.capitalize()} Differentiation:")
        print(f"  Base Value:          ${result['subtotal']:>10,.2f}")
        print(f"  Premium ({result['performance_premium_pct']:.0%}):      ${result['performance_premium']:>10,.2f}")
        print(f"  Total EVC:           ${result['total_evc']:>10,.2f}")

    # Example 3: Multiple value sources
    print("\n\nExample 3: Navigation App")
    print("-" * 60)

    calc3 = EVCCalculator()

    # Commuter uses app daily
    calc3.add_time_savings(hours_saved=15, hourly_rate=50)  # 30 min/day × 30 days
    print("Time Savings: 15 hours/month × $50/hour = $750/month")

    # Prevents late arrivals (lost opportunities, penalties)
    calc3.add_error_reduction(errors_avoided=0.5, cost_per_error=200)
    print("Error Reduction: 0.5 late arrivals/month × $200/arrival = $100/month")

    # Reduces fuel consumption
    calc3.add_revenue_increase(additional_revenue=50)  # Fuel savings
    print("Fuel Savings: $50/month")

    # Prevents accidents from getting lost
    calc3.add_risk_reduction(probability=0.001, impact=5000)
    print("Risk Reduction: 0.1% chance × $5,000 accident = $5/month")

    result3 = calc3.calculate_total_evc(differentiation_level='medium')

    print(f"\nTotal EVC: ${result3['total_evc']:,.2f}/month")
    print(f"Annual EVC: ${result3['total_evc'] * 12:,.2f}/year")

    print("\n" + "=" * 60)
    print("Examples complete!")
