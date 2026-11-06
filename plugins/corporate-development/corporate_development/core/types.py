"""Shared core types for the corporate-development plugin.

Types defined here are canonical across all sub-modules. Sub-module-specific
enums (e.g. FinancialRiskSeverity, IntegrationRiskSeverity) are NOT
force-migrated to this module; RiskSeverity is provided here as a common
superset for future use.
"""

from enum import Enum


class RiskSeverity(str, Enum):
    """Canonical risk severity enum — superset of all sub-module severity enums.

    Covers all 5 values found across financial_dd (CRITICAL/WARNING/INFO)
    and integration_planning (CRITICAL/HIGH/MEDIUM/LOW).

    Existing code should NOT be migrated to use this enum immediately;
    it is provided as a common base for new code.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ComplexityRating(str, Enum):
    """Integration complexity rating — canonical definition for core/types.

    Consolidates duplicate definitions from integration_planning/types.py
    and decision_framework/types.py. Both sub-modules import from here.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
