"""
Financial health scoring with 4-dimension framework.

Scoring dimensions (total 100 points):
- Liquidity: 30 points (current ratio, OCF, working capital)
- Profitability: 25 points (margins, ROE, ROA)
- Leverage: 25 points (debt ratios, coverage)
- Growth: 20 points (revenue, earnings growth)

Gate decisions:
- GO: >= 75 points
- CONDITIONAL: 50-74 points
- NO_GO: < 50 points
"""

from decimal import Decimal

from .types import HealthScoringMetrics, FinancialHealth
from corporate_development.core.phase import PhaseGate
from corporate_development.core.constants import FINANCIAL_GO_THRESHOLD, FINANCIAL_CONDITIONAL_THRESHOLD


class HealthScorer:
    """Calculate financial health score across 4 dimensions."""

    # Gate thresholds (deterministic rules) — kept as Decimal for score comparison
    GO_THRESHOLD = Decimal(str(FINANCIAL_GO_THRESHOLD))
    CONDITIONAL_THRESHOLD = Decimal(str(FINANCIAL_CONDITIONAL_THRESHOLD))

    def calculate_health(self, metrics: HealthScoringMetrics) -> FinancialHealth:
        """
        Calculate financial health score.

        Args:
            metrics: Financial metrics

        Returns:
            FinancialHealth with dimension scores and gate decision
        """
        # Calculate dimension scores
        liquidity_score = self._calculate_liquidity_score(metrics)
        profitability_score = self._calculate_profitability_score(metrics)
        leverage_score = self._calculate_leverage_score(metrics)
        growth_score = self._calculate_growth_score(metrics)

        # Calculate total score
        total_score = (
            liquidity_score + profitability_score + leverage_score + growth_score
        )

        # Determine gate decision
        gate_decision = self._determine_gate(total_score)

        return FinancialHealth(
            liquidity_score=liquidity_score,
            profitability_score=profitability_score,
            leverage_score=leverage_score,
            growth_score=growth_score,
            total_score=total_score,
            gate_decision=gate_decision,
        )

    def _calculate_liquidity_score(self, metrics: HealthScoringMetrics) -> Decimal:
        """
        Calculate liquidity score (0-30 points).

        Components:
        - Current ratio: 0-10 points
        - Operating cash flow ratio: 0-10 points
        - Working capital ratio: 0-10 points

        Current ratio thresholds:
        - >= 2.0: 10 points (Excellent)
        - 1.5-2.0: 8 points (Good)
        - 1.2-1.5: 6 points (Adequate)
        - 1.0-1.2: 4 points (Tight)
        - < 1.0: 0 points (Crisis)
        """
        score = Decimal("0")

        # Current ratio scoring
        if metrics.current_liabilities > 0:
            current_ratio = metrics.current_assets / metrics.current_liabilities

            if current_ratio >= Decimal("2.0"):
                score += Decimal("10")  # Excellent
            elif current_ratio >= Decimal("1.5"):
                score += Decimal("8")  # Good
            elif current_ratio >= Decimal("1.2"):
                score += Decimal("6")  # Adequate
            elif current_ratio >= Decimal("1.0"):
                score += Decimal("4")  # Tight
            else:
                score += Decimal("0")  # Crisis

        # OCF ratio scoring - only award points if current ratio >= 1.0
        # This prevents "gaming" the score with strong OCF but weak balance sheet
        if metrics.current_liabilities > 0:
            current_ratio = metrics.current_assets / metrics.current_liabilities
            if current_ratio >= Decimal("1.0") and metrics.operating_cash_flow > 0:
                ocf_to_current_liabilities = (
                    metrics.operating_cash_flow / metrics.current_liabilities
                )
                if ocf_to_current_liabilities >= Decimal("0.4"):
                    score += Decimal("10")  # Strong
                elif ocf_to_current_liabilities >= Decimal("0.25"):
                    score += Decimal("8")  # Good
                elif ocf_to_current_liabilities >= Decimal("0.15"):
                    score += Decimal("6")  # Adequate
                elif ocf_to_current_liabilities >= Decimal("0.1"):
                    score += Decimal("4")  # Tight
                else:
                    score += Decimal("2")  # Weak

        # Working capital ratio scoring - only if WC is positive
        working_capital = metrics.current_assets - metrics.current_liabilities
        if working_capital > 0:
            wc_ratio = working_capital / metrics.total_assets
            if wc_ratio >= Decimal("0.3"):
                score += Decimal("10")  # Strong
            elif wc_ratio >= Decimal("0.2"):
                score += Decimal("8")  # Good
            elif wc_ratio >= Decimal("0.1"):
                score += Decimal("6")  # Adequate
            elif wc_ratio >= Decimal("0.05"):
                score += Decimal("4")  # Tight
            else:
                score += Decimal("2")  # Weak

        return score

    def _calculate_profitability_score(self, metrics: HealthScoringMetrics) -> Decimal:
        """
        Calculate profitability score (0-25 points).

        Components:
        - Net margin: 0-15 points
        - Operating efficiency: 0-10 points (placeholder)
        """
        score = Decimal("0")

        if metrics.revenue > 0:
            # Net margin scoring (0-15 points)
            net_margin = metrics.net_income / metrics.revenue
            if net_margin >= Decimal("0.15"):
                score += Decimal("15")  # Excellent (15%+)
            elif net_margin >= Decimal("0.12"):
                score += Decimal("13")  # Strong (12-15%)
            elif net_margin >= Decimal("0.10"):
                score += Decimal("11")  # Good (10-12%)
            elif net_margin >= Decimal("0.07"):
                score += Decimal("9")  # Adequate (7-10%)
            elif net_margin >= Decimal("0.05"):
                score += Decimal("6")  # Marginal (5-7%)
            elif net_margin > Decimal("0"):
                score += Decimal("3")  # Weak but positive
            else:
                score += Decimal("0")  # Unprofitable

            # Operating efficiency (0-10 points) - placeholder
            # Use operating expenses as % of revenue
            if metrics.revenue > 0:
                opex_ratio = metrics.operating_expenses / metrics.revenue
                if opex_ratio <= Decimal("0.15"):
                    score += Decimal("10")  # Very efficient (<15%)
                elif opex_ratio <= Decimal("0.20"):
                    score += Decimal("8")  # Efficient (15-20%)
                elif opex_ratio <= Decimal("0.25"):
                    score += Decimal("6")  # Acceptable (20-25%)
                elif opex_ratio <= Decimal("0.30"):
                    score += Decimal("4")  # High (25-30%)
                else:
                    score += Decimal("2")  # Very high (>30%)

        return score

    def _calculate_leverage_score(self, metrics: HealthScoringMetrics) -> Decimal:
        """
        Calculate leverage score (0-25 points).

        Placeholder implementation - will expand in later phases.
        """
        # Placeholder: Award points based on debt-to-equity ratio
        score = Decimal("0")

        if metrics.total_assets > 0:
            equity = metrics.total_assets - metrics.total_liabilities
            if equity > 0:
                debt_to_equity = metrics.total_liabilities / equity

                if debt_to_equity <= Decimal("0.5"):
                    score = Decimal("25")  # Conservative
                elif debt_to_equity <= Decimal("1.0"):
                    score = Decimal("20")  # Moderate
                elif debt_to_equity <= Decimal("2.0"):
                    score = Decimal("15")  # Elevated
                elif debt_to_equity <= Decimal("3.0"):
                    score = Decimal("10")  # High
                else:
                    score = Decimal("5")  # Very high

        return score

    def _calculate_growth_score(self, metrics: HealthScoringMetrics) -> Decimal:
        """
        Calculate growth score (0-20 points).

        Placeholder implementation - will expand in later phases.
        """
        # Placeholder: Award points based on revenue growth
        score = Decimal("0")

        if metrics.prior_year_revenue > 0:
            revenue_growth = (
                (metrics.revenue - metrics.prior_year_revenue)
                / metrics.prior_year_revenue
            )

            if revenue_growth >= Decimal("0.3"):
                score = Decimal("20")  # Exceptional
            elif revenue_growth >= Decimal("0.2"):
                score = Decimal("17")  # Strong
            elif revenue_growth >= Decimal("0.1"):
                score = Decimal("14")  # Good
            elif revenue_growth >= Decimal("0.05"):
                score = Decimal("11")  # Moderate
            elif revenue_growth >= Decimal("0"):
                score = Decimal("8")  # Stable
            else:
                score = Decimal("3")  # Declining

        return score

    def _determine_gate(self, total_score: Decimal) -> PhaseGate:
        """
        Determine gate decision based on total score.

        Args:
            total_score: Total health score (0-100)

        Returns:
            Gate decision (GO, CONDITIONAL, or NO_GO)
        """
        if total_score >= self.GO_THRESHOLD:
            return PhaseGate.GO
        elif total_score >= self.CONDITIONAL_THRESHOLD:
            return PhaseGate.CONDITIONAL
        else:
            return PhaseGate.NO_GO
