"""Phase 0: Acquisition Readiness"""

import json
from corporate_development.core.phase import Phase, PhaseInput, PhaseOutput, PhaseGate
from corporate_development.core.constants import (
    READINESS_GO_THRESHOLD,
    READINESS_CONDITIONAL_LOWER,
    READINESS_NO_GO_THRESHOLD,
)
from corporate_development.artifacts.artifact_builder import ArtifactBuilder
from corporate_development.readiness_assessment.types import AcquisitionReadinessInput
from corporate_development.readiness_assessment.ceo_readiness_scorer import CEOReadinessScorer
from corporate_development.readiness_assessment.strategic_clarity_analyzer import StrategicClarityAnalyzer
from corporate_development.readiness_assessment.organizational_capacity_scorer import OrganizationalCapacityScorer
from corporate_development.readiness_assessment.financial_readiness_scorer import FinancialReadinessScorer
from corporate_development.readiness_assessment.governance_framework_scorer import GovernanceFrameworkScorer
from corporate_development.readiness_assessment.artifact_generators import (
    ReadinessAssessmentGenerator,
    ReadinessSummaryGenerator,
    AcquisitionPlaybookGenerator
)


class Phase0AcquisitionReadiness(Phase):
    """Phase 0: Acquisition Readiness - strategic foundation and preparedness."""

    name = "Phase 0: Acquisition Readiness"
    description = "Assess organizational readiness and define strategic acquisition criteria"
    phase_number = 0

    # Dimension weights
    CEO_WEIGHT = 0.30
    STRATEGIC_WEIGHT = 0.20
    ORGANIZATIONAL_WEIGHT = 0.25
    FINANCIAL_WEIGHT = 0.15
    GOVERNANCE_WEIGHT = 0.10

    # CEO minimum threshold (hard requirement)
    CEO_MINIMUM_THRESHOLD = 7.0

    def run(self, inputs: PhaseInput) -> PhaseOutput:
        """Execute Phase 0 acquisition readiness assessment.

        Validates organizational preparedness across 5 dimensions:
        1. CEO Readiness (30% weight)
        2. Strategic Clarity (20% weight)
        3. Organizational Capacity (25% weight)
        4. Financial Readiness (15% weight)
        5. Governance Framework (10% weight)

        Uses hybrid gate logic:
        - Hard requirements: CEO ≥7.0, Strategic targets defined, Capital committed
        - Overall thresholds: ≥80 GO, 65-79 CONDITIONAL, <65 NO_GO
        """
        # Validate and parse input
        readiness_input = AcquisitionReadinessInput(**inputs.user_input)

        # Score each dimension
        ceo_result = CEOReadinessScorer().score(readiness_input.ceo_readiness)
        strategic_result = StrategicClarityAnalyzer().analyze(readiness_input.strategic_targets)
        org_result = OrganizationalCapacityScorer().score(readiness_input.organizational_capacity)
        financial_result = FinancialReadinessScorer().score(readiness_input.financial_readiness)
        governance_result = GovernanceFrameworkScorer().score(readiness_input.governance)

        # Check hard requirements
        passed_requirements, failure_reason = self._check_hard_requirements(
            ceo_result, strategic_result, financial_result
        )

        # Calculate weighted overall score
        overall_score = (
            ceo_result["score"] * self.CEO_WEIGHT +
            strategic_result["score"] * self.STRATEGIC_WEIGHT +
            org_result["score"] * self.ORGANIZATIONAL_WEIGHT +
            financial_result["score"] * self.FINANCIAL_WEIGHT +
            governance_result["score"] * self.GOVERNANCE_WEIGHT
        )

        # Determine gate decision
        gate, reasoning = self._determine_gate(overall_score, passed_requirements, failure_reason)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_score, ceo_result, strategic_result, org_result, financial_result, governance_result
        )

        # Build assessment data for artifacts
        assessment_data = {
            "company_name": readiness_input.company_name,
            "overall_score": overall_score,
            "gate_decision": gate.value,
            "ceo_readiness": {"score": ceo_result["score"], "weight": self.CEO_WEIGHT, **ceo_result},
            "strategic_clarity": {"score": strategic_result["score"], "weight": self.STRATEGIC_WEIGHT, **strategic_result},
            "organizational_capacity": {"score": org_result["score"], "weight": self.ORGANIZATIONAL_WEIGHT, **org_result},
            "financial_readiness": {"score": financial_result["score"], "weight": self.FINANCIAL_WEIGHT, **financial_result},
            "governance_framework": {"score": governance_result["score"], "weight": self.GOVERNANCE_WEIGHT, **governance_result},
            "recommendations": recommendations,
            "ceo_score": ceo_result["score"],
            "strategic_score": strategic_result["score"],
            "target_industries": readiness_input.strategic_targets.target_industries,
            "revenue_range": f"${readiness_input.strategic_targets.revenue_range_min:,.0f}-${readiness_input.strategic_targets.revenue_range_max:,.0f}",
            "strategic_priorities": readiness_input.strategic_targets.strategic_priorities
        }

        # Generate artifacts
        artifact_builder = ArtifactBuilder(
            target_name=readiness_input.company_name,
            phase_name="phase_0_readiness"
        )

        assessment_json = ReadinessAssessmentGenerator().generate(assessment_data)
        assessment_path = artifact_builder.write_json("readiness_assessment", json.loads(assessment_json))

        summary_md = ReadinessSummaryGenerator().generate(assessment_data)
        summary_path = artifact_builder.write_markdown("readiness_summary", summary_md)

        playbook_md = AcquisitionPlaybookGenerator().generate(assessment_data)
        playbook_path = artifact_builder.write_markdown("acquisition_playbook", playbook_md)

        # Build output data
        output_data = {
            "overall_readiness_score": overall_score,
            "gate_decision": gate.value,
            "ceo_readiness": ceo_result,
            "strategic_clarity": strategic_result,
            "organizational_capacity": org_result,
            "financial_readiness": financial_result,
            "governance_framework": governance_result,
            "recommendations": recommendations
        }

        return PhaseOutput(
            data=output_data,
            gate=gate,
            artifacts={
                "readiness_assessment": str(assessment_path),
                "readiness_summary": str(summary_path),
                "acquisition_playbook": str(playbook_path)
            },
            reasoning=reasoning
        )

    def _check_hard_requirements(self, ceo_result, strategic_result, financial_result):
        """Check critical success factors.

        Hard requirements:
        1. CEO readiness ≥7.0
        2. Strategic targets defined (industries not empty)
        3. Financial capacity confirmed (capital > 0)
        """
        # CEO threshold
        if not ceo_result["meets_threshold"]:
            return False, f"CEO readiness below minimum threshold: {ceo_result['ceo_average']:.1f}/10 (requires ≥{self.CEO_MINIMUM_THRESHOLD})"

        # Strategic clarity (validated by Pydantic min_items=1, but double-check)
        if strategic_result["score"] == 0:
            return False, "Strategic targets not defined - cannot proceed without acquisition criteria"

        # Financial capacity
        if not financial_result["capital_committed"]:
            return False, "No committed capital - M&A requires dedicated financial resources"

        return True, None

    def _determine_gate(self, overall_score, passed_requirements, failure_reason):
        """Determine gate decision using hybrid logic."""
        # Hard requirements must pass first
        if not passed_requirements:
            return PhaseGate.NO_GO, f"Hard requirement not met — {failure_reason}. Build capabilities before pursuing acquisitions."

        # Apply score thresholds
        if overall_score >= READINESS_GO_THRESHOLD:
            gate_reasoning = f"Score {overall_score:.0f}/100 — Ready for M&A activities. Proceed with deal sourcing."
            return PhaseGate.GO, gate_reasoning
        elif overall_score >= READINESS_CONDITIONAL_LOWER:
            gate_reasoning = f"Score {overall_score:.0f}/100 — Proceed with conditions: capability development recommended. Review readiness_summary.md for specific gaps."
            return PhaseGate.CONDITIONAL, gate_reasoning
        elif overall_score >= READINESS_NO_GO_THRESHOLD:
            gate_reasoning = f"Score {overall_score:.0f}/100 — Address readiness gaps before active deal sourcing. Review readiness_summary.md for required improvements."
            return PhaseGate.CONDITIONAL, gate_reasoning
        else:
            gate_reasoning = f"Score {overall_score:.0f}/100 — Build capabilities first before pursuing acquisitions."
            return PhaseGate.NO_GO, gate_reasoning

    def _generate_recommendations(self, overall_score, ceo_result, strategic_result,
                                    org_result, financial_result, governance_result):
        """Generate recommendations based on scores."""
        recommendations = []

        # CEO development
        if ceo_result["score"] < 85:
            recommendations.append("Provide M&A training for CEO and leadership team")

        # Strategic clarity
        if strategic_result["score"] < 100:
            if not strategic_result["completeness"].get("strategic_priorities_set"):
                recommendations.append("Define strategic priorities for target evaluation")

        # Organizational capacity
        if org_result["score"] < 75:
            if org_result["integration_team_size"] < 3:
                recommendations.append("Build integration team from current size to 3-5 people")

        # Financial readiness
        if not financial_result.get("methodology_defined"):
            recommendations.append("Formalize valuation methodology approach")

        # Governance
        if governance_result["score"] < 70:
            recommendations.append("Document M&A governance framework and escalation procedures")

        return recommendations
