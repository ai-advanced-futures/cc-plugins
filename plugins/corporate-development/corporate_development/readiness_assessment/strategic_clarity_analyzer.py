# plugins/corporate-development/corporate_development/readiness_assessment/strategic_clarity_analyzer.py
"""Strategic clarity analyzer for target definition validation."""

from typing import Dict, Any
from corporate_development.readiness_assessment.types import StrategicTargetInput


class StrategicClarityAnalyzer:
    """Analyze strategic target definition completeness.

    Scores based on clarity and completeness of acquisition criteria:
    - Target industries defined
    - Revenue range set
    - Geographic focus clear
    - Strategic priorities set
    """

    def analyze(self, input_data: StrategicTargetInput) -> Dict[str, Any]:
        """Analyze strategic clarity and generate target statement.

        Args:
            input_data: Strategic target definition

        Returns:
            Dictionary with:
                - score: 0-100 based on criteria completeness
                - completeness: Dict showing which criteria are defined
                - target_statement: Human-readable acquisition target description
        """
        # Check each criterion (25 points each)
        industries_defined = len(input_data.target_industries) > 0
        revenue_range_set = (
            input_data.revenue_range_min > 0 and
            input_data.revenue_range_max > 0
        )
        geographic_focus_clear = len(input_data.geographic_focus) > 0
        strategic_priorities_set = len(input_data.strategic_priorities) > 0

        # Calculate score (4 required criteria × 25 points each)
        score = 0.0
        if industries_defined:
            score += 25.0
        if revenue_range_set:
            score += 25.0
        if geographic_focus_clear:
            score += 25.0
        if strategic_priorities_set:
            score += 25.0

        # Generate target statement
        target_statement = self._generate_target_statement(input_data)

        return {
            "score": score,
            "completeness": {
                "industries_defined": industries_defined,
                "revenue_range_set": revenue_range_set,
                "geographic_focus_clear": geographic_focus_clear,
                "strategic_priorities_set": strategic_priorities_set
            },
            "target_statement": target_statement,
            "industries": input_data.target_industries,
            "revenue_range": f"${input_data.revenue_range_min:,.0f} - ${input_data.revenue_range_max:,.0f}",
            "geographic_focus": input_data.geographic_focus,
            "strategic_priorities": input_data.strategic_priorities,
            "growth_threshold": input_data.growth_threshold_pct
        }

    def _generate_target_statement(self, input_data: StrategicTargetInput) -> str:
        """Generate human-readable target acquisition statement.

        Format: "We seek [industries] in [geography] with [revenue range]
                that provides [priorities] capabilities."
        """
        # Industries
        if len(input_data.target_industries) > 0:
            industries = ", ".join(input_data.target_industries)
        else:
            industries = "[industries not specified]"

        # Geography
        if len(input_data.geographic_focus) > 0:
            geography = ", ".join(input_data.geographic_focus)
        else:
            geography = "[geography not specified]"

        # Revenue range
        rev_min_m = input_data.revenue_range_min / 1_000_000
        rev_max_m = input_data.revenue_range_max / 1_000_000
        revenue_range = f"${rev_min_m:.1f}M-${rev_max_m:.1f}M"

        # Strategic priorities
        if len(input_data.strategic_priorities) > 0:
            priorities = input_data.strategic_priorities[0].lower()
        else:
            priorities = "strategic value"

        # Growth threshold (optional)
        growth_clause = ""
        if input_data.growth_threshold_pct is not None:
            growth_clause = f" with {input_data.growth_threshold_pct:.0f}%+ growth"

        return (
            f"We seek {industries} businesses in {geography} "
            f"with {revenue_range} revenue{growth_clause} "
            f"that provides {priorities} capabilities."
        )
