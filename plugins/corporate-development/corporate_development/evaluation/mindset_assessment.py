"""Growth mindset assessment based on Carol Dweck's research.

This module provides tools to assess CEO readiness through the lens of growth
mindset vs. fixed mindset orientation. Research shows that leaders with growth
mindsets are more adaptable and better positioned for acquisition success.

References:
    - Dweck, C. (2006). Mindset: The New Psychology of Success
    - HBR article on growth mindset in leadership
"""

from typing import Dict


class MindsetAssessment:
    """Assessment tool for measuring growth vs. fixed mindset orientation.

    Uses a 5-question framework to evaluate key mindset dimensions:
    - Learning orientation
    - Challenge response
    - Effort belief
    - Criticism reaction
    - Success of others
    """

    # Scoring rubric: Maps response types to point values (0-20 per question)
    GROWTH_SCORING = {
        "strongly_disagree": 0,
        "disagree": 5,
        "neutral": 10,
        "agree": 15,
        "strongly_agree": 20
    }

    @classmethod
    def score_growth_mindset(cls, responses: Dict[str, str]) -> int:
        """Calculate growth mindset score from question responses.

        Args:
            responses: Dictionary mapping question keys to response values.
                Expected keys:
                - learning_orientation
                - challenge_response
                - effort_belief
                - criticism_reaction
                - success_of_others

                Response values: strongly_disagree, disagree, neutral, agree, strongly_agree

        Returns:
            Integer score from 0-100 where:
            - 0-40: Fixed mindset orientation
            - 41-79: Mixed mindset orientation
            - 80-100: Growth mindset orientation

        Example:
            >>> responses = {
            ...     "learning_orientation": "strongly_agree",
            ...     "challenge_response": "agree",
            ...     "effort_belief": "strongly_agree",
            ...     "criticism_reaction": "neutral",
            ...     "success_of_others": "agree"
            ... }
            >>> MindsetAssessment.score_growth_mindset(responses)
            85
        """
        total_score = 0

        for question_key, response in responses.items():
            # Map response to point value using scoring rubric
            points = cls.GROWTH_SCORING.get(response, 0)
            total_score += points

        return total_score
