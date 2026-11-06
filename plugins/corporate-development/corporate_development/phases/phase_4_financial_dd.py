"""Phase 4: Financial Due Diligence"""

from datetime import date
from decimal import Decimal
from corporate_development.core.phase import Phase, PhaseInput, PhaseOutput, PhaseGate
from corporate_development.core.constants import FINANCIAL_GO_THRESHOLD, FINANCIAL_CONDITIONAL_THRESHOLD
from corporate_development.artifacts.artifact_builder import ArtifactBuilder
from corporate_development.financial_dd import (
    EarningsCalculator,
    FinancingAnalyzer,
    HealthScorer,
    StatementParser,
    RiskAnalyzer,
    FinancialAnalyzer,
)
from corporate_development.financial_dd.types import (
    IncomeStatement,
    BalanceSheet,
    OwnershipStructure,
    SizeTier,
    FinancialDataPoint,
    FinancialMetrics,
    HealthScoringMetrics,
    CompanySize,
    FinancingAssumptions,
    RiskLevel,
    FinancialRiskSeverity,
)


class Phase4FinancialDD(Phase):
    """Phase 4: Financial Due Diligence - valuation, synergies, liabilities."""

    name = "Phase 4: Financial Due Diligence"
    description = "Financial valuation, synergy quantification, hidden liability assessment"

    def __init__(self):
        self.earnings_calc = EarningsCalculator()
        self.financing_analyzer = FinancingAnalyzer()
        self.health_scorer = HealthScorer()
        self.statement_parser = StatementParser()
        self.risk_analyzer = RiskAnalyzer()
        self.financial_analyzer = FinancialAnalyzer()

    def _determine_size_tier(self, revenue: float) -> tuple[SizeTier, CompanySize]:
        """Determine size tier and company size from revenue.

        Args:
            revenue: Annual revenue in dollars

        Returns:
            Tuple of (SizeTier, CompanySize)
        """
        if revenue < 2_000_000:
            return SizeTier.SMALL, CompanySize.SMALL
        elif revenue < 10_000_000:
            return SizeTier.MEDIUM, CompanySize.MEDIUM
        elif revenue < 50_000_000:
            return SizeTier.MEDIUM, CompanySize.MID_MARKET
        else:
            return SizeTier.LARGE, CompanySize.ENTERPRISE

    def _calculate_net_income(self, income_stmt: IncomeStatement) -> Decimal:
        """Calculate net income from income statement.

        Args:
            income_stmt: Income statement with financial data

        Returns:
            Net income as Decimal
        """
        return (
            income_stmt.revenue
            - income_stmt.cogs
            - income_stmt.operating_expenses
            - income_stmt.interest_expense
            - income_stmt.tax_expense
            - (income_stmt.depreciation or Decimal("0"))
            - (income_stmt.amortization or Decimal("0"))
        )

    def _determine_gate(self, health_score: float, ebitda_value: float) -> PhaseGate:
        """Determine phase gate decision based on health score and EBITDA.

        Args:
            health_score: Overall health score (0-100)
            ebitda_value: EBITDA value in dollars

        Returns:
            Phase gate decision
        """
        if health_score >= FINANCIAL_GO_THRESHOLD and ebitda_value > 0:
            return PhaseGate.GO
        elif health_score >= FINANCIAL_CONDITIONAL_THRESHOLD:
            return PhaseGate.CONDITIONAL
        else:
            return PhaseGate.NO_GO

    def _determine_final_gate(
        self, health_gate: PhaseGate, risk_level: RiskLevel
    ) -> PhaseGate:
        """Determine final gate decision considering both health and risk.

        Risk influence:
        - HIGH risk → Downgrade one level (GO→CONDITIONAL, CONDITIONAL→NO_GO)
        - MEDIUM risk → Downgrade GO to CONDITIONAL only
        - LOW risk → No change

        Args:
            health_gate: Initial gate decision based on health score
            risk_level: Risk level from RiskAnalyzer

        Returns:
            Final phase gate decision
        """
        if risk_level == RiskLevel.HIGH:
            if health_gate == PhaseGate.GO:
                return PhaseGate.CONDITIONAL
            else:  # CONDITIONAL or NO_GO
                return PhaseGate.NO_GO

        if risk_level == RiskLevel.MEDIUM:
            if health_gate == PhaseGate.GO:
                return PhaseGate.CONDITIONAL
            # Don't downgrade CONDITIONAL→NO_GO for MEDIUM risk
            return health_gate

        # LOW risk: no change
        return health_gate

    def _build_financial_metrics(
        self,
        income_stmt: IncomeStatement,
        net_income: Decimal,
        owner_comp: Decimal,
        source: str
    ) -> FinancialMetrics:
        """Build FinancialMetrics from income statement data.

        Args:
            income_stmt: Income statement with financial data
            net_income: Calculated net income
            owner_comp: Owner's compensation
            source: Data source description (e.g., "income_statement", "parsed_file")

        Returns:
            FinancialMetrics object for calculations
        """
        return FinancialMetrics(
            net_income=FinancialDataPoint(value=float(net_income), source=source),
            interest_expense=FinancialDataPoint(value=float(income_stmt.interest_expense), source=source),
            tax_expense=FinancialDataPoint(value=float(income_stmt.tax_expense), source=source),
            depreciation=FinancialDataPoint(value=float(income_stmt.depreciation or 0), source=source),
            amortization=FinancialDataPoint(value=float(income_stmt.amortization or 0), source=source),
            owner_compensation=FinancialDataPoint(value=float(owner_comp), source="user_input" if source == "parsed_file" else source),
        )

    def _build_health_metrics(
        self,
        income_stmt: IncomeStatement,
        balance_sheet: BalanceSheet,
        net_income: Decimal
    ) -> HealthScoringMetrics:
        """Build HealthScoringMetrics from financial statements.

        Args:
            income_stmt: Income statement with financial data
            balance_sheet: Balance sheet with financial position
            net_income: Calculated net income

        Returns:
            HealthScoringMetrics for health score calculation
        """
        return HealthScoringMetrics(
            # Balance Sheet
            current_assets=balance_sheet.cash + balance_sheet.accounts_receivable + balance_sheet.inventory + balance_sheet.other_current_assets,
            current_liabilities=balance_sheet.accounts_payable + balance_sheet.accrued_expenses + balance_sheet.current_debt + balance_sheet.other_current_liabilities,
            total_assets=balance_sheet.cash + balance_sheet.accounts_receivable + balance_sheet.inventory + balance_sheet.other_current_assets + balance_sheet.ppe_net + balance_sheet.intangibles + balance_sheet.other_assets,
            total_liabilities=balance_sheet.accounts_payable + balance_sheet.accrued_expenses + balance_sheet.current_debt + balance_sheet.other_current_liabilities + balance_sheet.long_term_debt + balance_sheet.other_liabilities,
            # Income Statement
            revenue=income_stmt.revenue,
            cogs=income_stmt.cogs,
            operating_expenses=income_stmt.operating_expenses,
            interest_expense=income_stmt.interest_expense,
            tax_expense=income_stmt.tax_expense,
            net_income=net_income,
            # Cash Flow (simplified - use net income as proxy)
            operating_cash_flow=net_income,  # Simplified approximation
            # Growth (use current revenue as prior year for now)
            prior_year_revenue=income_stmt.revenue * Decimal("0.9"),  # Assume 10% growth
        )

    def _build_balance_sheet(self, raw: dict, as_of_date=None, currency: str = "USD") -> BalanceSheet:
        """Build a BalanceSheet from a raw user-input dict.

        Args:
            raw: Dictionary of balance sheet fields (keys match BalanceSheet field names).
            as_of_date: Date the balance sheet is as of. Defaults to 2025-12-31 if None.
            currency: Currency code (e.g. "USD"). Defaults to "USD".

        Returns:
            Populated BalanceSheet Pydantic model.
        """
        from datetime import date as _date
        if as_of_date is None:
            as_of_date = _date.fromisoformat(raw.get("as_of_date", "2025-12-31"))
        elif isinstance(as_of_date, str):
            as_of_date = _date.fromisoformat(as_of_date)

        kwargs = dict(
            as_of_date=as_of_date,
            cash=Decimal(str(raw.get("cash", 0))),
            accounts_receivable=Decimal(str(raw.get("accounts_receivable", 0))),
            inventory=Decimal(str(raw.get("inventory", 0))),
            other_current_assets=Decimal(str(raw.get("other_current_assets", 0))),
            ppe_net=Decimal(str(raw.get("ppe_net", 0))),
            intangibles=Decimal(str(raw.get("intangibles", 0))),
            other_assets=Decimal(str(raw.get("other_assets", 0))),
            accounts_payable=Decimal(str(raw.get("accounts_payable", 0))),
            accrued_expenses=Decimal(str(raw.get("accrued_expenses", 0))),
            current_debt=Decimal(str(raw.get("current_debt", 0))),
            other_current_liabilities=Decimal(str(raw.get("other_current_liabilities", 0))),
            long_term_debt=Decimal(str(raw.get("long_term_debt", 0))),
            other_liabilities=Decimal(str(raw.get("other_liabilities", 0))),
            equity=Decimal(str(raw.get("equity", 0))),
        )
        if currency != "USD":
            kwargs["currency"] = currency
        return BalanceSheet(**kwargs)

    def _build_output_data(self, revenue: float, ebitda_result, sde_result, debt_capacity_result,
                            leverage_scenarios, health_score: float, liquidity_score: float,
                            size_tier: SizeTier, ownership: OwnershipStructure, risk_result=None,
                            health_gate: PhaseGate = None, final_gate: PhaseGate = None,
                            analysis_result=None) -> dict:
        """Build structured output data dictionary.

        Args:
            revenue: Annual revenue
            ebitda_result: EBITDA calculation result
            sde_result: SDE calculation result
            debt_capacity_result: Debt capacity analysis result
            leverage_scenarios: List of leverage scenarios
            health_score: Overall health score
            liquidity_score: Liquidity component score
            size_tier: Company size tier
            ownership: Ownership structure
            risk_result: Risk analysis result (optional)
            health_gate: Original health-based gate decision (optional)
            final_gate: Final gate decision after risk consideration (optional)

        Returns:
            Dictionary with structured output data
        """
        # Calculate margins
        ebitda_margin = (ebitda_result.value / revenue * 100) if revenue > 0 else 0
        sde_margin = (sde_result.value / revenue * 100) if revenue > 0 else 0

        output = {
            "ebitda": ebitda_result.value,
            "ebitda_margin": ebitda_margin,
            "sde": sde_result.value,
            "sde_margin": sde_margin,
            "debt_capacity": {
                "max_debt_conservative": debt_capacity_result.max_debt_conservative,
                "max_debt_preferred": debt_capacity_result.max_debt_preferred,
                "monthly_payment_conservative": debt_capacity_result.monthly_payment_conservative,
                "monthly_payment_preferred": debt_capacity_result.monthly_payment_preferred,
            },
            "leverage_scenarios": [
                {
                    "leverage_percentage": scenario.leverage_percentage,
                    "debt_amount": scenario.debt_amount,
                    "equity_required": scenario.equity_required,
                    "cash_on_cash_roi": scenario.cash_on_cash_roi,
                    "meets_conservative_threshold": scenario.meets_conservative_threshold,
                }
                for scenario in leverage_scenarios
            ],
            "health_score": health_score,
            "liquidity_score": liquidity_score,
            "size_tier": size_tier.value,
            "ownership_structure": ownership.value,
        }

        # Add risk analysis if available
        if risk_result:
            # Count flags by severity
            critical_count = sum(1 for f in risk_result.red_flags if f.severity == FinancialRiskSeverity.CRITICAL)
            warning_count = sum(1 for f in risk_result.red_flags if f.severity == FinancialRiskSeverity.WARNING)
            watch_count = sum(1 for f in risk_result.red_flags if f.severity == FinancialRiskSeverity.INFO)

            output["risk_analysis"] = {
                "risk_level": risk_result.overall_risk_level.value,
                "risk_score": risk_result.risk_score,
                "red_flags": [
                    {
                        "severity": flag.severity.value,
                        "category": flag.category,
                        "description": flag.description,
                        "value": str(flag.value),
                        "threshold": str(flag.threshold),
                    }
                    for flag in risk_result.red_flags
                ],
                "critical_count": critical_count,
                "warning_count": warning_count,
                "watch_count": watch_count,
                "data_completeness": risk_result.data_completeness,
                "flags_detected": risk_result.flags_detected,
            }

        # Add gate decisions if available
        if health_gate is not None:
            output["health_gate"] = health_gate.value
        if final_gate is not None:
            output["gate_decision"] = final_gate.value

        # Add statement quality analysis if available
        if analysis_result:
            output["statement_quality"] = {
                "accounting_basis": analysis_result.accounting_basis.detected_basis.value,
                "confidence": analysis_result.accounting_basis.confidence.value,
                "basis_reasoning": analysis_result.accounting_basis.reasoning,
                "overall_quality": analysis_result.overall_quality,
                "is_validated": analysis_result.is_validated,
                "reconciliation_issues": [
                    {
                        "severity": issue.severity.value,
                        "category": issue.category,
                        "title": issue.title,
                        "description": issue.description,
                        "expected_value": str(issue.expected_value),
                        "actual_value": str(issue.actual_value),
                        "difference": str(issue.difference),
                        "difference_pct": str(issue.difference_pct),
                        "recommendation": issue.recommendation,
                    }
                    for issue in analysis_result.reconciliation_issues
                ],
                "critical_count": analysis_result.critical_count,
                "warning_count": analysis_result.warning_count,
                "info_count": analysis_result.info_count,
                "summary": analysis_result.summary,
            }

        return output

    def _run_core_analysis(
        self,
        company_name: str,
        income_stmt: IncomeStatement,
        balance_sheet: BalanceSheet,
        ownership_str: str,
        owner_comp: Decimal,
        source_label: str,
        summary_suffix: str = "",
    ) -> PhaseOutput:
        """Shared financial analysis pipeline for both manual and file-based inputs.

        Handles everything from ownership detection through artifact writing and
        PhaseOutput construction. Both run() and _run_with_file_input() parse their
        specific inputs into typed objects and then delegate here.

        Args:
            company_name: Human-readable name for the target company.
            income_stmt: Parsed IncomeStatement (period already resolved by caller).
            balance_sheet: Parsed BalanceSheet (currency field set by caller if needed).
            ownership_str: Raw ownership key, e.g. "llc" or "owner_operator".
            owner_comp: Owner's compensation as Decimal.
            source_label: Data provenance tag used in FinancialMetrics
                ("income_statement" for manual input, "parsed_file" for file input).
            summary_suffix: Optional markdown block appended to the generated summary
                before artifact writing (used by file path for data-quality warnings).
        """
        # Determine ownership structure
        ownership = OwnershipStructure(ownership_str)

        # Detect size tier from revenue
        revenue = float(income_stmt.revenue)
        size_tier, company_size = self._determine_size_tier(revenue)

        # Calculate net income for FinancialMetrics
        net_income = self._calculate_net_income(income_stmt)

        # Convert to FinancialMetrics format for calculator
        metrics = self._build_financial_metrics(income_stmt, net_income, owner_comp, source_label)

        # Calculate EBITDA and SDE
        ebitda_result = self.earnings_calc.calculate_ebitda(metrics)
        sde_result = self.earnings_calc.calculate_sde(metrics, company_size)

        # Default financing assumptions
        financing_assumptions = FinancingAssumptions(
            interest_rate=0.07,  # 7% annual rate
            term_years=10  # 10-year term
        )

        # Analyze debt capacity (use SDE as recommended in book)
        debt_capacity_result = self.financing_analyzer.calculate_debt_capacity(
            sde=sde_result.value,
            assumptions=financing_assumptions
        )

        # Generate leverage scenarios (use 4x SDE as typical purchase price)
        purchase_price = sde_result.value * 4.0
        leverage_scenarios = self.financing_analyzer.model_leverage_scenarios(
            purchase_price=purchase_price,
            sde=sde_result.value,
            assumptions=financing_assumptions
        )

        # Build health scoring metrics and calculate full 4-dimension health score
        health_metrics = self._build_health_metrics(income_stmt, balance_sheet, net_income)
        health_result = self.health_scorer.calculate_health(health_metrics)
        liquidity_score = float(health_result.liquidity_score)
        health_score = float(health_result.total_score)

        # Analyze statement quality
        analysis_result = self.financial_analyzer.analyze(
            income_statement=income_stmt,
            balance_sheet=balance_sheet,
            cash_flow_statement=None,
            prior_balance_sheet=None
        )

        # Run risk analysis
        risk_result = self.risk_analyzer.analyze_risks({
            "income_statements": [income_stmt],
            "balance_sheets": [balance_sheet]
        })

        # Determine gate decision based on health score and EBITDA
        health_gate = self._determine_gate(health_score, ebitda_result.value)

        # Determine final gate decision considering risk
        gate = self._determine_final_gate(health_gate, risk_result.overall_risk_level)

        # Generate comprehensive summary artifact
        summary = self._generate_summary(
            company_name=company_name,
            size_tier=size_tier,
            ownership=ownership,
            ebitda_result=ebitda_result,
            sde_result=sde_result,
            debt_capacity_result=debt_capacity_result,
            leverage_scenarios=leverage_scenarios,
            health_score=health_score,
            liquidity_score=liquidity_score,
            gate=gate,
            analysis_result=analysis_result
        )

        # Append any caller-supplied suffix (e.g. data-quality warnings from file parsing)
        if summary_suffix:
            summary += summary_suffix

        artifact_builder = ArtifactBuilder(
            target_name=company_name,
            phase_name="phase_4_financial_dd"
        )

        summary_path = artifact_builder.write_markdown("phase_4_summary", summary)

        # Calculate margins for output and reasoning
        ebitda_margin = (ebitda_result.value / revenue * 100) if revenue > 0 else 0
        sde_margin = (sde_result.value / revenue * 100) if revenue > 0 else 0

        # Prepare structured data output
        data = self._build_output_data(
            revenue, ebitda_result, sde_result, debt_capacity_result,
            leverage_scenarios, health_score, liquidity_score, size_tier, ownership,
            risk_result, health_gate, gate, analysis_result
        )

        reasoning = (
            f"Financial analysis complete for {company_name} ({company_size.value}, {ownership.value}):\n"
            f"- EBITDA: ${ebitda_result.value:,.0f} ({ebitda_margin:.1f}% margin)\n"
            f"- SDE: ${sde_result.value:,.0f} ({sde_margin:.1f}% margin)\n"
            f"- Max Debt Capacity: ${debt_capacity_result.max_debt_preferred:,.0f} (preferred 1.5x threshold)\n"
            f"- Health Score: {health_score:.0f}/100\n"
            f"- Risk Level: {risk_result.overall_risk_level.value} "
            f"(Score: {risk_result.risk_score}/100, "
            f"{sum(1 for f in risk_result.red_flags if f.severity == FinancialRiskSeverity.CRITICAL)} CRITICAL, "
            f"{sum(1 for f in risk_result.red_flags if f.severity == FinancialRiskSeverity.WARNING)} WARNING, "
            f"{sum(1 for f in risk_result.red_flags if f.severity == FinancialRiskSeverity.INFO)} WATCH)\n"
            f"- Statement Quality: {analysis_result.overall_quality} "
            f"({analysis_result.critical_count} CRITICAL, "
            f"{analysis_result.warning_count} WARNING, "
            f"{analysis_result.info_count} INFO)\n"
            f"- Accounting Basis: {analysis_result.accounting_basis.detected_basis.value} "
            f"({analysis_result.accounting_basis.confidence.value} confidence)\n"
            f"- Health Gate: {health_gate.value}\n"
            f"- Final Gate Decision: {gate.value}\n"
            f"- Note: Operating cash flow and prior-year revenue are estimated "
            f"(net income proxy + 10% growth assumption). Provide actual cash flow "
            f"statements for precise health scoring."
        )

        return PhaseOutput(
            data=data,
            gate=gate,
            artifacts={"summary": str(summary_path)},
            reasoning=reasoning
        )

    @staticmethod
    def _engine_income_keys(raw: dict) -> dict:
        """Return raw with each engine key of the income statement, also when raw gives another name.

        The names come from StatementParser.INCOME_STATEMENT_SYNONYMS, the list of the file path, so
        `cost_of_goods_sold` gives `cogs`. The engine key wins, then the first name of the list.
        """
        data = dict(raw)
        for key, names in StatementParser.INCOME_STATEMENT_SYNONYMS.items():
            if key in data:
                continue
            for name in names:
                if name in raw:
                    data[key] = raw[name]
                    break
        return data

    def run(self, inputs: PhaseInput) -> PhaseOutput:
        """Execute Phase 4 financial due diligence with manually provided statements.

        Parses income statement and balance sheet from user_input dict, then
        delegates all shared computation to _run_core_analysis().
        """
        company_name = inputs.user_input.get("company_name", "Unknown")

        # Check if file path provided (FILE-BASED WORKFLOW)
        if "financial_data_file" in inputs.user_input:
            return self._run_with_file_input(inputs)

        # MANUAL INPUT WORKFLOW
        income_data = self._engine_income_keys(inputs.user_input.get("income_statement", {}))
        balance_data = inputs.user_input.get("balance_sheet", {})

        # Parse dates
        period_start = income_data.get("period_start", "2025-01-01")
        period_end = income_data.get("period_end", "2025-12-31")
        as_of_date = balance_data.get("as_of_date", "2025-12-31")

        if isinstance(period_start, str):
            period_start = date.fromisoformat(period_start)
        if isinstance(period_end, str):
            period_end = date.fromisoformat(period_end)
        if isinstance(as_of_date, str):
            as_of_date = date.fromisoformat(as_of_date)

        income_stmt = IncomeStatement(
            period_start=period_start,
            period_end=period_end,
            revenue=Decimal(str(income_data.get("revenue", 0))),
            cogs=Decimal(str(income_data.get("cogs", 0))),
            operating_expenses=Decimal(str(income_data.get("operating_expenses", 0))),
            depreciation=Decimal(str(income_data.get("depreciation", 0))),
            amortization=Decimal(str(income_data.get("amortization", 0))),
            interest_expense=Decimal(str(income_data.get("interest_expense", 0))),
            tax_expense=Decimal(str(income_data.get("tax_expense", 0))),
        )

        balance_sheet = self._build_balance_sheet(balance_data, as_of_date=as_of_date)

        ownership_str = inputs.user_input.get("ownership_structure", "llc")
        owner_comp = Decimal(str(income_data.get("owners_compensation", 0)))

        return self._run_core_analysis(
            company_name=company_name,
            income_stmt=income_stmt,
            balance_sheet=balance_sheet,
            ownership_str=ownership_str,
            owner_comp=owner_comp,
            source_label="income_statement",
        )

    def _run_with_file_input(self, inputs: PhaseInput) -> PhaseOutput:
        """Run Phase 4 with file-based input.

        Parses statements from a CSV/JSON file via StatementParser, constructs
        IncomeStatement and BalanceSheet objects (balance sheet sourced from
        manual user_input since file parsing does not yet provide it), then
        delegates all shared computation to _run_core_analysis().
        """
        company_name = inputs.user_input.get("company_name", "Unknown")
        file_path = inputs.user_input["financial_data_file"]
        file_format = inputs.user_input.get("file_format")

        # Parse statements from file
        parse_result = self.statement_parser.parse_statements(
            file_path=file_path,
            file_format=file_format
        )

        # Use most recent period
        if not parse_result.income_statements:
            return PhaseOutput(
                data={},
                gate=PhaseGate.NO_GO,
                artifacts={},
                reasoning="No income statement data found in file"
            )

        income_stmt = parse_result.income_statements[-1]  # Most recent

        # Balance sheet sourced from manual user_input (file parsing does not yet provide it)
        balance_data = inputs.user_input.get("balance_sheet", {})

        # Resolve as_of_date: prefer user-supplied, fall back to most-recent income period end
        as_of_date_raw = balance_data.get("as_of_date", str(income_stmt.period_end))

        balance_sheet = self._build_balance_sheet(
            raw=balance_data,
            as_of_date=as_of_date_raw,
            currency=parse_result.currency,  # Currency carried from parsed file
        )

        ownership_str = inputs.user_input.get("ownership_structure", "llc")
        owner_comp = Decimal(str(inputs.user_input.get("owners_compensation", 0)))

        # Build data-quality warning suffix from parse validation results
        summary_suffix = ""
        if parse_result.validation.warnings:
            summary_suffix = "\n\n## Data Quality Warnings\n\n"
            for warning in parse_result.validation.warnings:
                summary_suffix += f"- {warning}\n"

        return self._run_core_analysis(
            company_name=company_name,
            income_stmt=income_stmt,
            balance_sheet=balance_sheet,
            ownership_str=ownership_str,
            owner_comp=owner_comp,
            source_label="parsed_file",
            summary_suffix=summary_suffix,
        )

    def _generate_summary(
        self,
        company_name: str,
        size_tier: SizeTier,
        ownership: OwnershipStructure,
        ebitda_result,
        sde_result,
        debt_capacity_result,
        leverage_scenarios,
        health_score: float,
        liquidity_score: float,
        gate: PhaseGate,
        analysis_result=None
    ) -> str:
        """Generate comprehensive markdown summary."""

        # Calculate margins
        # Extract revenue from calculation notes if available
        revenue_estimate = sde_result.value / 0.3 if sde_result.value > 0 else 1  # Assume 30% margin as fallback
        ebitda_margin = (ebitda_result.value / revenue_estimate * 100)
        sde_margin = (sde_result.value / revenue_estimate * 100)

        summary = f"""# Phase 4: Financial Due Diligence - {company_name}

## Company Profile
- **Size Tier**: {size_tier.value}
- **Ownership Structure**: {ownership.value}

## Earnings Analysis

### EBITDA (Earnings Before Interest, Taxes, Depreciation, Amortization)
- **EBITDA**: ${ebitda_result.value:,.0f}
- **Estimated Margin**: {ebitda_margin:.1f}%
- **Calculation**: {ebitda_result.notes}

### SDE (Seller's Discretionary Earnings)
- **SDE**: ${sde_result.value:,.0f}
- **Estimated Margin**: {sde_margin:.1f}%
- **Calculation**: {sde_result.notes}

## Financing Analysis

### Debt Capacity (Book's 1.25x/1.5x Thresholds)
- **Conservative (1.25x)**: ${debt_capacity_result.max_debt_conservative:,.0f} (${debt_capacity_result.monthly_payment_conservative:,.0f}/mo)
- **Preferred (1.5x)**: ${debt_capacity_result.max_debt_preferred:,.0f} (${debt_capacity_result.monthly_payment_preferred:,.0f}/mo)

### Leverage Scenarios
"""

        for i, scenario in enumerate(leverage_scenarios):
            leverage_pct = scenario.leverage_percentage * 100
            summary += f"""
#### Scenario {i+1}: {leverage_pct:.0f}% Leverage
- **Debt Amount**: ${scenario.debt_amount:,.0f}
- **Equity Required**: ${scenario.equity_required:,.0f}
- **Cash-on-Cash ROI**: {scenario.cash_on_cash_roi:.1f}%
- **Meets Conservative Threshold**: {"Yes" if scenario.meets_conservative_threshold else "No"}
"""

        summary += f"""
## Financial Health Score

- **Overall Health Score**: {health_score:.0f}/100
- **Liquidity Score**: {liquidity_score:.0f}/30 (only dimension scored currently)

**Note**: Full health scoring (4 dimensions) will be implemented in future updates.
"""

        # Add statement quality analysis if available
        if analysis_result:
            summary += f"""
## Statement Quality Analysis

**Accounting Basis Detected**: {analysis_result.accounting_basis.detected_basis.value} ({analysis_result.accounting_basis.confidence.value} confidence)

{analysis_result.accounting_basis.reasoning}

**Overall Quality**: {analysis_result.overall_quality}
**Validation Status**: {"✓ Validated" if analysis_result.is_validated else "✗ Not Validated"}

### Reconciliation Issues
"""

            if analysis_result.critical_count > 0:
                summary += f"\n#### Critical Issues ({analysis_result.critical_count})\n\n"
                for issue in analysis_result.reconciliation_issues:
                    if issue.severity == FinancialRiskSeverity.CRITICAL:
                        summary += f"- **{issue.title}**: {issue.description}\n"
                        summary += f"  - Expected: ${issue.expected_value:,.0f}, Actual: ${issue.actual_value:,.0f}\n"
                        summary += f"  - Difference: ${issue.difference:,.0f} ({issue.difference_pct:.1f}%)\n"
                        summary += f"  - Recommendation: {issue.recommendation}\n\n"

            if analysis_result.warning_count > 0:
                summary += f"\n#### Warnings ({analysis_result.warning_count})\n\n"
                for issue in analysis_result.reconciliation_issues:
                    if issue.severity == FinancialRiskSeverity.WARNING:
                        summary += f"- **{issue.title}**: {issue.description}\n"
                        summary += f"  - Recommendation: {issue.recommendation}\n\n"

            if analysis_result.info_count > 0:
                summary += f"\n#### Information ({analysis_result.info_count})\n\n"
                for issue in analysis_result.reconciliation_issues:
                    if issue.severity == FinancialRiskSeverity.INFO:
                        summary += f"- {issue.title}: {issue.description}\n"

            if not analysis_result.reconciliation_issues:
                summary += "\n✓ No reconciliation issues found. Statements are internally consistent.\n"

        summary += f"""
## Gate Decision: {gate.value}

"""

        if gate == PhaseGate.GO:
            summary += "**Recommendation**: Proceed with acquisition. Financial metrics are strong."
        elif gate == PhaseGate.CONDITIONAL:
            summary += "**Recommendation**: Proceed with caution. Address financial concerns before closing."
        else:
            summary += "**Recommendation**: Do not proceed. Financial metrics indicate high risk."

        return summary
