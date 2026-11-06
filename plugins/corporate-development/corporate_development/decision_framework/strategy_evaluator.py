"""StrategyEvaluator for Phase 6 qualitative assessment."""

from typing import List
from dataclasses import dataclass

from corporate_development.decision_framework.types import DealRecommendationInput


@dataclass
class StrategicFactor:
    """Assessment of a single strategic dimension."""

    dimension: str
    rating: str  # "strong", "acceptable", "weak", "concerning"
    rationale: str
    concerns: List[str]


@dataclass
class QualitativeAssessment:
    """Result of qualitative strategic assessment."""

    factors: List[StrategicFactor]
    critical_blockers: List[str]
    major_concerns: List[str]
    minor_concerns: List[str]


class StrategyEvaluator:
    """Evaluates qualitative strategic factors for Phase 6.

    Analyzes 7 dimensions:
    1. Strategic Fit & Rationale
    2. Leadership Team Assessment
    3. Customer Risk Analysis
    4. Competitive Positioning
    5. Technology & IP Considerations
    6. Cultural Compatibility
    7. Market Timing & Dynamics

    Identifies critical blockers (single issue blocks deal),
    major concerns (multiple can block deal), and minor issues.
    """

    def evaluate_strategic_factors(self, deal_input: DealRecommendationInput) -> QualitativeAssessment:
        """Perform comprehensive qualitative assessment.

        Args:
            deal_input: Validated deal input with strategic context

        Returns:
            QualitativeAssessment with factor ratings and blocker lists
        """
        factors: List[StrategicFactor] = []
        critical_blockers: List[str] = []
        major_concerns: List[str] = []
        minor_concerns: List[str] = []

        # 1. Strategic Fit & Rationale
        strategic_fit = self._evaluate_strategic_fit(deal_input)
        factors.append(strategic_fit)
        if strategic_fit.rating == "weak":
            critical_blockers.extend(strategic_fit.concerns)
        elif strategic_fit.rating == "concerning":
            major_concerns.extend(strategic_fit.concerns)

        # 2. Leadership Team Assessment
        leadership = self._evaluate_leadership(deal_input)
        factors.append(leadership)
        if leadership.rating == "weak":
            major_concerns.extend(leadership.concerns)
        elif leadership.rating == "concerning":
            minor_concerns.extend(leadership.concerns)

        # 3. Customer Risk Analysis
        customer_risk = self._evaluate_customer_risk(deal_input)
        factors.append(customer_risk)
        if customer_risk.rating == "weak":
            critical_blockers.extend(customer_risk.concerns)
        elif customer_risk.rating == "concerning":
            major_concerns.extend(customer_risk.concerns)

        # 4. Competitive Positioning
        competitive = self._evaluate_competitive_position(deal_input)
        factors.append(competitive)
        if competitive.rating == "weak":
            major_concerns.extend(competitive.concerns)
        elif competitive.rating == "concerning":
            minor_concerns.extend(competitive.concerns)

        # 5. Technology & IP Considerations
        technology = self._evaluate_technology_ip(deal_input)
        factors.append(technology)
        if technology.rating == "weak":
            major_concerns.extend(technology.concerns)
        elif technology.rating == "concerning":
            minor_concerns.extend(technology.concerns)

        # 6. Cultural Compatibility
        culture = self._evaluate_cultural_compatibility(deal_input)
        factors.append(culture)
        if culture.rating == "weak":
            major_concerns.extend(culture.concerns)
        elif culture.rating == "concerning":
            minor_concerns.extend(culture.concerns)

        # 7. Market Timing & Dynamics
        timing = self._evaluate_market_timing(deal_input)
        factors.append(timing)
        if timing.rating == "weak":
            major_concerns.extend(timing.concerns)
        elif timing.rating == "concerning":
            minor_concerns.extend(timing.concerns)

        return QualitativeAssessment(
            factors=factors,
            critical_blockers=critical_blockers,
            major_concerns=major_concerns,
            minor_concerns=minor_concerns,
        )

    def _evaluate_strategic_fit(self, deal_input: DealRecommendationInput) -> StrategicFactor:
        """Evaluate strategic fit and rationale."""
        concerns = []

        # Check if Phase 2 assessment available
        if deal_input.phase_2_assessment:
            score = deal_input.phase_2_assessment.strategic_fit_score
            if score >= 80:
                rating = "strong"
                rationale = f"Strong strategic alignment (score: {score}/100)"
            elif score >= 60:
                rating = "acceptable"
                rationale = f"Acceptable strategic fit (score: {score}/100)"
            else:
                rating = "weak"
                rationale = f"Weak strategic fit (score: {score}/100)"
                concerns.append(f"Low strategic fit score ({score}/100)")
        else:
            rating = "acceptable"
            rationale = "Strategic fit not formally assessed"
            concerns.append("No Phase 2 strategic assessment available")

        return StrategicFactor(
            dimension="Strategic Fit",
            rating=rating,
            rationale=rationale,
            concerns=concerns,
        )

    def _evaluate_leadership(self, deal_input: DealRecommendationInput) -> StrategicFactor:
        """Evaluate leadership team and retention risk."""
        concerns = []

        if deal_input.team_strength:
            if deal_input.team_strength == "strong":
                rating = "strong"
                rationale = "Strong leadership team with low retention risk"
            elif deal_input.team_strength == "medium":
                rating = "acceptable"
                rationale = "Adequate leadership team"
                concerns.append("Some leadership retention risk")
            else:  # weak
                rating = "weak"
                rationale = "Weak leadership team or high retention risk"
                concerns.append("Significant leadership retention risk")
        else:
            rating = "acceptable"
            rationale = "Leadership team assessment not available"

        return StrategicFactor(
            dimension="Leadership Team",
            rating=rating,
            rationale=rationale,
            concerns=concerns,
        )

    def _evaluate_customer_risk(self, deal_input: DealRecommendationInput) -> StrategicFactor:
        """Evaluate customer concentration and churn risk."""
        concerns = []

        if deal_input.customer_concentration:
            if deal_input.customer_concentration == "low":
                rating = "strong"
                rationale = "Well-diversified customer base"
            elif deal_input.customer_concentration == "medium":
                rating = "concerning"
                rationale = "Moderate customer concentration"
                concerns.append("Monitor customer concentration trends")
            else:  # high
                rating = "weak"
                rationale = "High customer concentration (>40% from top 3)"
                concerns.append("Critical dependency on few customers")
        else:
            rating = "acceptable"
            rationale = "Customer concentration data not available"

        return StrategicFactor(
            dimension="Customer Risk",
            rating=rating,
            rationale=rationale,
            concerns=concerns,
        )

    def _evaluate_competitive_position(self, deal_input: DealRecommendationInput) -> StrategicFactor:
        """Evaluate competitive positioning and defensibility."""
        concerns = []

        if deal_input.competitive_position:
            if deal_input.competitive_position == "strong":
                rating = "strong"
                rationale = "Strong competitive position with defensible moat"
            elif deal_input.competitive_position == "medium":
                rating = "acceptable"
                rationale = "Adequate competitive position"
                concerns.append("Competitive position could be stronger")
            else:  # weak
                rating = "weak"
                rationale = "Weak competitive position"
                concerns.append("Vulnerable to competitive pressure")
        else:
            rating = "acceptable"
            rationale = "Competitive position assessment not available"

        return StrategicFactor(
            dimension="Competitive Position",
            rating=rating,
            rationale=rationale,
            concerns=concerns,
        )

    def _evaluate_technology_ip(self, deal_input: DealRecommendationInput) -> StrategicFactor:
        """Evaluate technology moat and IP considerations."""
        concerns = []

        if deal_input.tech_debt_level:
            if deal_input.tech_debt_level == "low":
                rating = "strong"
                rationale = "Modern tech stack with minimal debt"
            elif deal_input.tech_debt_level == "medium":
                rating = "concerning"
                rationale = "Moderate technical debt"
                concerns.append("Technical debt modernization needed")
            else:  # high
                rating = "weak"
                rationale = "High technical debt or outdated technology"
                concerns.append("Significant technology modernization required")
        else:
            rating = "acceptable"
            rationale = "Technology assessment not available"

        return StrategicFactor(
            dimension="Technology & IP",
            rating=rating,
            rationale=rationale,
            concerns=concerns,
        )

    def _evaluate_cultural_compatibility(self, deal_input: DealRecommendationInput) -> StrategicFactor:
        """Evaluate cultural compatibility between organizations."""
        # For now, assume acceptable unless Phase 5 integration complexity suggests otherwise
        concerns = []
        rating = "acceptable"
        rationale = "Cultural assessment not formally conducted"

        if deal_input.phase_5_integration:
            if deal_input.phase_5_integration.complexity_rating == "high":
                rating = "concerning"
                rationale = "High integration complexity may indicate cultural mismatch"
                concerns.append("Cultural integration challenges anticipated")

        return StrategicFactor(
            dimension="Cultural Compatibility",
            rating=rating,
            rationale=rationale,
            concerns=concerns,
        )

    def _evaluate_market_timing(self, deal_input: DealRecommendationInput) -> StrategicFactor:
        """Evaluate market timing and dynamics."""
        concerns = []

        # Check Phase 2 market position as proxy for timing
        if deal_input.phase_2_assessment:
            if deal_input.phase_2_assessment.market_position == "leader":
                rating = "strong"
                rationale = "Acquiring market leader at optimal time"
            else:
                rating = "acceptable"
                rationale = "Market timing appears reasonable"
        else:
            rating = "acceptable"
            rationale = "Market timing assessment not available"

        return StrategicFactor(
            dimension="Market Timing",
            rating=rating,
            rationale=rationale,
            concerns=concerns,
        )
