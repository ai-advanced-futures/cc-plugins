"""ExecutiveSummaryGenerator for Phase 6 markdown reports."""

from corporate_development.core.phase import PhaseGate
from corporate_development.decision_framework.recommendation_synthesizer import FinalRecommendation
from corporate_development.decision_framework.types import DealRecommendationInput


class ExecutiveSummaryGenerator:
    """Generates 2-3 page markdown executive summary."""

    def generate(
        self,
        deal_input: DealRecommendationInput,
        final_recommendation: FinalRecommendation,
    ) -> str:
        """Generate executive summary markdown.

        Args:
            deal_input: Original deal input data
            final_recommendation: Final recommendation from synthesizer

        Returns:
            Markdown string with executive summary (2-3 pages)
        """
        sections = []

        # Header
        sections.append(f"# Deal Recommendation: {deal_input.company_name} ← {deal_input.acquirer_name}")
        sections.append("")

        # Executive Decision
        sections.append(self._generate_executive_decision(final_recommendation))
        sections.append("")

        # Deal Snapshot
        sections.append(self._generate_deal_snapshot(deal_input, final_recommendation))
        sections.append("")

        # Quantitative Assessment
        sections.append(self._generate_quantitative_assessment(final_recommendation))
        sections.append("")

        # Qualitative Assessment
        sections.append(self._generate_qualitative_assessment(final_recommendation))
        sections.append("")

        # Recommendation Rationale
        sections.append(self._generate_recommendation_rationale(final_recommendation))
        sections.append("")

        # Conditions (if CONDITIONAL)
        if final_recommendation.gate == PhaseGate.CONDITIONAL:
            sections.append(self._generate_conditions(final_recommendation))
            sections.append("")

        # Next Steps
        sections.append(self._generate_next_steps(final_recommendation))
        sections.append("")

        return "\n".join(sections)

    def _generate_executive_decision(self, final_rec: FinalRecommendation) -> str:
        """Generate Executive Decision section."""
        gate_text = final_rec.gate.value
        confidence_text = final_rec.confidence_level.capitalize()

        return f"""## Executive Decision

**Recommendation:** {gate_text}

**Overall Score:** {final_rec.overall_score}/100

**Confidence:** {confidence_text}"""

    def _generate_deal_snapshot(
        self,
        deal_input: DealRecommendationInput,
        final_rec: FinalRecommendation,
    ) -> str:
        """Generate Deal Snapshot section."""
        lines = ["## Deal Snapshot"]

        # Target info
        lines.append(f"- **Target:** {deal_input.company_name}")

        # Revenue if available
        if deal_input.annual_revenue:
            revenue_m = deal_input.annual_revenue / 1_000_000
            lines.append(f"- **Annual Revenue:** ${revenue_m:.1f}M")

        # Deal size if available
        if deal_input.deal_size:
            size_m = deal_input.deal_size / 1_000_000
            lines.append(f"- **Deal Size:** ${size_m:.1f}M")

        # Key risks
        risk_count = len(final_rec.qualitative_blockers) + len(final_rec.qualitative_concerns)
        if risk_count > 0:
            top_risks = (final_rec.qualitative_blockers + final_rec.qualitative_concerns)[:3]
            lines.append(f"- **Key Risks:** {', '.join(top_risks)}")
        else:
            lines.append("- **Key Risks:** None identified")

        return "\n".join(lines)

    def _generate_quantitative_assessment(self, final_rec: FinalRecommendation) -> str:
        """Generate Quantitative Assessment section."""
        lines = [f"## Quantitative Assessment (Score: {final_rec.overall_score}/100)"]
        lines.append("")

        # Overall assessment
        assessment_desc = {
            "strong": "Strong operational and financial health across key dimensions.",
            "acceptable": "Acceptable fundamentals with room for improvement.",
            "weak": "Significant operational or financial challenges identified.",
        }
        lines.append(assessment_desc.get(final_rec.quantitative_assessment, ""))
        lines.append("")

        # Dimension breakdown if available
        if final_rec.dimension_scores:
            lines.append("### Dimension Scores")
            lines.append("")
            for dimension, data in final_rec.dimension_scores.items():
                score = data.get("score")
                weight = data.get("weight", 0) * 100
                if score is not None:
                    lines.append(f"- **{dimension}:** {score}/100 (weight: {weight:.0f}%)")
            lines.append("")

        return "\n".join(lines)

    def _generate_qualitative_assessment(self, final_rec: FinalRecommendation) -> str:
        """Generate Qualitative Assessment section."""
        lines = ["## Qualitative Assessment"]
        lines.append("")

        # Critical blockers
        if final_rec.qualitative_blockers:
            lines.append("### Critical Blockers")
            lines.append("")
            for blocker in final_rec.qualitative_blockers:
                lines.append(f"- {blocker}")
            lines.append("")

        # Major concerns
        if final_rec.qualitative_concerns:
            lines.append("### Major Considerations")
            lines.append("")
            for concern in final_rec.qualitative_concerns:
                lines.append(f"- {concern}")
            lines.append("")

        # If no issues
        if not final_rec.qualitative_blockers and not final_rec.qualitative_concerns:
            lines.append("No critical strategic blockers or major concerns identified.")
            lines.append("")

        return "\n".join(lines)

    def _generate_recommendation_rationale(self, final_rec: FinalRecommendation) -> str:
        """Generate Recommendation Rationale section."""
        return f"""## Recommendation Rationale

{final_rec.recommendation_rationale}"""

    def _generate_conditions(self, final_rec: FinalRecommendation) -> str:
        """Generate Conditions section (for CONDITIONAL gate)."""
        lines = ["## Conditions"]
        lines.append("")
        lines.append("The following conditions must be satisfied before proceeding:")
        lines.append("")

        for idx, condition in enumerate(final_rec.conditions, 1):
            lines.append(f"{idx}. {condition}")

        return "\n".join(lines)

    def _generate_next_steps(self, final_rec: FinalRecommendation) -> str:
        """Generate Next Steps section."""
        lines = ["## Next Steps"]
        lines.append("")

        if final_rec.gate == PhaseGate.GO:
            lines.append("1. Proceed to Phase 7: Negotiation & Deal Structuring")
            lines.append("2. Begin integration planning activities")
            lines.append("3. Communicate decision to stakeholders")
        elif final_rec.gate == PhaseGate.CONDITIONAL:
            lines.append("1. Address conditions outlined above")
            lines.append("2. Re-evaluate once conditions are satisfied")
            lines.append("3. Consider alternative targets if conditions cannot be met")
        else:  # NO_GO
            lines.append("1. Do not proceed with this acquisition")
            lines.append("2. Document lessons learned")
            lines.append("3. Consider alternative targets or strategies")

        return "\n".join(lines)
