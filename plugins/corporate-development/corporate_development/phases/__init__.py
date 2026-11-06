"""Phase-specific implementations for M&A workflow."""

from corporate_development.phases.phase_0_readiness import Phase0AcquisitionReadiness
from corporate_development.phases.phase_1_sourcing import Phase1DealSourcing
from corporate_development.phases.phase_2_assessment import Phase2TargetAssessment
from corporate_development.phases.phase_3_operational_dd import Phase3OperationalDD
from corporate_development.phases.phase_4_financial_dd import Phase4FinancialDD
from corporate_development.phases.phase_5_integration import Phase5IntegrationPlanning
from corporate_development.phases.phase_6_decision import Phase6DealDecision

__all__ = [
    "Phase0AcquisitionReadiness",
    "Phase1DealSourcing",
    "Phase2TargetAssessment",
    "Phase3OperationalDD",
    "Phase4FinancialDD",
    "Phase5IntegrationPlanning",
    "Phase6DealDecision",
    "PHASES",
]

# Phase registry mapping phase numbers to phase classes
PHASES = {
    0: Phase0AcquisitionReadiness,
    1: Phase1DealSourcing,
    2: Phase2TargetAssessment,
    3: Phase3OperationalDD,
    4: Phase4FinancialDD,
    5: Phase5IntegrationPlanning,
    6: Phase6DealDecision,
}
