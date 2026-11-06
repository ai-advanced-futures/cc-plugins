"""CEO readiness scorer using 3 A's framework."""

from typing import Dict, Any
from corporate_development.readiness_assessment.types import CEOReadinessInput


class CEOReadinessScorer:
    """Score CEO readiness using the 3 A's framework.

    The 3 A's framework (from "Buy Then Build"):
    - Attitude: Growth mindset, character, resilience
    - Aptitude: Strategic thinking, leadership capability
    - Action: Execution track record, results delivery
    """

    MINIMUM_THRESHOLD = 7.0  # Minimum CEO score required to proceed

    def score(self, input_data: CEOReadinessInput) -> Dict[str, Any]:
        """Calculate CEO readiness score from 3 A's inputs.

        Args:
            input_data: CEO assessment scores (0-10 scale for each A)

        Returns:
            Dictionary with:
                - score: 0-100 normalized score
                - ceo_average: Raw average of 3 A's (0-10)
                - meets_threshold: Whether CEO score ≥7.0
                - overall_rating: Ready Now / Ready 6-12mo / Ready 1-2yr / Not Ready
                - key_strengths: List of strengths
                - development_areas: List of development needs
        """
        # Calculate average of 3 A's (0-10 scale)
        ceo_average = (
            input_data.attitude_score +
            input_data.aptitude_score +
            input_data.action_score
        ) / 3.0

        # Normalize to 0-100 scale
        score = ceo_average * 10.0

        # Check if meets minimum threshold
        meets_threshold = ceo_average >= self.MINIMUM_THRESHOLD

        # Determine overall rating
        overall_rating = self._determine_rating(ceo_average)

        return {
            "score": score,
            "ceo_average": ceo_average,
            "meets_threshold": meets_threshold,
            "overall_rating": overall_rating,
            "attitude_score": input_data.attitude_score,
            "aptitude_score": input_data.aptitude_score,
            "action_score": input_data.action_score,
            "assessment_context": input_data.assessment_context,
            "key_strengths": input_data.key_strengths,
            "development_areas": input_data.development_areas
        }

    def _determine_rating(self, ceo_average: float) -> str:
        """Determine readiness rating based on CEO average score.

        Ratings:
            - Ready Now: ≥8.0
            - Ready 6-12mo: 7.0-7.9
            - Ready 1-2yr: 6.0-6.9
            - Not Ready: <6.0
        """
        if ceo_average >= 8.0:
            return "Ready Now"
        elif ceo_average >= 7.0:
            return "Ready 6-12mo"
        elif ceo_average >= 6.0:
            return "Ready 1-2yr"
        else:
            return "Not Ready"
