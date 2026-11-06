"""ScoreAggregator for Phase 6 weighted scoring."""

from typing import Dict, List, Optional
from dataclasses import dataclass

from corporate_development.decision_framework.types import (
    DealRecommendationInput,
    ComplexityRating,
)


@dataclass
class DimensionScore:
    """Score for a single dimension."""

    dimension: str
    score: Optional[int]
    weight: float
    weighted_score: float
    redistributed: bool = False


@dataclass
class AggregationResult:
    """Result of score aggregation."""

    overall_score: float
    dimension_scores: List[DimensionScore]
    missing_dimensions: List[str]


class ScoreAggregator:
    """Aggregates scores from multiple phases into overall score.

    Follows the weighted scoring formula from the design doc:
    - Operational Health: 30%
    - Financial Health: 25%
    - Strategic Fit: 20%
    - Integration Complexity: 15% (inverted: LOW=100, MEDIUM=67, HIGH=33)
    - Organizational Readiness: 10%

    If dimensions are missing, weights are redistributed proportionally
    among present dimensions.
    """

    def __init__(self):
        """Initialize with default dimension weights."""
        self.dimension_weights: Dict[str, float] = {
            "operational_health": 0.30,
            "financial_health": 0.25,
            "strategic_fit": 0.20,
            "integration_complexity": 0.15,
            "organizational_readiness": 0.10,
        }

    def aggregate_scores(self, deal_input: DealRecommendationInput) -> AggregationResult:
        """Calculate weighted overall score from deal input.

        Args:
            deal_input: Validated deal input with scores from various phases

        Returns:
            AggregationResult with overall score, dimension scores, and missing dimensions
        """
        # Collect dimension scores
        dimension_scores: List[DimensionScore] = []
        missing_dimensions: List[str] = []

        # 1. Operational Health (required)
        dimension_scores.append(DimensionScore(
            dimension="Operational Health",
            score=deal_input.operational_health_score,
            weight=self.dimension_weights["operational_health"],
            weighted_score=0.0,  # Will calculate after redistribution
        ))

        # 2. Financial Health (required)
        dimension_scores.append(DimensionScore(
            dimension="Financial Health",
            score=deal_input.financial_health_score,
            weight=self.dimension_weights["financial_health"],
            weighted_score=0.0,
        ))

        # 3. Strategic Fit (optional - from Phase 2)
        if deal_input.phase_2_assessment:
            dimension_scores.append(DimensionScore(
                dimension="Strategic Fit",
                score=deal_input.phase_2_assessment.strategic_fit_score,
                weight=self.dimension_weights["strategic_fit"],
                weighted_score=0.0,
            ))
        else:
            dimension_scores.append(DimensionScore(
                dimension="Strategic Fit",
                score=None,
                weight=0.0,
                weighted_score=0.0,
            ))
            missing_dimensions.append("phase_2_assessment")

        # 4. Integration Complexity (optional - from Phase 5, INVERTED)
        if deal_input.phase_5_integration:
            complexity_score = self._invert_complexity_rating(
                deal_input.phase_5_integration.complexity_rating
            )
            dimension_scores.append(DimensionScore(
                dimension="Integration Complexity",
                score=complexity_score,
                weight=self.dimension_weights["integration_complexity"],
                weighted_score=0.0,
            ))
        else:
            dimension_scores.append(DimensionScore(
                dimension="Integration Complexity",
                score=None,
                weight=0.0,
                weighted_score=0.0,
            ))
            missing_dimensions.append("phase_5_integration")

        # 5. Organizational Readiness (optional - from Phase 0, AVERAGED)
        if deal_input.phase_0_readiness:
            readiness_score = round(
                (deal_input.phase_0_readiness.ceo_readiness_score +
                 deal_input.phase_0_readiness.org_readiness_score) / 2
            )
            dimension_scores.append(DimensionScore(
                dimension="Organizational Readiness",
                score=readiness_score,
                weight=self.dimension_weights["organizational_readiness"],
                weighted_score=0.0,
            ))
        else:
            dimension_scores.append(DimensionScore(
                dimension="Organizational Readiness",
                score=None,
                weight=0.0,
                weighted_score=0.0,
            ))
            missing_dimensions.append("phase_0_readiness")

        # Redistribute weights if dimensions missing
        dimension_scores = self._redistribute_weights(dimension_scores)

        # Calculate weighted scores
        overall_score = 0.0
        for ds in dimension_scores:
            if ds.score is not None:
                ds.weighted_score = ds.score * ds.weight
                overall_score += ds.weighted_score

        return AggregationResult(
            overall_score=round(overall_score, 2),
            dimension_scores=dimension_scores,
            missing_dimensions=missing_dimensions,
        )

    def _invert_complexity_rating(self, rating: ComplexityRating) -> int:
        """Convert complexity rating to score (inverted: LOW=good).

        Args:
            rating: ComplexityRating enum value

        Returns:
            Score where LOW=100, MEDIUM=67, HIGH=33
        """
        if rating == ComplexityRating.LOW:
            return 100
        elif rating == ComplexityRating.MEDIUM:
            return 67
        else:  # HIGH
            return 33

    def _redistribute_weights(self, dimension_scores: List[DimensionScore]) -> List[DimensionScore]:
        """Redistribute weights proportionally when dimensions are missing.

        Args:
            dimension_scores: List of dimension scores (some may be None)

        Returns:
            Updated dimension_scores with redistributed weights
        """
        # Calculate total weight of present dimensions
        present_weight = sum(
            ds.weight for ds in dimension_scores if ds.score is not None
        )

        if present_weight == 0:
            # No dimensions present (shouldn't happen with required fields)
            return dimension_scores

        if present_weight < 1.0:
            # Need to redistribute - scale up present dimensions
            scale_factor = 1.0 / present_weight
            for ds in dimension_scores:
                if ds.score is not None:
                    ds.weight = ds.weight * scale_factor
                    ds.redistributed = True

        return dimension_scores
