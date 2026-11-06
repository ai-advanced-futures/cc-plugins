"""Product assessment analyzer."""

from corporate_development.operational_dd.types import ProductAssessmentInput, DimensionScore, RiskFlag


class ProductAnalyzer:
    """Analyze product dimension for operational assessment."""

    DIMENSION = "Product"
    WEIGHT = 0.20
    PRODUCT_QUALITY_WEIGHT = 0.30
    ROADMAP_CLARITY_WEIGHT = 0.30
    CUSTOMER_SATISFACTION_WEIGHT = 0.20
    FEATURE_COMPLETENESS_WEIGHT = 0.20

    def analyze(self, input_data: ProductAssessmentInput) -> DimensionScore:
        score = round(
            input_data.product_quality * self.PRODUCT_QUALITY_WEIGHT +
            input_data.roadmap_clarity * self.ROADMAP_CLARITY_WEIGHT +
            input_data.customer_satisfaction * self.CUSTOMER_SATISFACTION_WEIGHT +
            input_data.feature_completeness * self.FEATURE_COMPLETENESS_WEIGHT
        )

        strengths = []
        if input_data.product_quality >= 80:
            strengths.append("High product quality")
        if input_data.customer_satisfaction >= 85:
            strengths.append("Excellent customer satisfaction")

        concerns = []
        if input_data.product_quality < 60:
            concerns.append("Poor product quality")

        risk_flags = []
        if input_data.customer_satisfaction < 50:
            risk_flags.append(RiskFlag(
                severity="CRITICAL",
                category="product",
                title="Very low customer satisfaction",
                description="Customer satisfaction below 50% indicates serious product issues",
                recommendation="Conduct customer interviews to identify and address critical pain points"
            ))

        return DimensionScore(
            dimension=self.DIMENSION,
            score=score,
            weight=self.WEIGHT,
            strengths=strengths,
            concerns=concerns,
            risk_flags=risk_flags
        )
