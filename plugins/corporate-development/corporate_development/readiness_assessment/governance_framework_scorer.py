"""Governance framework scorer for decision gates and risk management."""

from typing import Dict, Any
from corporate_development.readiness_assessment.types import GovernanceFrameworkInput


class GovernanceFrameworkScorer:
    """Score governance maturity and decision framework.

    Scoring:
    - Board approval process defined: +40 points
    - Risk tolerance defined: +30 points
    - Timeline expectations set: +30 points
    """

    def score(self, input_data: GovernanceFrameworkInput) -> Dict[str, Any]:
        """Calculate governance framework score.

        Args:
            input_data: Governance framework assessment data

        Returns:
            Dictionary with:
                - score: 0-100 based on governance maturity
                - board_process_defined: Boolean indicating if board approval required
                - risk_defined: Boolean indicating if risk tolerance set
                - timeline_set: Boolean indicating if timeline expectations set
        """
        score = 0.0

        # Board approval process (40 points)
        board_process_defined = input_data.board_approval_required
        if board_process_defined:
            score += 40.0

        # Risk tolerance defined (30 points)
        risk_defined = input_data.risk_tolerance is not None
        if risk_defined:
            score += 30.0

        # Timeline expectations set (30 points)
        timeline_set = input_data.timeline_expectation_months > 0
        if timeline_set:
            score += 30.0

        return {
            "score": score,
            "board_process_defined": board_process_defined,
            "risk_defined": risk_defined,
            "timeline_set": timeline_set,
            "board_approval_required": input_data.board_approval_required,
            "risk_tolerance": input_data.risk_tolerance if input_data.risk_tolerance else "",
            "timeline_expectation_months": input_data.timeline_expectation_months,
            "deal_breakers": input_data.deal_breakers
        }
