"""Team assessment analyzer."""

from typing import List
from corporate_development.operational_dd.types import TeamAssessmentInput, DimensionScore, RiskFlag


class TeamAnalyzer:
    """Analyze team dimension for operational assessment."""

    DIMENSION = "Team"
    WEIGHT = 0.25

    # Sub-metric weights
    LEADERSHIP_WEIGHT = 0.30
    SKILL_COVERAGE_WEIGHT = 0.30
    RETENTION_WEIGHT = 0.20
    KEY_PERSON_WEIGHT = 0.20

    def analyze(self, input_data: TeamAssessmentInput) -> DimensionScore:
        """Analyze team assessment input and calculate score."""
        # Convert retention rate to score (0.0-1.0 → 0-100)
        retention_score = int(input_data.retention_rate * 100)

        # Convert key person risk to score (False = 100, True = 50)
        key_person_score = 50 if input_data.key_person_risk else 100

        # Calculate weighted score
        score = round(
            input_data.leadership_quality * self.LEADERSHIP_WEIGHT +
            input_data.skill_coverage * self.SKILL_COVERAGE_WEIGHT +
            retention_score * self.RETENTION_WEIGHT +
            key_person_score * self.KEY_PERSON_WEIGHT
        )

        # Identify strengths and concerns
        strengths = self._identify_strengths(input_data, retention_score, key_person_score)
        concerns = self._identify_concerns(input_data, retention_score, key_person_score)

        # Identify risk flags
        risk_flags = self._identify_risks(input_data, retention_score, key_person_score)

        return DimensionScore(
            dimension=self.DIMENSION,
            score=score,
            weight=self.WEIGHT,
            strengths=strengths,
            concerns=concerns,
            risk_flags=risk_flags
        )

    def _identify_strengths(self, input_data: TeamAssessmentInput, retention_score: int, key_person_score: int) -> List[str]:
        """Identify team strengths."""
        strengths = []

        if input_data.leadership_quality >= 80:
            strengths.append("Strong leadership team")

        if input_data.skill_coverage >= 80:
            strengths.append("Comprehensive skill coverage")

        if retention_score >= 90:
            strengths.append("Excellent employee retention")

        if key_person_score == 100:
            strengths.append("No critical key person dependencies")

        return strengths

    def _identify_concerns(self, input_data: TeamAssessmentInput, retention_score: int, key_person_score: int) -> List[str]:
        """Identify team concerns."""
        concerns = []

        if input_data.leadership_quality < 60:
            concerns.append("Weak leadership team")

        if input_data.skill_coverage < 60:
            concerns.append("Significant skill gaps")

        if retention_score < 80:
            concerns.append("High employee turnover")

        if key_person_score == 50:
            concerns.append("Critical key person dependencies")

        return concerns

    def _identify_risks(self, input_data: TeamAssessmentInput, retention_score: int, key_person_score: int) -> List[RiskFlag]:
        """Identify team-related risk flags."""
        risks = []

        # Critical risks
        if input_data.key_person_risk:
            risks.append(RiskFlag(
                severity="CRITICAL",
                category="team",
                title="Key person dependency risk",
                description="Significant revenue or operations depend on key individuals",
                recommendation="Document critical processes and cross-train team members"
            ))

        if retention_score < 70:
            risks.append(RiskFlag(
                severity="CRITICAL",
                category="team",
                title="High employee turnover",
                description=f"Retention rate of {input_data.retention_rate:.0%} indicates instability",
                recommendation="Investigate turnover causes and implement retention initiatives"
            ))

        # Warning risks
        if input_data.leadership_quality < 60:
            risks.append(RiskFlag(
                severity="WARNING",
                category="team",
                title="Weak leadership capability",
                description="Leadership team may struggle to execute growth plans",
                recommendation="Consider leadership coaching or supplemental hires"
            ))

        if input_data.skill_coverage < 60:
            risks.append(RiskFlag(
                severity="WARNING",
                category="team",
                title="Skill coverage gaps",
                description="Missing critical skills for operations",
                recommendation="Identify and fill critical skill gaps pre-close"
            ))

        # Info risks
        if input_data.headcount < 20:
            risks.append(RiskFlag(
                severity="INFO",
                category="team",
                title="Small team size",
                description=f"Team of {input_data.headcount} may limit scaling capacity",
                recommendation="Plan for strategic hiring post-acquisition"
            ))

        return risks
