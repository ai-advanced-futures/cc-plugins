"""
Competitive Intelligence Plugin - Strategic Positioning Analysis Lens

Analyzes competitive positioning and strategic choices.

Based on Porter's Generic Strategies and positioning theory:
- Cost Leadership: Compete on low cost/price
- Differentiation: Compete on unique features/quality
- Focus: Target specific market segment

Key Concepts:
- Generic Strategy: Overall competitive approach
- Positioning Dimensions: Quality, price, features, service, etc.
- Strategic Groups: Clusters of competitors with similar strategies
- Differentiation Factors: Sources of competitive uniqueness
- Positioning Distance: How far apart competitors are positioned

Key Features:
- Generic strategy identification (Porter's 4 strategies)
- Multi-dimensional positioning (quality, price, features, service)
- Positioning map generation
- Strategic group analysis
- Differentiation assessment
- Positioning gap identification
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class GenericStrategy(Enum):
    """
    Porter's Generic Competitive Strategies.

    4 fundamental strategic positions:
    - COST_LEADERSHIP: Broad market, low cost
    - DIFFERENTIATION: Broad market, unique features
    - COST_FOCUS: Narrow market, low cost
    - DIFFERENTIATION_FOCUS: Narrow market, unique features
    """
    COST_LEADERSHIP = "cost_leadership"
    DIFFERENTIATION = "differentiation"
    COST_FOCUS = "cost_focus"
    DIFFERENTIATION_FOCUS = "differentiation_focus"


class PositioningDimension(Enum):
    """
    Dimensions of competitive positioning.

    Key dimensions customers use to evaluate solutions:
    - QUALITY: Overall quality/reliability
    - PRICE: Cost/affordability
    - FEATURES: Feature richness/completeness
    - SERVICE: Support/service quality
    - PERFORMANCE: Speed/performance
    - EASE_OF_USE: Usability/simplicity
    """
    QUALITY = "quality"
    PRICE = "price"
    FEATURES = "features"
    SERVICE = "service"
    PERFORMANCE = "performance"
    EASE_OF_USE = "ease_of_use"


@dataclass
class PositionScore:
    """
    Score on a positioning dimension.

    Attributes:
        dimension: Positioning dimension
        score: Score on 1-5 scale
        evidence: Supporting evidence
    """
    dimension: PositioningDimension
    score: float  # 1-5 scale
    evidence: List[str] = field(default_factory=list)


@dataclass
class DifferentiationFactor:
    """
    Factor that differentiates competitor.

    Attributes:
        name: Name of differentiation factor
        strength: How strong (weak/moderate/strong)
        sustainability: How sustainable (low/medium/high)
        customer_value: Value to customers (low/medium/high)
    """
    name: str
    strength: str  # "weak", "moderate", "strong"
    sustainability: str  # "low", "medium", "high"
    customer_value: str  # "low", "medium", "high"


@dataclass
class StrategicGroup:
    """
    Strategic group (cluster of similar competitors).

    Attributes:
        name: Group name
        strategy: Primary generic strategy
        members: List of competitor IDs
        characteristics: Key characteristics of group
    """
    name: str
    strategy: GenericStrategy
    members: List[str]
    characteristics: List[str] = field(default_factory=list)


@dataclass
class PositioningProfile:
    """
    Strategic positioning profile for competitor.

    Attributes:
        competitor_id: Competitor identifier
        generic_strategy: Porter's generic strategy
        position_scores: Scores on each positioning dimension
        target_segments: Target market segments
        differentiation_factors: Factors that differentiate
        strategic_group: Strategic group membership
    """
    competitor_id: str
    generic_strategy: GenericStrategy
    position_scores: Dict[PositioningDimension, PositionScore]
    target_segments: List[str]
    differentiation_factors: List[DifferentiationFactor]
    strategic_group: Optional[StrategicGroup] = None


class StrategicPositioningLens:
    """
    Strategic Positioning Analysis Lens.

    Analyzes competitive positioning and strategic choices.

    Workflow:
    1. Identify generic strategy for each competitor
    2. Score competitors on positioning dimensions
    3. Identify differentiation factors
    4. Group competitors into strategic groups
    5. Generate positioning map
    6. Identify positioning gaps and opportunities
    """

    def __init__(self, job_statement: str):
        """
        Initialize strategic positioning lens.

        Args:
            job_statement: The job customers are trying to get done
        """
        self.job_statement = job_statement
        self.profiles: Dict[str, PositioningProfile] = {}

    def set_position_score(
        self,
        competitor_id: str,
        dimension: PositioningDimension,
        score: float,
        evidence: Optional[List[str]] = None
    ):
        """
        Set position score for competitor on dimension.

        Args:
            competitor_id: Competitor identifier
            dimension: Positioning dimension
            score: Score (1-5)
            evidence: Supporting evidence
        """
        # Create profile if doesn't exist
        if competitor_id not in self.profiles:
            self.profiles[competitor_id] = PositioningProfile(
                competitor_id=competitor_id,
                generic_strategy=GenericStrategy.DIFFERENTIATION,  # Default
                position_scores={},
                target_segments=[],
                differentiation_factors=[]
            )

        # Create position score
        position_score = PositionScore(
            dimension=dimension,
            score=score,
            evidence=evidence or []
        )

        # Add to profile
        self.profiles[competitor_id].position_scores[dimension] = position_score

    def set_generic_strategy(
        self,
        competitor_id: str,
        strategy: GenericStrategy
    ):
        """
        Set generic strategy for competitor.

        Args:
            competitor_id: Competitor identifier
            strategy: Generic strategy
        """
        if competitor_id not in self.profiles:
            self.profiles[competitor_id] = PositioningProfile(
                competitor_id=competitor_id,
                generic_strategy=strategy,
                position_scores={},
                target_segments=[],
                differentiation_factors=[]
            )
        else:
            self.profiles[competitor_id].generic_strategy = strategy

    def add_differentiation_factor(
        self,
        competitor_id: str,
        factor: DifferentiationFactor
    ):
        """
        Add differentiation factor to competitor.

        Args:
            competitor_id: Competitor identifier
            factor: DifferentiationFactor
        """
        if competitor_id not in self.profiles:
            self.profiles[competitor_id] = PositioningProfile(
                competitor_id=competitor_id,
                generic_strategy=GenericStrategy.DIFFERENTIATION,
                position_scores={},
                target_segments=[],
                differentiation_factors=[]
            )

        self.profiles[competitor_id].differentiation_factors.append(factor)

    def calculate_distance(
        self,
        competitor_a: str,
        competitor_b: str
    ) -> float:
        """
        Calculate positioning distance between two competitors.

        Args:
            competitor_a: First competitor ID
            competitor_b: Second competitor ID

        Returns:
            Distance (Euclidean distance across dimensions)
        """
        # Get profiles
        profile_a = self.profiles.get(competitor_a)
        profile_b = self.profiles.get(competitor_b)

        if not profile_a or not profile_b:
            return 0.0

        # Get position scores as dicts
        pos_a = {dim: score.score for dim, score in profile_a.position_scores.items()}
        pos_b = {dim: score.score for dim, score in profile_b.position_scores.items()}

        return calculate_position_distance(pos_a, pos_b)

    def get_profile(self, competitor_id: str) -> Optional[PositioningProfile]:
        """
        Get positioning profile for competitor.

        Args:
            competitor_id: Competitor identifier

        Returns:
            PositioningProfile or None if not found
        """
        return self.profiles.get(competitor_id)

    def get_all_profiles(self) -> List[PositioningProfile]:
        """
        Get all competitor profiles.

        Returns:
            List of PositioningProfile objects
        """
        return list(self.profiles.values())


def calculate_position_distance(
    position_a: Dict[PositioningDimension, float],
    position_b: Dict[PositioningDimension, float]
) -> float:
    """
    Calculate Euclidean distance between two positions.

    Args:
        position_a: First position (dimension -> score)
        position_b: Second position (dimension -> score)

    Returns:
        Euclidean distance
    """
    # Get all dimensions
    all_dimensions = set(position_a.keys()) | set(position_b.keys())

    if not all_dimensions:
        return 0.0

    # Calculate squared differences
    squared_diffs = []
    for dim in all_dimensions:
        score_a = position_a.get(dim, 0)
        score_b = position_b.get(dim, 0)
        squared_diffs.append((score_a - score_b) ** 2)

    # Return Euclidean distance
    return math.sqrt(sum(squared_diffs))


def identify_strategic_group(profile: PositioningProfile) -> StrategicGroup:
    """
    Identify strategic group for competitor.

    Args:
        profile: PositioningProfile

    Returns:
        StrategicGroup
    """
    strategy = profile.generic_strategy

    # Map strategy to group
    strategy_to_group = {
        GenericStrategy.COST_LEADERSHIP: StrategicGroup(
            name="Cost leaders",
            strategy=GenericStrategy.COST_LEADERSHIP,
            members=[profile.competitor_id],
            characteristics=["Low price", "High efficiency", "Mass market"]
        ),
        GenericStrategy.DIFFERENTIATION: StrategicGroup(
            name="Premium differentiators",
            strategy=GenericStrategy.DIFFERENTIATION,
            members=[profile.competitor_id],
            characteristics=["High quality", "Unique features", "Premium price"]
        ),
        GenericStrategy.COST_FOCUS: StrategicGroup(
            name="Niche cost players",
            strategy=GenericStrategy.COST_FOCUS,
            members=[profile.competitor_id],
            characteristics=["Low price", "Narrow segment", "Specialized"]
        ),
        GenericStrategy.DIFFERENTIATION_FOCUS: StrategicGroup(
            name="Specialist premium players",
            strategy=GenericStrategy.DIFFERENTIATION_FOCUS,
            members=[profile.competitor_id],
            characteristics=["High differentiation", "Narrow segment", "Specialist"]
        )
    }

    return strategy_to_group[strategy]


def assess_differentiation(profile: PositioningProfile) -> Dict[str, Any]:
    """
    Assess differentiation strength.

    Args:
        profile: PositioningProfile

    Returns:
        Dict with differentiation assessment
    """
    factors = profile.differentiation_factors

    if not factors:
        return {
            "overall_strength": "weak",
            "factor_count": 0,
            "strong_factors": 0,
            "sustainable_factors": 0,
            "high_value_factors": 0
        }

    # Count factors by attributes
    strong_factors = sum(1 for f in factors if f.strength == "strong")
    sustainable_factors = sum(1 for f in factors if f.sustainability == "high")
    high_value_factors = sum(1 for f in factors if f.customer_value == "high")

    # Determine overall strength
    if strong_factors >= 2 and sustainable_factors >= 2:
        overall_strength = "very_strong"
    elif strong_factors >= 1 or sustainable_factors >= 1:
        overall_strength = "strong"
    elif len(factors) >= 2:
        overall_strength = "moderate"
    else:
        overall_strength = "weak"

    return {
        "overall_strength": overall_strength,
        "factor_count": len(factors),
        "strong_factors": strong_factors,
        "sustainable_factors": sustainable_factors,
        "high_value_factors": high_value_factors
    }


def analyze_strategic_positioning(
    job_statement: str,
    competitors: List[str],
    our_id: str = "us"
) -> Dict[str, Any]:
    """
    Analyze strategic positioning across competitors.

    Args:
        job_statement: The job to be done
        competitors: List of competitor names
        our_id: Our identifier (default: "us")

    Returns:
        Dict with strategic positioning analysis
    """
    lens = StrategicPositioningLens(job_statement=job_statement)

    # Generate placeholder positioning data
    # Real implementation would gather actual data

    strategies = [
        GenericStrategy.COST_LEADERSHIP,
        GenericStrategy.DIFFERENTIATION,
        GenericStrategy.DIFFERENTIATION_FOCUS,
        GenericStrategy.COST_FOCUS
    ]

    for i, comp in enumerate(competitors):
        # Assign strategy (cycle through for variety)
        strategy = strategies[i % len(strategies)]
        lens.set_generic_strategy(comp, strategy)

        # Set position scores based on strategy
        if strategy == GenericStrategy.COST_LEADERSHIP:
            lens.set_position_score(comp, PositioningDimension.PRICE, 5.0, [])
            lens.set_position_score(comp, PositioningDimension.QUALITY, 3.0, [])
            lens.set_position_score(comp, PositioningDimension.FEATURES, 3.0, [])
        elif strategy == GenericStrategy.DIFFERENTIATION:
            lens.set_position_score(comp, PositioningDimension.PRICE, 2.0, [])
            lens.set_position_score(comp, PositioningDimension.QUALITY, 5.0, [])
            lens.set_position_score(comp, PositioningDimension.FEATURES, 5.0, [])
        else:
            # Focus strategies
            lens.set_position_score(comp, PositioningDimension.PRICE, 3.5, [])
            lens.set_position_score(comp, PositioningDimension.QUALITY, 4.0, [])
            lens.set_position_score(comp, PositioningDimension.FEATURES, 4.0, [])

        # Add differentiation factors
        if strategy in [GenericStrategy.DIFFERENTIATION, GenericStrategy.DIFFERENTIATION_FOCUS]:
            factor = DifferentiationFactor(
                name=f"Unique capability for {comp}",
                strength="strong",
                sustainability="high",
                customer_value="high"
            )
            lens.add_differentiation_factor(comp, factor)

    # Build analysis result
    analysis = {
        "job_statement": job_statement,
        "competitor_profiles": [],
        "strategic_groups": {}
    }

    # Add profile data for each competitor
    for profile in lens.get_all_profiles():
        # Identify strategic group
        group = identify_strategic_group(profile)
        profile.strategic_group = group

        # Assess differentiation
        diff_assessment = assess_differentiation(profile)

        profile_data = {
            "competitor_id": profile.competitor_id,
            "generic_strategy": profile.generic_strategy.value,
            "position_scores": {
                dim.value: {
                    "score": score.score,
                    "evidence": score.evidence
                }
                for dim, score in profile.position_scores.items()
            },
            "target_segments": profile.target_segments,
            "differentiation_factors": [
                {
                    "name": f.name,
                    "strength": f.strength,
                    "sustainability": f.sustainability,
                    "customer_value": f.customer_value
                }
                for f in profile.differentiation_factors
            ],
            "differentiation_assessment": diff_assessment,
            "strategic_group": {
                "name": group.name,
                "strategy": group.strategy.value,
                "characteristics": group.characteristics
            }
        }

        analysis["competitor_profiles"].append(profile_data)

        # Add to strategic groups summary
        group_key = group.strategy.value
        if group_key not in analysis["strategic_groups"]:
            analysis["strategic_groups"][group_key] = {
                "name": group.name,
                "members": [],
                "characteristics": group.characteristics
            }
        analysis["strategic_groups"][group_key]["members"].append(profile.competitor_id)

    return analysis


# Convenience functions

def create_differentiation_factor(
    name: str,
    strength: str = "moderate",
    sustainability: str = "medium",
    customer_value: str = "medium"
) -> DifferentiationFactor:
    """
    Convenience function to create differentiation factor.

    Args:
        name: Factor name
        strength: Strength level
        sustainability: Sustainability level
        customer_value: Customer value level

    Returns:
        DifferentiationFactor
    """
    return DifferentiationFactor(
        name=name,
        strength=strength,
        sustainability=sustainability,
        customer_value=customer_value
    )
