# plugins/corporate-development/corporate_development/readiness_assessment/organizational_capacity_scorer.py
"""Organizational capacity scorer for integration readiness."""

from typing import Dict, Any
from corporate_development.readiness_assessment.types import OrganizationalCapacityInput


class OrganizationalCapacityScorer:
    """Score organizational integration capacity and M&A readiness.

    Weighted scoring:
    - Prior M&A experience: 40%
    - Integration team size: 30%
    - Cultural readiness: 30%
    """

    # Weights for each dimension
    EXPERIENCE_WEIGHT = 0.40
    TEAM_SIZE_WEIGHT = 0.30
    CULTURE_WEIGHT = 0.30

    def score(self, input_data: OrganizationalCapacityInput) -> Dict[str, Any]:
        """Calculate organizational capacity score.

        Args:
            input_data: Organizational capacity assessment data

        Returns:
            Dictionary with:
                - score: 0-100 weighted score
                - experience_points: Points from M&A experience (0-100)
                - team_points: Points from integration team size (0-100)
                - culture_points: Points from cultural readiness (0-100)
        """
        # Score each dimension
        experience_points = self._score_experience(input_data.prior_mna_experience)
        team_points = self._score_team_size(input_data.integration_team_size)
        culture_points = self._score_culture(input_data.cultural_readiness)

        # Calculate weighted score
        score = (
            experience_points * self.EXPERIENCE_WEIGHT +
            team_points * self.TEAM_SIZE_WEIGHT +
            culture_points * self.CULTURE_WEIGHT
        )

        return {
            "score": score,
            "experience_points": experience_points,
            "team_points": team_points,
            "culture_points": culture_points,
            "prior_mna_experience": input_data.prior_mna_experience,
            "integration_team_size": input_data.integration_team_size,
            "integration_philosophy": input_data.integration_philosophy,
            "cultural_readiness": input_data.cultural_readiness
        }

    def _score_experience(self, experience_level: str) -> float:
        """Score prior M&A experience.

        Mapping:
            - none: 0 points
            - limited: 33 points
            - moderate: 67 points
            - extensive: 100 points
        """
        mapping = {
            "none": 0,
            "limited": 33,
            "moderate": 67,
            "extensive": 100
        }
        return mapping.get(experience_level, 0)

    def _score_team_size(self, team_size: int) -> float:
        """Score integration team size.

        Mapping:
            - 0 people: 0 points
            - 1-2 people: 50 points
            - 3-5 people: 75 points
            - 6+ people: 100 points
        """
        if team_size == 0:
            return 0
        elif team_size <= 2:
            return 50
        elif team_size <= 5:
            return 75
        else:
            return 100

    def _score_culture(self, cultural_readiness: str) -> float:
        """Score cultural readiness for acquisitions.

        Mapping:
            - low: 33 points
            - medium: 67 points
            - high: 100 points
        """
        mapping = {
            "low": 33,
            "medium": 67,
            "high": 100
        }
        return mapping.get(cultural_readiness, 0)
