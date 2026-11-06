"""Core data types for Financial Due Diligence.

All financial amounts use Decimal for precision.
All models use Pydantic for validation.
"""

from decimal import Decimal
from datetime import date
from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass

from pydantic import BaseModel, field_validator
from corporate_development.core.phase import PhaseGate


# ============================================================================
# Enums
# ============================================================================


class SizeTier(str, Enum):
    """Company size classification."""

    MICRO = "micro"  # < $1M revenue
    SMALL = "small"  # $1M - $5M
    MEDIUM = "medium"  # $5M - $50M
    LARGE = "large"  # > $50M


class OwnershipStructure(str, Enum):
    """Legal ownership structure."""

    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    PARTNERSHIP = "partnership"
    LLC = "llc"
    S_CORP = "s_corp"
    C_CORP = "c_corp"


class AccountingBasis(str, Enum):
    """Accounting methodology."""

    CASH = "cash"
    ACCRUAL = "accrual"
    MODIFIED_CASH = "modified_cash"


class AddBackCategory(str, Enum):
    """Categories of EBITDA/SDE add-backs."""

    OWNER_COMPENSATION = "owner_compensation"
    DISCRETIONARY_EXPENSE = "discretionary_expense"
    NON_RECURRING = "non_recurring"
    RELATED_PARTY = "related_party"
    DEPRECIATION = "depreciation"
    AMORTIZATION = "amortization"
    INTEREST = "interest"
    TAXES = "taxes"


class Confidence(str, Enum):
    """Confidence level for estimates and calculations."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CompanySize(str, Enum):
    """Company size classification for earnings context."""

    SMALL = "small"  # $1M - $5M revenue
    MEDIUM = "medium"  # $5M - $50M revenue
    MID_MARKET = "mid_market"  # $50M - $500M revenue
    ENTERPRISE = "enterprise"  # > $500M revenue


class FinancialRiskSeverity(str, Enum):
    """Severity level for financial risk flags."""

    CRITICAL = "critical"  # Deal-breaker issues
    WARNING = "warning"  # Concerning but not fatal
    INFO = "info"  # Worth noting


# Backwards-compatible alias — will be removed in a future major version
Severity = FinancialRiskSeverity


class RiskLevel(str, Enum):
    """Overall risk level for a deal."""

    HIGH = "high"  # Multiple critical flags or serious concerns
    MEDIUM = "medium"  # Some warnings but manageable
    LOW = "low"  # Clean financials, minimal concerns


# ============================================================================
# Validation and Parsing Result Types
# ============================================================================


@dataclass
class ValidationResult:
    """Result of financial statement validation."""
    is_complete: bool  # True if completeness_score >= 80%
    completeness_score: float  # 0-100
    missing_fields: List[str]  # Required/recommended fields not found
    warnings: List[str]  # Data quality issues
    suggestions: List[str]  # Helpful hints for user
    mapped_fields: Dict[str, str]  # Input column → canonical field
    unmapped_fields: List[str]  # Columns that couldn't be mapped


@dataclass
class RedFlag:
    """Individual risk flag identified during analysis."""
    severity: FinancialRiskSeverity
    category: str  # e.g., "liquidity", "profitability", "leverage"
    description: str  # Human-readable explanation
    value: float  # The metric value that triggered the flag
    threshold: float  # The threshold that was violated


@dataclass
class RiskAnalysis:
    """Complete risk analysis result."""
    overall_risk_level: RiskLevel
    risk_score: int  # 0-100 (lower is riskier)
    red_flags: List[RedFlag]
    summary: str  # Executive summary of risk assessment
    data_completeness: str = "full"  # "insufficient", "limited", or "full"
    flags_detected: int = 0  # Total number of flags checked
    recommendations: List[str] = None  # Recommended actions based on findings

    def __post_init__(self):
        """Initialize optional fields with defaults."""
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class ParseResult:
    """Result of parsing financial statements from file."""
    income_statements: List["IncomeStatement"]
    balance_sheets: List["BalanceSheet"]
    cash_flow_statements: List["CashFlowStatement"]
    validation: ValidationResult
    currency: str  # Detected currency (if consistent across statements)


# ============================================================================
# Financial Data Point Models
# ============================================================================


class FinancialDataPoint(BaseModel):
    """A single financial data point with source tracking."""

    value: float
    source: str
    notes: Optional[str] = None


class FinancialMetrics(BaseModel):
    """Collection of financial metrics for calculations."""

    net_income: Optional[FinancialDataPoint] = None
    interest_expense: Optional[FinancialDataPoint] = None
    tax_expense: Optional[FinancialDataPoint] = None
    depreciation: Optional[FinancialDataPoint] = None
    amortization: Optional[FinancialDataPoint] = None
    one_time_expenses: Optional[FinancialDataPoint] = None
    owner_compensation: Optional[FinancialDataPoint] = None
    owner_benefits: Optional[FinancialDataPoint] = None


class CalculationResult(BaseModel):
    """Result of a financial calculation with audit trail."""

    value: float
    calculation_steps: str
    data_sources: list[str]
    notes: str


# ============================================================================
# Financial Statement Models
# ============================================================================


class IncomeStatement(BaseModel):
    """Income statement data model."""

    period_start: date
    period_end: date
    revenue: Decimal
    cogs: Decimal
    operating_expenses: Decimal
    interest_expense: Decimal
    tax_expense: Decimal
    depreciation: Optional[Decimal] = None
    amortization: Optional[Decimal] = None
    currency: str = "USD"

    @field_validator("revenue")
    @classmethod
    def revenue_must_be_non_negative(cls, v: Decimal) -> Decimal:
        """Validate revenue is non-negative."""
        if v < 0:
            raise ValueError("Revenue must be non-negative")
        return v


class BalanceSheet(BaseModel):
    """Balance sheet data model."""

    as_of_date: date
    cash: Decimal
    accounts_receivable: Decimal
    inventory: Decimal
    other_current_assets: Decimal
    ppe_net: Decimal
    intangibles: Decimal
    other_assets: Decimal
    accounts_payable: Decimal
    accrued_expenses: Decimal
    current_debt: Decimal
    other_current_liabilities: Decimal
    long_term_debt: Decimal
    other_liabilities: Decimal
    equity: Decimal
    currency: str = "USD"

    @property
    def working_capital(self) -> Decimal:
        """Calculate working capital (current assets - current liabilities)."""
        current_assets = (
            self.cash
            + self.accounts_receivable
            + self.inventory
            + self.other_current_assets
        )
        current_liabilities = (
            self.accounts_payable
            + self.accrued_expenses
            + self.current_debt
            + self.other_current_liabilities
        )
        return current_assets - current_liabilities

    @property
    def current_ratio(self) -> Decimal:
        """Calculate current ratio (current assets / current liabilities)."""
        current_assets = (
            self.cash
            + self.accounts_receivable
            + self.inventory
            + self.other_current_assets
        )
        current_liabilities = (
            self.accounts_payable
            + self.accrued_expenses
            + self.current_debt
            + self.other_current_liabilities
        )
        if current_liabilities == 0:
            return Decimal("0")
        return current_assets / current_liabilities


class CashFlowStatement(BaseModel):
    """Cash flow statement data model."""

    period_start: date
    period_end: date
    operating_cash_flow: Decimal
    investing_cash_flow: Decimal
    financing_cash_flow: Decimal
    net_change_cash: Decimal
    beginning_cash: Decimal
    ending_cash: Decimal
    currency: str = "USD"


# ============================================================================
# Add-Back Models
# ============================================================================


class AddBack(BaseModel):
    """Individual add-back item for earnings normalization."""

    category: AddBackCategory
    amount: Decimal
    description: str
    confidence: Confidence
    rationale: str


# ============================================================================
# Calculation Result Models
# ============================================================================


class EBITDAResult(BaseModel):
    """EBITDA calculation result."""

    ebitda: Decimal
    ebitda_margin: Decimal
    add_backs_total: Decimal
    add_backs: list[AddBack]


class SDEResult(BaseModel):
    """Seller's Discretionary Earnings calculation result."""

    sde: Decimal
    sde_margin: Decimal
    add_backs_total: Decimal
    add_backs: list[AddBack]


class DebtCapacity(BaseModel):
    """Debt capacity analysis result using book's 1.25x/1.5x thresholds."""

    max_debt_conservative: float  # At 1.25x debt-to-earnings
    max_debt_preferred: float  # At 1.5x debt-to-earnings
    debt_to_earnings_conservative: float  # 1.25
    debt_to_earnings_preferred: float  # 1.5
    monthly_payment_conservative: float
    monthly_payment_preferred: float
    annual_debt_service_conservative: float
    annual_debt_service_preferred: float


class FinancingAssumptions(BaseModel):
    """Financing terms and assumptions."""

    interest_rate: float  # Annual interest rate (e.g., 0.07 for 7%)
    term_years: int  # Loan term in years


class LeverageScenario(BaseModel):
    """Leverage scenario with ROI calculations."""

    leverage_percentage: float  # 0.0 to 1.0
    debt_amount: float
    equity_required: float
    monthly_debt_service: float
    annual_debt_service: float
    annual_cash_flow: float  # After debt service
    cash_on_cash_roi: float
    debt_to_earnings: float
    meets_conservative_threshold: bool  # <= 1.25x
    meets_preferred_threshold: bool  # <= 1.5x


# ============================================================================
# Health Scoring Models
# ============================================================================


class LiquidityScore(BaseModel):
    """Liquidity health score."""

    score: int  # 0-100
    current_ratio: Decimal
    quick_ratio: Decimal
    working_capital: Decimal
    cash_conversion_days: Optional[int] = None


class ProfitabilityScore(BaseModel):
    """Profitability health score."""

    score: int  # 0-100
    gross_margin: Decimal
    ebitda_margin: Decimal
    net_margin: Decimal
    roa: Optional[Decimal] = None  # Return on Assets
    roe: Optional[Decimal] = None  # Return on Equity


class LeverageScore(BaseModel):
    """Leverage health score."""

    score: int  # 0-100
    debt_to_equity: Decimal
    debt_to_ebitda: Decimal
    interest_coverage: Decimal
    dscr: Decimal


class GrowthScore(BaseModel):
    """Growth health score."""

    score: int  # 0-100
    revenue_growth_rate: Decimal
    ebitda_growth_rate: Decimal
    compound_annual_growth_rate: Optional[Decimal] = None


class HealthScore(BaseModel):
    """Overall financial health score."""

    overall_score: int  # 0-100
    liquidity: LiquidityScore
    profitability: ProfitabilityScore
    leverage: LeverageScore
    growth: GrowthScore
    rating: str  # e.g., "Excellent", "Good", "Fair", "Poor"


# ============================================================================
# Health Scorer Types (Simplified for Testing)
# ============================================================================


class HealthScoringMetrics(BaseModel):
    """Simplified financial metrics for health scoring.

    Note: Renamed from FinancialMetrics to avoid conflict with the earnings calculator's
    FinancialMetrics type (which uses FinancialDataPoint fields).
    """

    # Balance Sheet
    current_assets: Decimal
    current_liabilities: Decimal
    total_assets: Decimal
    total_liabilities: Decimal

    # Income Statement
    revenue: Decimal
    cogs: Decimal
    operating_expenses: Decimal
    interest_expense: Decimal
    tax_expense: Decimal
    net_income: Decimal

    # Cash Flow
    operating_cash_flow: Decimal

    # Growth
    prior_year_revenue: Decimal


class FinancialHealth(BaseModel):
    """Financial health assessment result."""

    liquidity_score: Decimal  # 0-30 points
    profitability_score: Decimal  # 0-25 points
    leverage_score: Decimal  # 0-25 points
    growth_score: Decimal  # 0-20 points
    total_score: Decimal  # 0-100 points
    gate_decision: PhaseGate


# ============================================================================
# Financial Analysis Result Models
# ============================================================================


@dataclass
class ReconciliationIssue:
    """An identified financial statement inconsistency."""
    severity: FinancialRiskSeverity
    category: str  # e.g., "balance_sheet", "cash_flow", "income_equity"
    title: str  # Short title of the issue
    description: str  # Detailed explanation
    expected_value: Decimal
    actual_value: Decimal
    difference: Decimal
    difference_pct: Decimal
    recommendation: str  # Suggested action


@dataclass
class BasisDetectionResult:
    """Result of accounting basis detection."""
    detected_basis: AccountingBasis
    confidence: Confidence
    indicators: Dict[str, bool]  # Indicator name → whether present
    reasoning: str  # Explanation of why this basis was detected


@dataclass
class FinancialAnalysisResult:
    """Complete financial analysis result."""
    accounting_basis: BasisDetectionResult
    reconciliation_issues: List[ReconciliationIssue]
    critical_count: int
    warning_count: int
    info_count: int
    overall_quality: str  # "EXCELLENT", "GOOD", "FAIR", "POOR"
    is_validated: bool  # Whether statements reconcile
    summary: str  # Executive summary
