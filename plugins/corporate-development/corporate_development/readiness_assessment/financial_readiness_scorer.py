"""Financial readiness scorer for capital and deal structure preparedness."""

from typing import Dict, Any
from corporate_development.readiness_assessment.types import FinancialReadinessInput


class FinancialReadinessScorer:
    """Score financial preparedness for acquisitions.

    Scoring:
    - Has capital committed: +40 points
    - Has valuation methodology: +30 points
    - Deal size aligned with capital: +30 points
    """

    def score(self, input_data: FinancialReadinessInput) -> Dict[str, Any]:
        """Calculate financial readiness score.

        Args:
            input_data: Financial readiness assessment data

        Returns:
            Dictionary with:
                - score: 0-100 based on financial preparedness
                - capital_committed: Boolean indicating if capital > 0
                - methodology_defined: Boolean indicating if methodology set
                - size_aligned: Boolean indicating if deal size <= max capital
        """
        score = 0.0

        # Check capital commitment (40 points)
        capital_committed = input_data.available_capital_min > 0
        if capital_committed:
            score += 40.0

        # Check valuation methodology (30 points)
        methodology_defined = input_data.valuation_methodology is not None
        if methodology_defined:
            score += 30.0

        # Check deal size alignment (30 points)
        size_aligned = input_data.max_deal_size <= input_data.available_capital_max
        if size_aligned:
            score += 30.0

        return {
            "score": score,
            "capital_committed": capital_committed,
            "methodology_defined": methodology_defined,
            "size_aligned": size_aligned,
            "available_capital": f"${input_data.available_capital_min:,.0f} - ${input_data.available_capital_max:,.0f}",
            "preferred_deal_structure": input_data.preferred_deal_structure,
            "valuation_methodology": input_data.valuation_methodology if input_data.valuation_methodology else "",
            "max_deal_size": input_data.max_deal_size
        }
