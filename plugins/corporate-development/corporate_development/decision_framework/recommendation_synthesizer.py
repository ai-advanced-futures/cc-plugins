"""RecommendationSynthesizer for Phase 6 final decision."""

from typing import List
from dataclasses import dataclass

from corporate_development.core.phase import PhaseGate
from corporate_development.decision_framework.score_aggregator import AggregationResult
from corporate_development.decision_framework.strategy_evaluator import QualitativeAssessment


@dataclass
class FinalRecommendation:
    """Final Phase 6 recommendation."""

    gate: PhaseGate
    overall_score: float
    dimension_scores: dict
    quantitative_assessment: str  # "strong", "acceptable", "weak"
    qualitative_blockers: List[str]
    qualitative_concerns: List[str]
    recommendation_rationale: str
    conditions: List[str]
    confidence_level: str  # "high", "medium", "low"


class RecommendationSynthesizer:
    """Synthesizes quantitative and qualitative assessments into final recommendation.

    Applies balanced judgment decision matrix where BOTH dimensions must pass:
    - Quantitative score ≥75 (strong) or 60-74 (acceptable) or <60 (weak)
    - Qualitative: no critical blockers, limited major concerns

    Decision Matrix:
    - ≥75 + no critical blockers → GO
    - ≥75 + 1+ critical blockers → NO_GO (qualitative veto)
    - 60-74 + no critical blockers → CONDITIONAL (address score gaps)
    - 60-74 + 1+ major concerns → NO_GO (combined risk too high)
    - 60-74 + only minor concerns → CONDITIONAL (address both)
    - <60 + any qualitative state → NO_GO (quantitative veto)
    """

    def synthesize_recommendation(
        self,
        aggregation: AggregationResult,
        qualitative: QualitativeAssessment,
    ) -> FinalRecommendation:
        """Combine quantitative and qualitative assessments.

        Args:
            aggregation: Quantitative score aggregation result
            qualitative: Qualitative strategic assessment result

        Returns:
            FinalRecommendation with gate decision, rationale, and conditions
        """
        # Classify quantitative assessment
        quant_assessment = self._classify_quantitative(aggregation.overall_score)

        # Check qualitative blockers
        has_critical_blockers = len(qualitative.critical_blockers) > 0
        major_concern_count = len(qualitative.major_concerns)

        # Apply balanced judgment decision matrix
        gate, rationale, conditions = self._apply_decision_matrix(
            quant_assessment,
            aggregation.overall_score,
            has_critical_blockers,
            major_concern_count,
            qualitative.critical_blockers,
            qualitative.major_concerns,
        )

        # Calculate confidence level
        confidence = self._calculate_confidence(aggregation, qualitative)

        # Build dimension scores dict
        dimension_scores_dict = {
            ds.dimension: {
                "score": ds.score,
                "weight": ds.weight,
                "weighted_score": ds.weighted_score,
            }
            for ds in aggregation.dimension_scores
        }

        return FinalRecommendation(
            gate=gate,
            overall_score=aggregation.overall_score,
            dimension_scores=dimension_scores_dict,
            quantitative_assessment=quant_assessment,
            qualitative_blockers=qualitative.critical_blockers,
            qualitative_concerns=qualitative.major_concerns,
            recommendation_rationale=rationale,
            conditions=conditions,
            confidence_level=confidence,
        )

    def _classify_quantitative(self, score: float) -> str:
        """Classify quantitative score.

        Args:
            score: Overall quantitative score (0-100)

        Returns:
            "strong" (≥75), "acceptable" (60-74), or "weak" (<60)
        """
        if score >= 75:
            return "strong"
        elif score >= 60:
            return "acceptable"
        else:
            return "weak"

    def _apply_decision_matrix(
        self,
        quant_assessment: str,
        score: float,
        has_critical_blockers: bool,
        major_concern_count: int,
        critical_blockers: List[str],
        major_concerns: List[str],
    ) -> tuple:
        """Apply balanced judgment decision matrix.

        Returns:
            Tuple of (gate, rationale, conditions)
        """
        # Rule 1: Weak quantitative score → NO_GO (quantitative veto)
        if quant_assessment == "weak":
            return (
                PhaseGate.NO_GO,
                f"Quantitative score ({score:.1f}/100) below acceptable threshold (60). "
                "Fundamental operational or financial issues must be resolved.",
                []
            )

        # Rule 2: Critical blocker present → NO_GO (qualitative veto)
        if has_critical_blockers:
            blockers_text = "; ".join(critical_blockers)
            return (
                PhaseGate.NO_GO,
                f"Critical strategic blockers identified: {blockers_text}. "
                "These issues cannot be mitigated post-acquisition.",
                []
            )

        # Rule 3: Strong quantitative + multiple major concerns → CONDITIONAL
        if quant_assessment == "strong" and major_concern_count >= 2:
            return (
                PhaseGate.CONDITIONAL,
                f"Strong operational/financial health (score: {score:.1f}/100) but "
                f"{major_concern_count} major strategic concerns require resolution. "
                "Proceed only if concerns can be adequately mitigated.",
                self._generate_conditions_for_concerns(major_concerns)
            )

        # Rule 4: Strong quantitative + no major concerns → GO
        if quant_assessment == "strong":
            return (
                PhaseGate.GO,
                f"Strong operational and financial health (score: {score:.1f}/100) with "
                "no critical strategic blockers. Deal aligns with strategic objectives.",
                []
            )

        # Rule 5: Acceptable quantitative + 2+ major concerns → NO_GO
        if quant_assessment == "acceptable" and major_concern_count >= 2:
            return (
                PhaseGate.NO_GO,
                f"Acceptable operational/financial health (score: {score:.1f}/100) "
                "insufficient to overcome multiple strategic risks. Combined risk too high.",
                []
            )

        # Rule 6: Acceptable quantitative + 0-1 major concerns → CONDITIONAL
        if quant_assessment == "acceptable":
            conditions = []

            # Add conditions for score improvement
            conditions.append(f"Improve operational/financial health from {score:.1f} to ≥75")

            # Add conditions for major concerns
            if major_concern_count > 0:
                conditions.extend(self._generate_conditions_for_concerns(major_concerns))

            return (
                PhaseGate.CONDITIONAL,
                f"Acceptable fundamentals (score: {score:.1f}/100) with addressable concerns. "
                "Proceed only after satisfying conditions.",
                conditions
            )

        # Fallback (should not reach here)
        return (
            PhaseGate.CONDITIONAL,
            "Unable to determine clear recommendation. Further assessment required.",
            ["Complete comprehensive due diligence"]
        )

    def _generate_conditions_for_concerns(self, major_concerns: List[str]) -> List[str]:
        """Generate specific conditions from major concerns.

        Args:
            major_concerns: List of major concern descriptions

        Returns:
            List of actionable conditions
        """
        conditions = []

        for concern in major_concerns:
            # Convert concern to actionable condition
            if "leadership" in concern.lower() or "team" in concern.lower():
                conditions.append("Secure retention agreements with key leaders")
            elif "customer" in concern.lower():
                conditions.append("Develop customer diversification plan")
            elif "competitive" in concern.lower():
                conditions.append("Strengthen competitive moat and differentiation")
            elif "technology" in concern.lower() or "tech" in concern.lower():
                conditions.append("Create technology modernization roadmap")
            elif "cultural" in concern.lower():
                conditions.append("Develop cultural integration plan")
            else:
                conditions.append(f"Address concern: {concern}")

        return conditions

    def _calculate_confidence(
        self,
        aggregation: AggregationResult,
        qualitative: QualitativeAssessment,
    ) -> str:
        """Calculate confidence level based on data completeness.

        Args:
            aggregation: Quantitative aggregation with missing dimensions info
            qualitative: Qualitative assessment

        Returns:
            "high" (all data present), "medium" (some missing), or "low" (minimal data)
        """
        missing_count = len(aggregation.missing_dimensions)

        if missing_count == 0:
            return "high"
        elif missing_count <= 3:
            return "medium"
        else:
            return "low"
