"""Phase 5: Integration Planning module."""

from corporate_development.integration_planning.base_analyzer import BaseDomainAnalyzer
from corporate_development.integration_planning.types import (
    IntegrationPlanningInput,
    Activity,
    TimePeriod,
    Risk,
    Metric,
    IntegrationPlan,
    Priority,
    IntegrationRiskSeverity,
    Severity,  # backwards-compatible alias for IntegrationRiskSeverity
    Likelihood,
    Impact,
    ReviewFrequency,
    ComplexityRating,
)
from corporate_development.integration_planning.templates import TemplateLibrary
from corporate_development.integration_planning.team_analyzer import TeamAnalyzer
from corporate_development.integration_planning.technology_analyzer import TechnologyAnalyzer
from corporate_development.integration_planning.product_analyzer import ProductAnalyzer
from corporate_development.integration_planning.operations_analyzer import OperationsAnalyzer
from corporate_development.integration_planning.customer_analyzer import CustomerAnalyzer
from corporate_development.integration_planning.finance_analyzer import FinanceAnalyzer
from corporate_development.integration_planning.timeline_builder import TimelineBuilder
from corporate_development.integration_planning.risk_analyzer import RiskAnalyzer
from corporate_development.integration_planning.metrics_generator import MetricsGenerator
from corporate_development.integration_planning.planner import IntegrationPlanner
from corporate_development.integration_planning.playbook_generator import PlaybookGenerator
from corporate_development.integration_planning.timeline_generator import TimelineGenerator
from corporate_development.integration_planning.action_tracker_generator import ActionTrackerGenerator
from corporate_development.integration_planning.risk_mitigation_generator import RiskMitigationGenerator
from corporate_development.integration_planning.metrics_artifact_generator import MetricsArtifactGenerator

__all__ = [
    "BaseDomainAnalyzer",
    "IntegrationPlanningInput",
    "Activity",
    "TimePeriod",
    "Risk",
    "Metric",
    "IntegrationPlan",
    "Priority",
    "IntegrationRiskSeverity",
    "Severity",
    "Likelihood",
    "Impact",
    "ReviewFrequency",
    "ComplexityRating",
    "TemplateLibrary",
    "TeamAnalyzer",
    "TechnologyAnalyzer",
    "ProductAnalyzer",
    "OperationsAnalyzer",
    "CustomerAnalyzer",
    "FinanceAnalyzer",
    "TimelineBuilder",
    "RiskAnalyzer",
    "MetricsGenerator",
    "IntegrationPlanner",
    "PlaybookGenerator",
    "TimelineGenerator",
    "ActionTrackerGenerator",
    "RiskMitigationGenerator",
    "MetricsArtifactGenerator",
]
