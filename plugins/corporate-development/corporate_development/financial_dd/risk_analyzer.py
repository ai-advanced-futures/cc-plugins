"""
Risk analyzer for financial due diligence.

Detects red flags and calculates overall risk scores based on financial metrics.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from corporate_development.financial_dd.types import (
    RiskAnalysis,
    RiskLevel,
    RedFlag,
    FinancialRiskSeverity,
    BalanceSheet,
    IncomeStatement,
)


class RiskAnalyzer:
    """
    Analyzer for financial red flags and risk assessment.

    Uses weighted scoring across multiple dimensions:
    - Liquidity risks (30% weight)
    - Profitability risks (25% weight)
    - Leverage risks (25% weight)
    - Growth/sustainability risks (20% weight)
    """

    # Risk score thresholds (lower score = higher risk)
    RISK_THRESHOLDS = {
        "high": 50,      # < 50 = HIGH risk
        "medium": 75,    # 50-74 = MEDIUM risk
        # >= 75 = LOW risk
    }

    # Category weights for overall risk score
    CATEGORY_WEIGHTS = {
        "liquidity": 0.30,
        "profitability": 0.25,
        "leverage": 0.25,
        "growth": 0.20,
    }

    # Severity weights for risk score calculation
    CRITICAL_WEIGHT = 30
    WARNING_WEIGHT = 10
    INFO_WEIGHT = 3

    # Risk level thresholds
    LOW_THRESHOLD = 25
    MEDIUM_THRESHOLD = 50
    HIGH_THRESHOLD = 75

    def __init__(self):
        """Initialize the risk analyzer."""
        pass

    def _calculate_risk_score(self, red_flags: List[RedFlag]) -> int:
        """
        Calculate risk score based on red flags.

        Weighted scoring:
        - CRITICAL: 30 points
        - WARNING: 10 points
        - INFO: 3 points

        Args:
            red_flags: List of identified red flags

        Returns:
            Risk score (0-100, capped at 100)
        """
        if not red_flags:
            return 0

        total_score = 0
        for flag in red_flags:
            if flag.severity == FinancialRiskSeverity.CRITICAL:
                total_score += self.CRITICAL_WEIGHT
            elif flag.severity == FinancialRiskSeverity.WARNING:
                total_score += self.WARNING_WEIGHT
            elif flag.severity == FinancialRiskSeverity.INFO:
                total_score += self.INFO_WEIGHT

        # Cap at 100
        return min(total_score, 100)

    def _determine_risk_level(self, score: int) -> RiskLevel:
        """
        Determine risk level based on risk score.

        Thresholds:
        - 0-25: LOW risk
        - 26-50: MEDIUM risk
        - 51+: HIGH risk

        Args:
            score: Risk score (0-100)

        Returns:
            RiskLevel enum value
        """
        if score <= self.LOW_THRESHOLD:
            return RiskLevel.LOW
        elif score <= self.MEDIUM_THRESHOLD:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    # ============================================================================
    # CRITICAL Red Flag Detectors
    # ============================================================================

    def _detect_negative_working_capital(self, balance_sheet: BalanceSheet) -> Optional[RedFlag]:
        """
        Detect negative working capital (CRITICAL).

        Working capital = Current Assets - Current Liabilities
        Negative WC indicates liquidity crisis.

        Args:
            balance_sheet: Latest balance sheet

        Returns:
            RedFlag if WC < 0, None otherwise
        """
        wc = balance_sheet.working_capital

        if wc < 0:
            return RedFlag(
                severity=FinancialRiskSeverity.CRITICAL,
                category="liquidity",
                description=f"Negative working capital of ${abs(float(wc)):,.2f}",
                value=float(wc),
                threshold=0.0
            )

        return None

    def _detect_over_leveraged(self, balance_sheet: BalanceSheet) -> Optional[RedFlag]:
        """
        Detect over-leveraged company (CRITICAL).

        Debt-to-Equity > 3.0 indicates dangerous leverage.
        Also handles negative equity (instant red flag).

        Args:
            balance_sheet: Latest balance sheet

        Returns:
            RedFlag if Debt/Equity > 3.0 or equity <= 0, None otherwise
        """
        total_debt = balance_sheet.current_debt + balance_sheet.long_term_debt
        equity = balance_sheet.equity

        # Negative or zero equity is automatic red flag
        if equity <= 0:
            return RedFlag(
                severity=FinancialRiskSeverity.CRITICAL,
                category="leverage",
                description="Negative or zero equity - company is insolvent",
                value=float(equity),
                threshold=0.0
            )

        debt_to_equity = float(total_debt) / float(equity)

        if debt_to_equity > 3.0:
            return RedFlag(
                severity=FinancialRiskSeverity.CRITICAL,
                category="leverage",
                description=f"Debt-to-equity ratio of {debt_to_equity:.2f}x exceeds 3.0x threshold",
                value=debt_to_equity,
                threshold=3.0
            )

        return None

    def _detect_liquidity_crisis(self, balance_sheet: BalanceSheet) -> Optional[RedFlag]:
        """
        Detect liquidity crisis (CRITICAL).

        Current Ratio < 0.8 indicates severe liquidity problems.

        Args:
            balance_sheet: Latest balance sheet

        Returns:
            RedFlag if current ratio < 0.8, None otherwise
        """
        current_ratio = balance_sheet.current_ratio

        if current_ratio < Decimal("0.8"):
            return RedFlag(
                severity=FinancialRiskSeverity.CRITICAL,
                category="liquidity",
                description=f"Current ratio of {float(current_ratio):.2f} below 0.8 threshold",
                value=float(current_ratio),
                threshold=0.8
            )

        return None

    def _detect_negative_ebitda(self, income_statement: IncomeStatement) -> Optional[RedFlag]:
        """
        Detect negative EBITDA (CRITICAL).

        EBITDA < 0 indicates fundamental profitability problems.

        Args:
            income_statement: Latest income statement

        Returns:
            RedFlag if EBITDA < 0, None otherwise
        """
        # Calculate net income
        net_income = (
            income_statement.revenue
            - income_statement.cogs
            - income_statement.operating_expenses
            - income_statement.interest_expense
            - income_statement.tax_expense
        )

        # Add back interest, taxes, depreciation, amortization
        ebitda = net_income + income_statement.interest_expense + income_statement.tax_expense

        if income_statement.depreciation:
            ebitda += income_statement.depreciation
        if income_statement.amortization:
            ebitda += income_statement.amortization

        if ebitda < 0:
            return RedFlag(
                severity=FinancialRiskSeverity.CRITICAL,
                category="profitability",
                description=f"Negative EBITDA of ${abs(float(ebitda)):,.2f}",
                value=float(ebitda),
                threshold=0.0
            )

        return None

    def _detect_severe_revenue_decline(
        self,
        current_income: IncomeStatement,
        prior_income: IncomeStatement
    ) -> Optional[RedFlag]:
        """
        Detect severe revenue decline (CRITICAL).

        Revenue decline > 20% YoY indicates serious business problems.

        Args:
            current_income: Current period income statement
            prior_income: Prior period income statement

        Returns:
            RedFlag if revenue decline > 20%, None otherwise
        """
        if prior_income.revenue == 0:
            return None  # Can't calculate if no prior revenue

        revenue_change = (
            (float(current_income.revenue) - float(prior_income.revenue))
            / float(prior_income.revenue)
            * 100
        )

        if revenue_change < -20:
            return RedFlag(
                severity=FinancialRiskSeverity.CRITICAL,
                category="growth",
                description=f"Revenue decline of {abs(revenue_change):.1f}% exceeds 20% threshold",
                value=revenue_change,
                threshold=-20.0
            )

        return None

    # ============================================================================
    # WARNING Red Flag Detectors
    # ============================================================================

    def _detect_working_capital_deterioration(
        self,
        current_balance: BalanceSheet,
        prior_balance: BalanceSheet
    ) -> Optional[RedFlag]:
        """
        Detect working capital deterioration (WARNING).

        Working capital decline > 15% YoY indicates liquidity concerns.

        Args:
            current_balance: Current period balance sheet
            prior_balance: Prior period balance sheet

        Returns:
            RedFlag if WC decline > 15%, None otherwise
        """
        current_wc = current_balance.working_capital
        prior_wc = prior_balance.working_capital

        # Can't calculate if prior WC is zero or negative
        if prior_wc <= 0:
            return None

        wc_change_pct = (
            (float(current_wc) - float(prior_wc)) / float(prior_wc) * 100
        )

        if wc_change_pct < -15:
            return RedFlag(
                severity=FinancialRiskSeverity.WARNING,
                category="liquidity",
                description=f"Working capital declined {abs(wc_change_pct):.1f}% YoY",
                value=wc_change_pct,
                threshold=-15.0
            )

        return None

    def _detect_margin_compression(
        self,
        current_income: IncomeStatement,
        prior_income: IncomeStatement
    ) -> Optional[RedFlag]:
        """
        Detect gross margin compression (WARNING).

        Gross margin decline > 5 percentage points YoY indicates pricing pressure.

        Args:
            current_income: Current period income statement
            prior_income: Prior period income statement

        Returns:
            RedFlag if margin decline > 5pp, None otherwise
        """
        # Can't calculate if no revenue
        if prior_income.revenue == 0 or current_income.revenue == 0:
            return None

        # Calculate gross margins (percentage)
        prior_margin = (
            (float(prior_income.revenue) - float(prior_income.cogs))
            / float(prior_income.revenue)
            * 100
        )

        current_margin = (
            (float(current_income.revenue) - float(current_income.cogs))
            / float(current_income.revenue)
            * 100
        )

        margin_change = current_margin - prior_margin

        if margin_change < -5:
            return RedFlag(
                severity=FinancialRiskSeverity.WARNING,
                category="profitability",
                description=f"Gross margin compressed {abs(margin_change):.1f}pp YoY",
                value=margin_change,
                threshold=-5.0
            )

        return None

    def _detect_tight_liquidity(self, balance_sheet: BalanceSheet) -> Optional[RedFlag]:
        """
        Detect tight liquidity position (WARNING).

        Current ratio between 0.8 and 1.2 indicates marginal liquidity.

        Args:
            balance_sheet: Latest balance sheet

        Returns:
            RedFlag if 0.8 <= current ratio < 1.2, None otherwise
        """
        current_ratio = balance_sheet.current_ratio

        if Decimal("0.8") <= current_ratio < Decimal("1.2"):
            return RedFlag(
                severity=FinancialRiskSeverity.WARNING,
                category="liquidity",
                description=f"Current ratio of {float(current_ratio):.2f} in danger zone (0.8-1.2)",
                value=float(current_ratio),
                threshold=1.2
            )

        return None

    def analyze_risks(self, statements: Dict[str, Any]) -> RiskAnalysis:
        """
        Analyze financial statements for red flags and calculate risk score.

        Implements data validation and graceful degradation:
        - No data: Returns "insufficient" analysis with no flags
        - Single period: Runs snapshot-only flags (4 flags)
        - Multi-period: Runs all flags including YoY comparisons (14 flags)

        Args:
            statements: Dictionary containing:
                - income_statements: List[IncomeStatement]
                - balance_sheets: List[BalanceSheet]
                - cash_flow_statements: List[CashFlowStatement]

        Returns:
            RiskAnalysis with red flags, risk score, and risk level
        """
        income_statements = statements.get("income_statements", [])
        balance_sheets = statements.get("balance_sheets", [])

        # ============================================================================
        # Data Validation: Check for minimum data requirements
        # ============================================================================

        # Case 1: No data available
        if not income_statements and not balance_sheets:
            return RiskAnalysis(
                overall_risk_level=RiskLevel.LOW,
                risk_score=0,
                red_flags=[],
                summary="Insufficient data for risk analysis",
                data_completeness="insufficient",
                flags_detected=0,
                recommendations=[]
            )

        # ============================================================================
        # Data Preparation: Sort statements by period (most recent first)
        # ============================================================================

        # Sort income statements by period_end (most recent first)
        sorted_income = sorted(
            income_statements,
            key=lambda x: x.period_end,
            reverse=True
        ) if income_statements else []

        # Sort balance sheets by as_of_date (most recent first)
        sorted_balance = sorted(
            balance_sheets,
            key=lambda x: x.as_of_date,
            reverse=True
        ) if balance_sheets else []

        # ============================================================================
        # Determine Data Completeness: Single period or multi-period?
        # ============================================================================

        has_multi_period_income = len(sorted_income) >= 2
        has_multi_period_balance = len(sorted_balance) >= 2
        has_multi_period = has_multi_period_income and has_multi_period_balance

        red_flags: List[RedFlag] = []
        flags_checked = 0

        # ============================================================================
        # Snapshot Analysis: Run point-in-time flag detectors (always run)
        # ============================================================================

        # Requires at least one balance sheet and one income statement
        if sorted_balance and sorted_income:
            latest_balance = sorted_balance[0]
            latest_income = sorted_income[0]

            # CRITICAL snapshot flags (4 total)
            flag = self._detect_negative_working_capital(latest_balance)
            flags_checked += 1
            if flag:
                red_flags.append(flag)

            flag = self._detect_over_leveraged(latest_balance)
            flags_checked += 1
            if flag:
                red_flags.append(flag)

            flag = self._detect_liquidity_crisis(latest_balance)
            flags_checked += 1
            if flag:
                red_flags.append(flag)

            flag = self._detect_negative_ebitda(latest_income)
            flags_checked += 1
            if flag:
                red_flags.append(flag)

        # ============================================================================
        # Year-over-Year Analysis: Run trend-based detectors (only if multi-period)
        # ============================================================================

        if has_multi_period:
            # We have at least 2 periods for both income and balance sheets
            current_income = sorted_income[0]
            prior_income = sorted_income[1]
            current_balance = sorted_balance[0]
            prior_balance = sorted_balance[1]

            # CRITICAL YoY flags
            flag = self._detect_severe_revenue_decline(current_income, prior_income)
            flags_checked += 1
            if flag:
                red_flags.append(flag)

            # WARNING YoY flags
            flag = self._detect_working_capital_deterioration(current_balance, prior_balance)
            flags_checked += 1
            if flag:
                red_flags.append(flag)

            flag = self._detect_margin_compression(current_income, prior_income)
            flags_checked += 1
            if flag:
                red_flags.append(flag)

            flag = self._detect_tight_liquidity(current_balance)
            flags_checked += 1
            if flag:
                red_flags.append(flag)

        # ============================================================================
        # Limited Data Notification: Add informational flag if single period only
        # ============================================================================

        data_completeness = "full"
        if not has_multi_period and (sorted_balance or sorted_income):
            # We have data but only single period
            data_completeness = "limited"
            red_flags.append(
                RedFlag(
                    severity=FinancialRiskSeverity.INFO,
                    category="data_quality",
                    description="Limited to single-period analysis - trend detection unavailable",
                    value=1.0,
                    threshold=2.0
                )
            )

        # ============================================================================
        # Risk Scoring: Calculate overall risk score and level
        # ============================================================================

        risk_score = self._calculate_risk_score(red_flags)
        risk_level = self._determine_risk_level(risk_score)

        # ============================================================================
        # Recommendations: Build actionable recommendations from CRITICAL/WARNING flags
        # ============================================================================

        recommendations = []
        critical_flags = [f for f in red_flags if f.severity == FinancialRiskSeverity.CRITICAL]
        warning_flags = [f for f in red_flags if f.severity == FinancialRiskSeverity.WARNING]

        if critical_flags:
            recommendations.append("Address critical issues immediately - these are potential deal-breakers")
            for flag in critical_flags:
                if "working capital" in flag.description.lower() and flag.value < 0:
                    recommendations.append("Improve liquidity position - consider reducing current liabilities or increasing current assets")
                elif "debt-to-equity" in flag.description.lower():
                    recommendations.append("Reduce leverage - consider debt restructuring or equity injection")
                elif "current ratio" in flag.description.lower() and flag.value < 0.8:
                    recommendations.append("Shore up short-term liquidity - may need working capital loan or asset sales")
                elif "ebitda" in flag.description.lower() and flag.value < 0:
                    recommendations.append("Restore profitability - review cost structure and revenue generation")
                elif "revenue decline" in flag.description.lower():
                    recommendations.append("Investigate revenue decline - assess market position and competitive threats")

        if warning_flags:
            recommendations.append("Monitor warning indicators closely - trends may worsen")
            for flag in warning_flags:
                if "working capital" in flag.description.lower():
                    recommendations.append("Watch working capital trends - early intervention may prevent crisis")
                elif "margin" in flag.description.lower():
                    recommendations.append("Address margin compression - evaluate pricing power and cost management")
                elif "liquidity" in flag.description.lower():
                    recommendations.append("Build liquidity cushion - maintain adequate current ratio buffer")

        # ============================================================================
        # Summary: Generate executive summary
        # ============================================================================

        summary_parts = []
        if risk_level == RiskLevel.HIGH:
            summary_parts.append(f"HIGH RISK: {len(critical_flags)} critical issues identified")
        elif risk_level == RiskLevel.MEDIUM:
            summary_parts.append(f"MEDIUM RISK: {len(warning_flags)} warnings require attention")
        else:
            summary_parts.append("LOW RISK: Financial position appears stable")

        if data_completeness == "limited":
            summary_parts.append("(Limited to single-period analysis)")

        summary = " ".join(summary_parts)

        # ============================================================================
        # Return Complete Analysis
        # ============================================================================

        return RiskAnalysis(
            overall_risk_level=risk_level,
            risk_score=risk_score,
            red_flags=red_flags,
            summary=summary,
            data_completeness=data_completeness,
            flags_detected=flags_checked,
            recommendations=recommendations
        )
