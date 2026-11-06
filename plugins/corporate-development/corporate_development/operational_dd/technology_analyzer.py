"""Technology assessment analyzer."""

from typing import List
from corporate_development.operational_dd.types import TechnologyAssessmentInput, DimensionScore, RiskFlag


class TechnologyAnalyzer:
    """Analyze technology dimension for operational assessment."""

    DIMENSION = "Technology"
    WEIGHT = 0.25

    # Sub-metric weights
    ARCHITECTURE_WEIGHT = 0.30
    TECH_DEBT_WEIGHT = 0.30
    SCALABILITY_WEIGHT = 0.40

    # Tech debt level mappings
    TECH_DEBT_SCORES = {
        "LOW": 90,
        "MEDIUM": 60,
        "HIGH": 30
    }

    def analyze(self, input_data: TechnologyAssessmentInput) -> DimensionScore:
        """Analyze technology assessment input and calculate score."""
        # Convert tech debt level to score
        tech_debt_score = self.TECH_DEBT_SCORES.get(input_data.technical_debt_level, 60)

        # Calculate weighted score
        score = round(
            input_data.architecture_quality * self.ARCHITECTURE_WEIGHT +
            tech_debt_score * self.TECH_DEBT_WEIGHT +
            input_data.scalability_score * self.SCALABILITY_WEIGHT
        )

        # Identify strengths and concerns
        strengths = self._identify_strengths(input_data, tech_debt_score)
        concerns = self._identify_concerns(input_data, tech_debt_score)

        # Identify risk flags
        risk_flags = self._identify_risks(input_data, tech_debt_score)

        return DimensionScore(
            dimension=self.DIMENSION,
            score=score,
            weight=self.WEIGHT,
            strengths=strengths,
            concerns=concerns,
            risk_flags=risk_flags
        )

    def _identify_strengths(self, input_data: TechnologyAssessmentInput, tech_debt_score: int) -> List[str]:
        """Identify technology strengths."""
        strengths = []

        if input_data.architecture_quality >= 80:
            strengths.append("Well-designed architecture")

        if tech_debt_score >= 80:
            strengths.append("Low technical debt")

        if input_data.scalability_score >= 80:
            strengths.append("Highly scalable infrastructure")

        if len(input_data.tech_stack) > 0:
            modern_tech = ["Python", "React", "TypeScript", "Go", "Rust", "Kubernetes"]
            if any(tech in input_data.tech_stack for tech in modern_tech):
                strengths.append("Modern technology stack")

        return strengths

    def _identify_concerns(self, input_data: TechnologyAssessmentInput, tech_debt_score: int) -> List[str]:
        """Identify technology concerns."""
        concerns = []

        if input_data.architecture_quality < 60:
            concerns.append("Poor architecture quality")

        if tech_debt_score < 60:
            concerns.append("Significant technical debt")

        if input_data.scalability_score < 60:
            concerns.append("Limited scalability")

        return concerns

    def _identify_risks(self, input_data: TechnologyAssessmentInput, tech_debt_score: int) -> List[RiskFlag]:
        """Identify technology-related risk flags."""
        risks = []

        # Critical risks
        if input_data.architecture_quality < 40:
            risks.append(RiskFlag(
                severity="CRITICAL",
                category="technology",
                title="Poor architecture quality",
                description="Architecture may not support growth or integration",
                recommendation="Conduct architecture review and plan remediation"
            ))

        if input_data.technical_debt_level == "HIGH":
            risks.append(RiskFlag(
                severity="CRITICAL",
                category="technology",
                title="High technical debt",
                description="Significant technical debt will impede development velocity",
                recommendation="Budget time and resources for debt reduction post-acquisition"
            ))

        # Warning risks
        if input_data.scalability_score < 60:
            risks.append(RiskFlag(
                severity="WARNING",
                category="technology",
                title="Limited scalability",
                description="Infrastructure may not handle growth without investment",
                recommendation="Plan infrastructure upgrades to support scaling"
            ))

        return risks
