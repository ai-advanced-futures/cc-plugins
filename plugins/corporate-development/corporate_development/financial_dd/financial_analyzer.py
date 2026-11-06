"""Financial statement analyzer for reconciliation and accounting basis detection."""

from decimal import Decimal
from typing import Optional, List

from .types import (
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    ReconciliationIssue,
    BasisDetectionResult,
    FinancialAnalysisResult,
    AccountingBasis,
    Confidence,
    FinancialRiskSeverity,
)


class FinancialAnalyzer:
    """Analyzer for financial statement relationships and accounting basis."""

    def __init__(self):
        """Initialize the financial analyzer."""
        # Materiality thresholds (will be configurable in future)
        self.materiality_percentage = Decimal("0.05")  # 5%
        self.materiality_absolute = Decimal("10000")  # $10k

    def analyze(
        self,
        income_statement: IncomeStatement,
        balance_sheet: BalanceSheet,
        cash_flow_statement: Optional[CashFlowStatement] = None,
        prior_balance_sheet: Optional[BalanceSheet] = None,
    ) -> FinancialAnalysisResult:
        """
        Analyze financial statements for consistency and detect accounting basis.

        Args:
            income_statement: Current period income statement
            balance_sheet: Current period balance sheet
            cash_flow_statement: Optional cash flow statement
            prior_balance_sheet: Optional prior period balance sheet for comparisons

        Returns:
            FinancialAnalysisResult with detected basis and reconciliation issues
        """
        # Detect accounting basis
        basis_result = self.detect_accounting_basis(
            income_statement, balance_sheet, cash_flow_statement
        )

        # Run all validators
        issues: List[ReconciliationIssue] = []
        issues.extend(self._validate_balance_sheet_equation(balance_sheet))
        issues.extend(self._validate_data_quality(balance_sheet))

        if prior_balance_sheet:
            issues.extend(self._validate_cash_decline(balance_sheet, prior_balance_sheet))

        if cash_flow_statement:
            issues.extend(
                self._validate_cash_flow_reconciliation(
                    cash_flow_statement, balance_sheet, prior_balance_sheet
                )
            )
            issues.extend(
                self._validate_income_to_equity(
                    income_statement, balance_sheet, prior_balance_sheet, cash_flow_statement
                )
            )

        issues.extend(self._validate_line_item_reasonableness(income_statement, balance_sheet))

        # Tally severity counts
        critical_count = sum(1 for issue in issues if issue.severity == FinancialRiskSeverity.CRITICAL)
        warning_count = sum(1 for issue in issues if issue.severity == FinancialRiskSeverity.WARNING)
        info_count = sum(1 for issue in issues if issue.severity == FinancialRiskSeverity.INFO)

        # Determine overall quality
        if critical_count > 0:
            overall_quality = "POOR"
            is_validated = False
        elif warning_count >= 3:
            overall_quality = "FAIR"
            is_validated = True
        elif warning_count > 0:
            overall_quality = "GOOD"
            is_validated = True
        else:
            overall_quality = "EXCELLENT"
            is_validated = True

        # Build summary
        summary = self._build_summary(
            critical_count, warning_count, info_count, overall_quality
        )

        return FinancialAnalysisResult(
            accounting_basis=basis_result,
            reconciliation_issues=issues,
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            overall_quality=overall_quality,
            is_validated=is_validated,
            summary=summary,
        )

    def detect_accounting_basis(
        self,
        income_statement: IncomeStatement,
        balance_sheet: BalanceSheet,
        cash_flow_statement: Optional[CashFlowStatement] = None,
    ) -> BasisDetectionResult:
        """
        Detect accounting basis using 4 key indicators.

        Indicators:
        1. Accounts Receivable (>= 5% of revenue)
        2. Accounts Payable (present and material)
        3. Depreciation expense (>= 1% of revenue)
        4. Accrual accounts (accrued expenses, prepaid, deferred)

        Confidence levels:
        - HIGH: 4 indicators (accrual) or 0 indicators (cash)
        - MEDIUM: 2-3 indicators (modified cash)
        - LOW: Insufficient data

        Returns:
            BasisDetectionResult with detected basis, confidence, and reasoning
        """
        # Check for insufficient data
        if income_statement.revenue == 0:
            return BasisDetectionResult(
                detected_basis=AccountingBasis.CASH,
                confidence=Confidence.LOW,
                indicators={
                    "has_accounts_receivable": False,
                    "has_accounts_payable": False,
                    "has_depreciation": False,
                    "has_accrual_accounts": False,
                },
                reasoning="Insufficient data (zero revenue) - defaulting to CASH basis with LOW confidence",
            )

        # Indicator 1: Accounts Receivable >= 5% of revenue
        ar_threshold = income_statement.revenue * Decimal("0.05")
        has_ar = balance_sheet.accounts_receivable >= ar_threshold

        # Indicator 2: Accounts Payable present and material
        # Material means > 0 (any AP suggests accrual)
        has_ap = balance_sheet.accounts_payable > 0

        # Indicator 3: Depreciation >= 1% of revenue
        depreciation = income_statement.depreciation or Decimal("0")
        amortization = income_statement.amortization or Decimal("0")
        total_da = depreciation + amortization
        da_threshold = income_statement.revenue * Decimal("0.01")
        has_da = total_da >= da_threshold

        # Indicator 4: Accrual accounts present (accrued expenses)
        # Material means > 0
        has_accruals = balance_sheet.accrued_expenses > 0

        # Store indicators
        indicators = {
            "has_accounts_receivable": has_ar,
            "has_accounts_payable": has_ap,
            "has_depreciation": has_da,
            "has_accrual_accounts": has_accruals,
        }

        # Count indicators
        indicator_count = sum(indicators.values())

        # Determine basis and confidence
        if indicator_count == 4:
            detected_basis = AccountingBasis.ACCRUAL
            confidence = Confidence.HIGH
            reasoning = "All 4 accrual indicators present (AR, AP, depreciation, accruals) - HIGH confidence ACCRUAL basis"
        elif indicator_count == 0:
            detected_basis = AccountingBasis.CASH
            confidence = Confidence.HIGH
            reasoning = "No accrual indicators present - HIGH confidence CASH basis"
        elif indicator_count >= 2:
            detected_basis = AccountingBasis.MODIFIED_CASH
            confidence = Confidence.MEDIUM
            reasoning = f"{indicator_count} of 4 indicators present - MEDIUM confidence MODIFIED_CASH basis"
        else:  # indicator_count == 1
            detected_basis = AccountingBasis.MODIFIED_CASH
            confidence = Confidence.LOW
            reasoning = "Only 1 of 4 indicators present - LOW confidence, likely MODIFIED_CASH"

        return BasisDetectionResult(
            detected_basis=detected_basis,
            confidence=confidence,
            indicators=indicators,
            reasoning=reasoning,
        )

    def _validate_balance_sheet_equation(
        self, balance_sheet: BalanceSheet
    ) -> List[ReconciliationIssue]:
        """
        Validate that Assets = Liabilities + Equity.

        Returns:
            List of ReconciliationIssue (empty if balanced)
        """
        # Calculate total assets
        total_assets = (
            balance_sheet.cash
            + balance_sheet.accounts_receivable
            + balance_sheet.inventory
            + balance_sheet.other_current_assets
            + balance_sheet.ppe_net
            + balance_sheet.intangibles
            + balance_sheet.other_assets
        )

        # Calculate total liabilities
        total_liabilities = (
            balance_sheet.accounts_payable
            + balance_sheet.accrued_expenses
            + balance_sheet.current_debt
            + balance_sheet.other_current_liabilities
            + balance_sheet.long_term_debt
            + balance_sheet.other_liabilities
        )

        # Calculate liabilities + equity
        liabilities_plus_equity = total_liabilities + balance_sheet.equity

        # Check if balanced
        difference = total_assets - liabilities_plus_equity

        # If balanced (within rounding), no issues
        if abs(difference) < Decimal("1"):  # Allow $1 rounding
            return []

        # Calculate severity
        severity = self._calculate_severity(difference, total_assets)

        return [
            ReconciliationIssue(
                severity=severity,
                category="balance_sheet",
                title="Balance sheet equation does not balance",
                description=f"Assets ({total_assets:,.2f}) != Liabilities ({total_liabilities:,.2f}) + Equity ({balance_sheet.equity:,.2f}). Difference: {difference:,.2f}",
                expected_value=float(liabilities_plus_equity),
                actual_value=float(total_assets),
                difference=float(difference),
                difference_pct=float((difference / total_assets) * 100) if total_assets != 0 else 0.0,
                recommendation="Review all balance sheet line items for errors or omissions",
            )
        ]

    def _validate_data_quality(
        self, balance_sheet: BalanceSheet
    ) -> List[ReconciliationIssue]:
        """
        Check for negative balances where inappropriate.

        Validates:
        - Cash should not be negative (data error)
        - AR should not be negative (warning)
        - Inventory should not be negative (warning)

        Returns:
            List of ReconciliationIssue (empty if no data quality issues)
        """
        issues = []

        # Check cash (CRITICAL if negative)
        if balance_sheet.cash < 0:
            issues.append(
                ReconciliationIssue(
                    severity=FinancialRiskSeverity.CRITICAL,
                    category="data_quality",
                    title="Negative cash balance",
                    description=f"Cash is negative ({balance_sheet.cash:,.2f}). This is likely a data entry error.",
                    expected_value=0.0,
                    actual_value=float(balance_sheet.cash),
                    difference=float(balance_sheet.cash),
                    difference_pct=100.0,
                    recommendation="Review cash accounts for data entry errors",
                )
            )

        # Check AR (WARNING if negative)
        if balance_sheet.accounts_receivable < 0:
            issues.append(
                ReconciliationIssue(
                    severity=FinancialRiskSeverity.WARNING,
                    category="data_quality",
                    title="Negative accounts receivable",
                    description=f"Accounts receivable is negative ({balance_sheet.accounts_receivable:,.2f}).",
                    expected_value=0.0,
                    actual_value=float(balance_sheet.accounts_receivable),
                    difference=float(balance_sheet.accounts_receivable),
                    difference_pct=100.0,
                    recommendation="Review AR aging and payment applications",
                )
            )

        # Check inventory (WARNING if negative)
        if balance_sheet.inventory < 0:
            issues.append(
                ReconciliationIssue(
                    severity=FinancialRiskSeverity.WARNING,
                    category="data_quality",
                    title="Negative inventory",
                    description=f"Inventory is negative ({balance_sheet.inventory:,.2f}).",
                    expected_value=0.0,
                    actual_value=float(balance_sheet.inventory),
                    difference=float(balance_sheet.inventory),
                    difference_pct=100.0,
                    recommendation="Review inventory records and COGS calculations",
                )
            )

        return issues

    def _validate_cash_decline(
        self, balance_sheet: BalanceSheet, prior_balance_sheet: BalanceSheet
    ) -> List[ReconciliationIssue]:
        """
        Flag significant cash declines (>= 20%).

        Args:
            balance_sheet: Current period balance sheet
            prior_balance_sheet: Prior period balance sheet

        Returns:
            List of ReconciliationIssue (empty if cash stable or increasing)
        """
        current_cash = balance_sheet.cash
        prior_cash = prior_balance_sheet.cash

        # If prior cash was zero or negative, can't calculate decline
        if prior_cash <= 0:
            return []

        # Calculate decline
        decline = prior_cash - current_cash

        # Only flag declines (not increases)
        if decline <= 0:
            return []

        # Calculate percentage decline
        decline_pct = (decline / prior_cash) * Decimal("100")

        # Flag if decline >= 20%
        if decline_pct >= Decimal("20"):
            # Use WARNING severity (significant liquidity concern but not critical)
            return [
                ReconciliationIssue(
                    severity=FinancialRiskSeverity.WARNING,
                    category="liquidity",
                    title=f"Significant cash decline ({decline_pct:.1f}%)",
                    description=f"Cash declined from {prior_cash:,.2f} to {current_cash:,.2f} ({decline_pct:.1f}% decline). This may indicate liquidity stress or operating losses.",
                    expected_value=float(prior_cash),
                    actual_value=float(current_cash),
                    difference=float(-decline),
                    difference_pct=float(-decline_pct),
                    recommendation="Review cash flow statement and operating performance for causes of cash burn",
                )
            ]

        return []

    def _validate_cash_flow_reconciliation(
        self,
        cash_flow_statement: CashFlowStatement,
        balance_sheet: BalanceSheet,
        prior_balance_sheet: Optional[BalanceSheet],
    ) -> List[ReconciliationIssue]:
        """
        Validate cash flow statement reconciles to balance sheet cash.

        Checks:
        - Ending cash from cash flow statement matches balance sheet cash
        - Net change cash = operating + investing + financing
        - Beginning cash + net change = ending cash

        Returns:
            List of ReconciliationIssue (empty if reconciled)
        """
        issues = []

        # Check 1: Ending cash matches balance sheet
        difference = cash_flow_statement.ending_cash - balance_sheet.cash
        if abs(difference) >= Decimal("1"):  # Allow $1 rounding
            severity = self._calculate_severity(difference, balance_sheet.cash)
            issues.append(
                ReconciliationIssue(
                    severity=severity,
                    category="cash_flow",
                    title="Cash flow ending cash doesn't match balance sheet",
                    description=f"Cash flow statement shows ending cash of {cash_flow_statement.ending_cash:,.2f} but balance sheet shows {balance_sheet.cash:,.2f}. Difference: {difference:,.2f}",
                    expected_value=float(balance_sheet.cash),
                    actual_value=float(cash_flow_statement.ending_cash),
                    difference=float(difference),
                    difference_pct=float((difference / balance_sheet.cash) * 100) if balance_sheet.cash != 0 else 0.0,
                    recommendation="Verify cash flow statement calculations and balance sheet cash accounts",
                )
            )

        # Check 2: Net change calculation
        calc_net_change = (
            cash_flow_statement.operating_cash_flow
            + cash_flow_statement.investing_cash_flow
            + cash_flow_statement.financing_cash_flow
        )
        net_change_diff = calc_net_change - cash_flow_statement.net_change_cash
        if abs(net_change_diff) >= Decimal("1"):
            severity = self._calculate_severity(net_change_diff, abs(calc_net_change))
            issues.append(
                ReconciliationIssue(
                    severity=severity,
                    category="cash_flow",
                    title="Net change cash doesn't reconcile",
                    description=f"Operating + Investing + Financing = {calc_net_change:,.2f} but net change shows {cash_flow_statement.net_change_cash:,.2f}",
                    expected_value=float(calc_net_change),
                    actual_value=float(cash_flow_statement.net_change_cash),
                    difference=float(net_change_diff),
                    difference_pct=float((net_change_diff / calc_net_change) * 100) if calc_net_change != 0 else 0.0,
                    recommendation="Review cash flow statement activity categories for errors",
                )
            )

        # Check 3: Beginning + net change = ending (if prior balance sheet provided)
        if prior_balance_sheet:
            beginning_diff = cash_flow_statement.beginning_cash - prior_balance_sheet.cash
            if abs(beginning_diff) >= Decimal("1"):
                severity = self._calculate_severity(beginning_diff, prior_balance_sheet.cash)
                issues.append(
                    ReconciliationIssue(
                        severity=severity,
                        category="cash_flow",
                        title="Beginning cash doesn't match prior period ending cash",
                        description=f"Cash flow shows beginning cash of {cash_flow_statement.beginning_cash:,.2f} but prior balance sheet shows {prior_balance_sheet.cash:,.2f}",
                        expected_value=float(prior_balance_sheet.cash),
                        actual_value=float(cash_flow_statement.beginning_cash),
                        difference=float(beginning_diff),
                        difference_pct=float((beginning_diff / prior_balance_sheet.cash) * 100) if prior_balance_sheet.cash != 0 else 0.0,
                        recommendation="Verify beginning cash matches prior period",
                    )
                )

        return issues

    def _validate_income_to_equity(
        self,
        income_statement: IncomeStatement,
        balance_sheet: BalanceSheet,
        prior_balance_sheet: Optional[BalanceSheet],
        cash_flow_statement: CashFlowStatement,
    ) -> List[ReconciliationIssue]:
        """
        Validate net income flows to retained earnings.

        Simplified validation: Equity change should reasonably relate to net income.
        Note: This is a basic check - full validation would need retained earnings breakdown.

        Returns:
            List of ReconciliationIssue (empty if reasonable)
        """
        # Skip if no prior balance sheet
        if not prior_balance_sheet:
            return []

        # Calculate net income
        net_income = (
            income_statement.revenue
            - income_statement.cogs
            - income_statement.operating_expenses
            - income_statement.interest_expense
            - income_statement.tax_expense
        )

        # Calculate equity change
        equity_change = balance_sheet.equity - prior_balance_sheet.equity

        # Simplified check: If net income is positive, equity should generally increase
        # (or at least not decrease significantly more than net income)
        # This catches major discrepancies without requiring detailed retained earnings data
        issues = []

        # If net income is significantly positive but equity decreased significantly
        if net_income > Decimal("10000") and equity_change < Decimal("-10000"):
            issues.append(
                ReconciliationIssue(
                    severity=FinancialRiskSeverity.INFO,
                    category="income_equity",
                    title="Equity decreased despite positive net income",
                    description=f"Net income of {net_income:,.2f} but equity decreased by {abs(equity_change):,.2f}. May indicate dividends or other distributions not visible in income statement.",
                    expected_value=float(net_income),  # Approximate
                    actual_value=float(equity_change),
                    difference=float(equity_change - net_income),
                    difference_pct=0.0,
                    recommendation="Review equity accounts for dividends, distributions, or other non-income changes",
                )
            )

        return issues

    def _validate_line_item_reasonableness(
        self, income_statement: IncomeStatement, balance_sheet: BalanceSheet
    ) -> List[ReconciliationIssue]:
        """
        Check for unusual relationships between line items.

        Validates basic reasonableness checks:
        - COGS should not exceed revenue (impossible margin)
        - Operating expenses should be reasonable relative to revenue

        Returns:
            List of ReconciliationIssue (empty if reasonable)
        """
        issues = []

        # Check 1: COGS should not exceed revenue
        if income_statement.cogs > income_statement.revenue:
            excess = income_statement.cogs - income_statement.revenue
            issues.append(
                ReconciliationIssue(
                    severity=FinancialRiskSeverity.CRITICAL,
                    category="line_items",
                    title="COGS exceeds revenue",
                    description=f"Cost of goods sold ({income_statement.cogs:,.2f}) exceeds revenue ({income_statement.revenue:,.2f}). This indicates a data error or impossible business model.",
                    expected_value=float(income_statement.revenue),
                    actual_value=float(income_statement.cogs),
                    difference=float(excess),
                    difference_pct=float((excess / income_statement.revenue) * 100) if income_statement.revenue > 0 else 0.0,
                    recommendation="Review COGS and revenue accounts for data entry errors",
                )
            )

        # Check 2: Extremely high operating expense ratio (>200% of revenue)
        if income_statement.revenue > 0:
            opex_ratio = (income_statement.operating_expenses / income_statement.revenue) * Decimal("100")
            if opex_ratio > Decimal("200"):
                issues.append(
                    ReconciliationIssue(
                        severity=FinancialRiskSeverity.WARNING,
                        category="line_items",
                        title=f"Very high operating expense ratio ({opex_ratio:.1f}%)",
                        description=f"Operating expenses ({income_statement.operating_expenses:,.2f}) are {opex_ratio:.1f}% of revenue ({income_statement.revenue:,.2f}). This may indicate startup/distressed operations or data errors.",
                        expected_value=float(income_statement.revenue),
                        actual_value=float(income_statement.operating_expenses),
                        difference=float(income_statement.operating_expenses - income_statement.revenue),
                        difference_pct=float(opex_ratio),
                        recommendation="Review operating expense classifications and revenue recognition",
                    )
                )

        return issues

    def _calculate_severity(
        self, difference: Decimal, base_value: Decimal
    ) -> FinancialRiskSeverity:
        """
        Calculate severity using hybrid materiality thresholds.

        BOTH percentage AND absolute thresholds must be met for each level:
        - CRITICAL: >= 5% AND >= $10,000
        - WARNING: >= 2% AND >= $5,000
        - INFO: Below WARNING thresholds

        Args:
            difference: The discrepancy amount (absolute value)
            base_value: The base amount to calculate percentage from

        Returns:
            Severity level (CRITICAL, WARNING, or INFO)

        Note:
            When base_value is zero, use absolute thresholds only.
        """
        # Take absolute value to handle negative differences
        abs_difference = abs(difference)

        # Handle zero base value - use absolute thresholds only
        if base_value == 0:
            if abs_difference >= Decimal("10000"):
                return FinancialRiskSeverity.CRITICAL
            elif abs_difference >= Decimal("5000"):
                return FinancialRiskSeverity.WARNING
            else:
                return FinancialRiskSeverity.INFO

        # Calculate percentage difference
        percentage = (abs_difference / abs(base_value)) * Decimal("100")

        # Hybrid thresholds - BOTH must be met
        # Check CRITICAL: >= 5% AND >= $10,000
        if percentage >= Decimal("5") and abs_difference >= Decimal("10000"):
            return FinancialRiskSeverity.CRITICAL

        # Check WARNING: >= 2% AND >= $5,000
        if percentage >= Decimal("2") and abs_difference >= Decimal("5000"):
            return FinancialRiskSeverity.WARNING

        # Below both threshold pairs
        return FinancialRiskSeverity.INFO

    def _build_summary(
        self, critical_count: int, warning_count: int, info_count: int, quality: str
    ) -> str:
        """Build executive summary of analysis results."""
        if critical_count > 0:
            return f"{critical_count} critical issues found - statements do not reconcile"
        elif warning_count > 0:
            return f"{warning_count} warnings found, statements generally reconcile"
        elif info_count > 0:
            return f"{info_count} informational notes, statements reconcile well"
        else:
            return "No issues found, statements reconcile perfectly"
