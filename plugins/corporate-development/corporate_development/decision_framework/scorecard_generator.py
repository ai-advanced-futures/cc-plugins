"""ScorecardGenerator for Phase 6 JSON scorecards."""

import json
from datetime import datetime, timezone

from corporate_development.decision_framework.recommendation_synthesizer import FinalRecommendation
from corporate_development.decision_framework.types import DealRecommendationInput


class ScorecardGenerator:
    """Generates machine-readable JSON scorecard."""

    def generate(
        self,
        deal_input: DealRecommendationInput,
        final_recommendation: FinalRecommendation,
    ) -> str:
        """Generate scorecard JSON.

        Args:
            deal_input: Original deal input data
            final_recommendation: Final recommendation from synthesizer

        Returns:
            JSON string with scorecard data
        """
        scorecard = {
            "target_name": deal_input.company_name,
            "acquirer_name": deal_input.acquirer_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_score": final_recommendation.overall_score,
            "recommendation": final_recommendation.gate.value,
            "confidence": final_recommendation.confidence_level,
            "dimension_scores": final_recommendation.dimension_scores,
            "qualitative_assessment": {
                "quantitative_rating": final_recommendation.quantitative_assessment,
                "critical_blockers": final_recommendation.qualitative_blockers,
                "major_concerns": final_recommendation.qualitative_concerns,
            },
            "data_completeness": self._calculate_data_completeness(
                deal_input,
                final_recommendation,
            ),
        }

        return json.dumps(scorecard, indent=2)

    def _calculate_data_completeness(
        self,
        deal_input: DealRecommendationInput,
        final_rec: FinalRecommendation,
    ) -> dict:
        """Calculate data completeness metrics.

        Args:
            deal_input: Original input
            final_rec: Final recommendation

        Returns:
            Dict with completeness metrics
        """
        # Count optional fields present
        optional_fields = [
            "phase_0_readiness",
            "phase_2_assessment",
            "phase_5_integration",
            "annual_revenue",
            "deal_size",
            "team_strength",
            "tech_debt_level",
            "customer_concentration",
            "competitive_position",
        ]

        present_count = sum(
            1 for field in optional_fields
            if getattr(deal_input, field) is not None
        )
        total_count = len(optional_fields)

        return {
            "required_fields_present": True,  # Already validated by Pydantic
            "optional_fields_present": present_count / total_count,
            "confidence_impact": final_rec.confidence_level,
        }
