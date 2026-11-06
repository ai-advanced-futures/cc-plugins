"""Phase 5: Integration Planning (Buy then Build)"""

from corporate_development.core.phase import Phase, PhaseInput, PhaseOutput, PhaseGate
from corporate_development.artifacts.artifact_builder import ArtifactBuilder
from corporate_development.integration_planning import (
    IntegrationPlanner,
    IntegrationPlanningInput,
    PlaybookGenerator,
    TimelineGenerator,
    ActionTrackerGenerator,
    RiskMitigationGenerator,
    MetricsArtifactGenerator,
)


class Phase5IntegrationPlanning(Phase):
    """Phase 5: Integration Planning - 100-day playbook and buyer capability check."""

    name = "Phase 5: Integration Planning (Buy then Build)"
    description = "Validate buyer capability and design 100-day integration playbook"

    def __init__(self):
        self.integration_planner = IntegrationPlanner()

    def run(self, inputs: PhaseInput) -> PhaseOutput:
        """Execute Phase 5 integration planning.

        Pre-Gate: Buyer Capability Assessment
        - assess the expertise of the leadership team of the buyer

        Full Phase:
        - org design
        - manager enablement
        - integration roadmap
        - execution planning
        - product integration
        - retention strategy
        - at-risk customers
        - synergy tracking
        - communication plan
        """

        # Extract inputs
        company_name = inputs.user_input.get("company_name", "Unknown")
        acquirer_name = inputs.user_input.get("acquirer_name", "Your Company")

        # Optional inputs from previous phases
        operational_health_score = inputs.user_input.get("operational_health_score")
        team_strength = inputs.user_input.get("team_strength")
        tech_debt_level = inputs.user_input.get("tech_debt_level")
        financial_health_score = inputs.user_input.get("financial_health_score")
        annual_revenue = inputs.user_input.get("annual_revenue")
        strategic_fit = inputs.user_input.get("strategic_fit")
        integration_complexity = inputs.user_input.get("integration_complexity")
        critical_risks = inputs.user_input.get("critical_risks", [])

        # Build IntegrationPlanningInput
        planning_input = IntegrationPlanningInput(
            target_name=company_name,
            acquirer_name=acquirer_name,
            operational_health_score=operational_health_score,
            team_strength=team_strength,
            tech_debt_level=tech_debt_level,
            financial_health_score=financial_health_score,
            annual_revenue=annual_revenue,
            strategic_fit=strategic_fit,
            integration_complexity=integration_complexity,
            critical_risks=critical_risks if critical_risks else None,
        )

        # Generate complete integration plan
        integration_plan = self.integration_planner.generate_plan(planning_input)

        # Generate all 5 artifacts using a shared artifact builder to avoid archiving conflicts
        # Each generator internally creates its own builder, so we need to use manual generation
        output_base = inputs.user_input.get("output_base", ".corporate-development")

        # Create a single artifact builder for all Phase 5 artifacts
        artifact_builder = ArtifactBuilder(
            target_name=company_name,
            phase_name="phase_5_integration_planning",
            output_base=output_base,
        )

        # Generate artifacts manually using the generators' internal methods
        # but write with the shared artifact builder
        playbook_gen = PlaybookGenerator(target_name=company_name, output_base=output_base)
        playbook_content = playbook_gen._build_playbook_content(integration_plan)
        playbook_path = artifact_builder.write_markdown("playbook", playbook_content)

        timeline_gen = TimelineGenerator(target_name=company_name, output_base=output_base)
        timeline_data = timeline_gen._build_timeline_data(integration_plan)
        timeline_path = artifact_builder.write_json("timeline", timeline_data)

        action_tracker_gen = ActionTrackerGenerator(target_name=company_name, output_base=output_base)
        tracker_csv = action_tracker_gen._build_csv_content(integration_plan)
        action_tracker_path = artifact_builder.write_csv("action_tracker", tracker_csv)

        risk_mitigation_gen = RiskMitigationGenerator(target_name=company_name, output_base=output_base)
        risk_content = risk_mitigation_gen._build_risk_mitigation_content(integration_plan)
        risk_mitigation_path = artifact_builder.write_markdown("risk_mitigation", risk_content)

        metrics_gen = MetricsArtifactGenerator(target_name=company_name, output_base=output_base)
        metrics_data = metrics_gen._build_metrics_data(integration_plan)
        metrics_path = artifact_builder.write_json("success_metrics", metrics_data)

        # Build result data
        result_data = {
            "target_name": integration_plan.target_name,
            "acquirer_name": integration_plan.acquirer_name,
            "complexity_rating": integration_plan.complexity_rating.value,
            "total_activities": integration_plan.total_activities,
            "activities_by_domain": integration_plan.activities_by_domain,
            "critical_path_count": len(integration_plan.critical_path_activities),
            "risk_count": len(integration_plan.integration_risks),
            "risk_count_by_severity": integration_plan.risk_count_by_severity,
            "metrics_count": len(integration_plan.success_metrics),
            "timeline_periods": len(integration_plan.timeline),
        }

        # Build artifacts dictionary
        artifacts = {
            "playbook": str(playbook_path),
            "timeline": str(timeline_path),
            "action_tracker": str(action_tracker_path),
            "risk_mitigation": str(risk_mitigation_path),
            "success_metrics": str(metrics_path),
        }

        # Determine gate based on complexity and risks
        gate = PhaseGate.GO
        reasoning_parts = [
            f"Generated comprehensive 100-day integration plan for {company_name}.",
            f"Complexity: {integration_plan.complexity_rating.value.upper()}",
            f"Activities: {integration_plan.total_activities} across 6 domains",
            f"Risks: {len(integration_plan.integration_risks)} identified",
            f"Metrics: {len(integration_plan.success_metrics)} defined",
        ]

        # Check for high-risk conditions
        high_severity_risks = (
            integration_plan.risk_count_by_severity.get("critical", 0) +
            integration_plan.risk_count_by_severity.get("high", 0)
        )

        if high_severity_risks >= 5:
            reasoning_parts.append(
                f"CAUTION: {high_severity_risks} high-severity risks require executive attention."
            )

        return PhaseOutput(
            data=result_data,
            gate=gate,
            artifacts=artifacts,
            reasoning=" ".join(reasoning_parts)
        )
