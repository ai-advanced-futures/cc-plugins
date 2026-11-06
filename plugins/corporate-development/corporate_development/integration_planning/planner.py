"""IntegrationPlanner orchestrator for Phase 5.

This module provides the IntegrationPlanner class which coordinates all
6 domain analyzers, timeline builder, risk analyzer, and metrics generator
to produce a complete 100-day integration plan.

Example:
    >>> from corporate_development.integration_planning import (
    ...     IntegrationPlanner,
    ...     IntegrationPlanningInput,
    ... )
    >>>
    >>> # Create input with company details and conditions
    >>> input_data = IntegrationPlanningInput(
    ...     target_name="TechCorp",
    ...     acquirer_name="MegaCorp",
    ...     operational_health_score=75,
    ...     team_strength="moderate",
    ...     tech_debt_level="moderate",
    ...     financial_health_score=80,
    ...     annual_revenue=50_000_000.0,
    ...     strategic_fit="high",
    ...     integration_complexity="medium",
    ...     critical_risks=["Key leader may depart", "Customer concentration risk"],
    ... )
    >>>
    >>> # Generate complete integration plan
    >>> planner = IntegrationPlanner()
    >>> plan = planner.generate_plan(input_data)
    >>>
    >>> # Access plan components
    >>> print(f"Total Activities: {plan.total_activities}")
    >>> print(f"Integration Risks: {len(plan.integration_risks)}")
    >>> print(f"Success Metrics: {len(plan.success_metrics)}")
    >>> print(f"Complexity: {plan.complexity_rating.value}")
"""

from typing import List, Dict
from corporate_development.integration_planning.types import (
    IntegrationPlanningInput,
    IntegrationPlan,
    Activity,
    ComplexityRating,
    Priority,
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


class IntegrationPlanner:
    """Orchestrator for Phase 5 integration planning.

    This class coordinates all components to generate a complete 100-day
    integration plan:

    1. Uses 6 domain analyzers to generate 120+ activities
    2. Organizes activities into 4 time periods
    3. Generates 15-20 integration risks
    4. Generates 15-20 success metrics
    5. Calculates summary statistics and complexity rating

    The resulting IntegrationPlan model contains everything needed for:
    - Day-by-day execution playbook
    - Risk mitigation strategies
    - Success metrics tracking
    """

    def __init__(self):
        """Initialize IntegrationPlanner with all components."""
        # Shared template library for all analyzers
        self.template_library = TemplateLibrary()

        # 6 domain analyzers
        self.team_analyzer = TeamAnalyzer(self.template_library)
        self.technology_analyzer = TechnologyAnalyzer(self.template_library)
        self.product_analyzer = ProductAnalyzer(self.template_library)
        self.operations_analyzer = OperationsAnalyzer(self.template_library)
        self.customer_analyzer = CustomerAnalyzer(self.template_library)
        self.finance_analyzer = FinanceAnalyzer(self.template_library)

        # Support components
        self.timeline_builder = TimelineBuilder()
        self.risk_analyzer = RiskAnalyzer()
        self.metrics_generator = MetricsGenerator()

    def generate_plan(self, input_data: IntegrationPlanningInput) -> IntegrationPlan:
        """Generate a complete 100-day integration plan.

        This method orchestrates all analyzers and generators to produce
        a comprehensive integration plan.

        Args:
            input_data: Integration planning input with company info and conditions.

        Returns:
            Complete IntegrationPlan with timeline, risks, metrics, and statistics.
        """
        # Step 1: Generate activities from all 6 domain analyzers
        all_activities = []

        all_activities.extend(self.team_analyzer.generate_activities(input_data))
        all_activities.extend(self.technology_analyzer.generate_activities(input_data))
        all_activities.extend(self.product_analyzer.generate_activities(input_data))
        all_activities.extend(self.operations_analyzer.generate_activities(input_data))
        all_activities.extend(self.customer_analyzer.generate_activities(input_data))
        all_activities.extend(self.finance_analyzer.generate_activities(input_data))

        # Step 2: Build 4-period timeline from activities
        timeline = self.timeline_builder.build_timeline(all_activities)

        # Step 3: Generate integration risks
        integration_risks = self.risk_analyzer.generate_risks(input_data)

        # Step 4: Generate success metrics
        success_metrics = self.metrics_generator.generate_metrics(input_data)

        # Step 5: Calculate summary statistics
        total_activities = len(all_activities)
        activities_by_domain = self._count_by_domain(all_activities)
        critical_path_activities = self._identify_critical_path(all_activities)
        risk_count_by_severity = self._count_risks_by_severity(integration_risks)
        complexity_rating = self._determine_complexity(input_data, total_activities)

        # Step 6: Build and return complete plan
        return IntegrationPlan(
            target_name=input_data.target_name,
            acquirer_name=input_data.acquirer_name,
            timeline=timeline,
            total_activities=total_activities,
            activities_by_domain=activities_by_domain,
            critical_path_activities=critical_path_activities,
            integration_risks=integration_risks,
            risk_count_by_severity=risk_count_by_severity,
            success_metrics=success_metrics,
            complexity_rating=complexity_rating,
        )

    def _count_by_domain(self, activities: List[Activity]) -> Dict[str, int]:
        """Count activities by domain.

        Args:
            activities: List of all activities.

        Returns:
            Dictionary mapping domain names to activity counts.
        """
        counts = {}
        for activity in activities:
            domain = activity.domain
            counts[domain] = counts.get(domain, 0) + 1
        return counts

    def _identify_critical_path(self, activities: List[Activity]) -> List[str]:
        """Extract activity IDs for critical priority activities.

        Critical path activities are those with priority=CRITICAL that
        must be completed for integration success.

        Args:
            activities: List of all activities.

        Returns:
            List of activity IDs on the critical path.
        """
        critical_activities = [
            activity.id
            for activity in activities
            if activity.priority == Priority.CRITICAL
        ]
        return critical_activities

    def _count_risks_by_severity(self, risks: List) -> Dict[str, int]:
        """Count risks by severity level.

        Args:
            risks: List of Risk instances.

        Returns:
            Dictionary mapping severity levels to counts.
        """
        counts = {}
        for risk in risks:
            severity = risk.severity.value  # Get string value from enum
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def _determine_complexity(
        self,
        input_data: IntegrationPlanningInput,
        total_activities: int
    ) -> ComplexityRating:
        """Determine overall integration complexity rating.

        Complexity is based on:
        - Explicit integration_complexity from input
        - Number of critical risks
        - Team strength
        - Tech debt level
        - Operational/financial health scores
        - Total number of activities

        Args:
            input_data: Integration planning input.
            total_activities: Total number of activities generated.

        Returns:
            ComplexityRating (LOW, MEDIUM, or HIGH).
        """
        # Start with a base score
        complexity_score = 0

        # Factor 1: Explicit integration_complexity (highest weight)
        if input_data.integration_complexity:
            complexity_map = {
                "low": 0,
                "medium": 5,
                "high": 10,
            }
            complexity_score += complexity_map.get(input_data.integration_complexity.lower(), 5)

        # Factor 2: Number of critical risks
        if input_data.critical_risks:
            if len(input_data.critical_risks) >= 3:
                complexity_score += 3
            elif len(input_data.critical_risks) >= 1:
                complexity_score += 1

        # Factor 3: Team strength
        if input_data.team_strength:
            if input_data.team_strength.lower() == "weak":
                complexity_score += 2
            elif input_data.team_strength.lower() == "moderate":
                complexity_score += 1

        # Factor 4: Tech debt level
        if input_data.tech_debt_level:
            if input_data.tech_debt_level.lower() == "high":
                complexity_score += 2
            elif input_data.tech_debt_level.lower() == "moderate":
                complexity_score += 1

        # Factor 5: Operational health score
        if input_data.operational_health_score is not None:
            if input_data.operational_health_score < 60:
                complexity_score += 2
            elif input_data.operational_health_score < 75:
                complexity_score += 1

        # Factor 6: Financial health score
        if input_data.financial_health_score is not None:
            if input_data.financial_health_score < 60:
                complexity_score += 2
            elif input_data.financial_health_score < 75:
                complexity_score += 1

        # Factor 7: Total activities (more activities = more complexity)
        if total_activities >= 150:
            complexity_score += 2
        elif total_activities >= 130:
            complexity_score += 1

        # Map score to rating
        if complexity_score <= 4:
            return ComplexityRating.LOW
        elif complexity_score <= 10:
            return ComplexityRating.MEDIUM
        else:
            return ComplexityRating.HIGH
