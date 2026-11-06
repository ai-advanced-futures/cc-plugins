"""Market position assessment analyzer."""

from corporate_development.operational_dd.types import MarketPositionInput, DimensionScore, RiskFlag


class MarketAnalyzer:
    """Analyze market position dimension for operational assessment."""

    DIMENSION = "Market Position"
    WEIGHT = 0.10
    COMPETITIVE_STANDING_WEIGHT = 0.40
    MOAT_STRENGTH_WEIGHT = 0.35
    DIFFERENTIATION_WEIGHT = 0.25

    def analyze(self, input_data: MarketPositionInput) -> DimensionScore:
        score = round(
            input_data.competitive_standing * self.COMPETITIVE_STANDING_WEIGHT +
            input_data.moat_strength * self.MOAT_STRENGTH_WEIGHT +
            input_data.differentiation * self.DIFFERENTIATION_WEIGHT
        )

        strengths = []
        if input_data.competitive_standing >= 80:
            strengths.append("Strong competitive position")
        if input_data.moat_strength >= 80:
            strengths.append("Defensible competitive moat")

        concerns = []
        if input_data.moat_strength < 60:
            concerns.append("Weak competitive moat")

        risk_flags = []
        if input_data.moat_strength < 40:
            risk_flags.append(RiskFlag(
                severity="CRITICAL",
                category="market",
                title="No competitive moat",
                description="Lack of defensibility makes business vulnerable to competition",
                recommendation="Identify or build sustainable competitive advantages"
            ))

        return DimensionScore(
            dimension=self.DIMENSION,
            score=score,
            weight=self.WEIGHT,
            strengths=strengths,
            concerns=concerns,
            risk_flags=risk_flags
        )
