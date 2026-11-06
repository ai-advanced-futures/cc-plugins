"""Financial Due Diligence module for Phase 4.

This module provides comprehensive financial analysis for M&A transactions,
including statement parsing, earnings normalization, leverage analysis,
and health scoring.

All calculations use 100% deterministic Python math - zero AI in formulas.
"""

# Import all components
from corporate_development.financial_dd.statement_parser import StatementParser
from corporate_development.financial_dd.financial_analyzer import FinancialAnalyzer
from corporate_development.financial_dd.earnings_calculator import EarningsCalculator
from corporate_development.financial_dd.financing_analyzer import FinancingAnalyzer
from corporate_development.financial_dd.health_scorer import HealthScorer
from corporate_development.financial_dd.risk_analyzer import RiskAnalyzer

# Import new analysis result types
from corporate_development.financial_dd.types import (
    ReconciliationIssue,
    BasisDetectionResult,
    FinancialAnalysisResult,
)

__all__ = [
    "StatementParser",
    "FinancialAnalyzer",
    "EarningsCalculator",
    "FinancingAnalyzer",
    "HealthScorer",
    "RiskAnalyzer",
    # Analysis result types
    "ReconciliationIssue",
    "BasisDetectionResult",
    "FinancialAnalysisResult",
]
