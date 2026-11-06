"""Operations assessment analyzer."""

from corporate_development.operational_dd.types import OperationsAssessmentInput, DimensionScore, RiskFlag


class OperationsAnalyzer:
    """Analyze operations dimension for operational assessment."""

    DIMENSION = "Operations"
    WEIGHT = 0.20
    PROCESS_MATURITY_WEIGHT = 0.30
    WORKFLOW_EFFICIENCY_WEIGHT = 0.30
    DOCUMENTATION_WEIGHT = 0.20
    SCALABILITY_WEIGHT = 0.20

    def analyze(self, input_data: OperationsAssessmentInput) -> DimensionScore:
        score = round(
            input_data.process_maturity * self.PROCESS_MATURITY_WEIGHT +
            input_data.workflow_efficiency * self.WORKFLOW_EFFICIENCY_WEIGHT +
            input_data.documentation_quality * self.DOCUMENTATION_WEIGHT +
            input_data.scalability * self.SCALABILITY_WEIGHT
        )

        strengths = []
        if input_data.process_maturity >= 80:
            strengths.append("Mature operational processes")
        if input_data.workflow_efficiency >= 80:
            strengths.append("Highly efficient workflows")

        concerns = []
        if input_data.process_maturity < 60:
            concerns.append("Immature operational processes")

        risk_flags = []
        if input_data.scalability < 40:
            risk_flags.append(RiskFlag(
                severity="CRITICAL",
                category="operations",
                title="Poor operations scalability",
                description="Operations cannot scale to support growth",
                recommendation="Plan significant operations infrastructure investment"
            ))

        return DimensionScore(
            dimension=self.DIMENSION,
            score=score,
            weight=self.WEIGHT,
            strengths=strengths,
            concerns=concerns,
            risk_flags=risk_flags
        )
