"""
Competitive Intelligence Plugin - Technology Disruption Analysis Lens

Analyzes disruptive innovation potential and technology maturity.

Based on Christensen's Disruptive Innovation Theory:
- Disruptive innovations start by serving overlooked segments
- Initially offer lower performance but compensate with simplicity/cost
- Improve rapidly and eventually displace incumbents

Key Concepts:
- Innovation Type: Sustaining vs. Disruptive vs. Radical
- Maturity Stage: Technology lifecycle position
- Disruption Potential: Likelihood of disrupting market
- Disruption Indicators: Signals of disruptive threat
- Disruption Score: Quantitative disruption assessment

Key Features:
- Innovation type classification (3 types)
- Technology maturity assessment (5 stages)
- Disruption potential scoring (0-1 scale)
- Disruption indicator detection
- Adoption curve analysis
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class InnovationType(Enum):
    """
    Types of innovation.

    Based on Christensen's framework:
    - SUSTAINING: Incremental improvements for existing customers
    - DISRUPTIVE: New approach serving overlooked segments
    - RADICAL: Breakthrough creating entirely new markets
    """
    SUSTAINING = "sustaining"
    DISRUPTIVE = "disruptive"
    RADICAL = "radical"


class MaturityStage(Enum):
    """
    Technology maturity lifecycle stages.

    Based on technology adoption curve:
    - EMERGING: Early stage, limited adoption (innovators)
    - GROWTH: Rapid adoption (early adopters/early majority)
    - MAINSTREAM: Widespread adoption (late majority)
    - MATURE: Fully adopted, commoditized
    - DECLINING: Losing relevance, being replaced
    """
    EMERGING = "emerging"
    GROWTH = "growth"
    MAINSTREAM = "mainstream"
    MATURE = "mature"
    DECLINING = "declining"


# Note: Numeric values mirror ConfidenceLevel in confidence_scoring.py (HIGH=3, MEDIUM=2, LOW=1).
# For cross-lens aggregation, convert to ConfidenceLevel using: ConfidenceLevel(value)
class DisruptionPotential(Enum):
    """
    Disruption potential assessment levels.

    Likelihood of disrupting existing market:
    - VERY_HIGH: Clear disruption signals, high threat
    - HIGH: Strong disruption indicators
    - MODERATE: Some disruption potential
    - LOW: Minimal disruption threat
    """
    VERY_HIGH = 4
    HIGH = 3
    MODERATE = 2
    LOW = 1


@dataclass
class DisruptionIndicator:
    """
    Indicator of disruptive potential.

    Based on Christensen's disruption signals:
    - Lower cost than incumbents
    - Simpler/easier to use
    - Serves overlooked segments
    - Initially lower performance
    - Rapid improvement trajectory

    Attributes:
        name: Indicator name
        present: Whether indicator is present
        strength: Strength of indicator (weak/moderate/strong)
        evidence: Supporting evidence
    """
    name: str
    present: bool
    strength: str  # "weak", "moderate", "strong"
    evidence: List[str] = field(default_factory=list)


@dataclass
class TechnologyProfile:
    """
    Technology disruption profile for competitor.

    Attributes:
        competitor_id: Competitor identifier
        innovation_type: Type of innovation
        maturity_stage: Technology maturity stage
        disruption_potential: Disruption potential level
        disruption_indicators: List of disruption indicators
        disruption_score: Quantitative disruption score (0-1)
    """
    competitor_id: str
    innovation_type: InnovationType
    maturity_stage: MaturityStage
    disruption_potential: DisruptionPotential
    disruption_indicators: List[DisruptionIndicator]
    disruption_score: float  # 0-1 scale


class TechnologyDisruptionLens:
    """
    Technology Disruption Analysis Lens.

    Analyzes disruptive innovation potential.

    Workflow:
    1. Classify innovation type for each competitor
    2. Identify maturity stage
    3. Detect disruption indicators
    4. Calculate disruption score
    5. Assess disruption potential
    6. Identify threats and opportunities
    """

    def __init__(self, job_statement: str):
        """
        Initialize technology disruption lens.

        Args:
            job_statement: The job customers are trying to get done
        """
        self.job_statement = job_statement
        self.profiles: Dict[str, TechnologyProfile] = {}

    def add_profile(self, profile: TechnologyProfile):
        """
        Add technology profile for competitor.

        Args:
            profile: TechnologyProfile to add
        """
        self.profiles[profile.competitor_id] = profile

    def add_disruption_indicator(
        self,
        competitor_id: str,
        indicator: DisruptionIndicator
    ):
        """
        Add disruption indicator to competitor.

        Args:
            competitor_id: Competitor identifier
            indicator: DisruptionIndicator
        """
        # Create profile if doesn't exist
        if competitor_id not in self.profiles:
            self.profiles[competitor_id] = TechnologyProfile(
                competitor_id=competitor_id,
                innovation_type=InnovationType.SUSTAINING,  # Default
                maturity_stage=MaturityStage.MAINSTREAM,  # Default
                disruption_potential=DisruptionPotential.LOW,  # Default
                disruption_indicators=[],
                disruption_score=0.0
            )

        self.profiles[competitor_id].disruption_indicators.append(indicator)

    def assess_competitor(self, competitor_id: str):
        """
        Assess disruption potential for competitor.

        Args:
            competitor_id: Competitor identifier
        """
        if competitor_id not in self.profiles:
            return

        profile = self.profiles[competitor_id]

        # Calculate disruption score
        profile.disruption_score = calculate_disruption_score(
            profile.disruption_indicators
        )

        # Assess disruption potential
        profile.disruption_potential = assess_disruption_potential(
            profile.disruption_indicators
        )

    def get_profile(self, competitor_id: str) -> Optional[TechnologyProfile]:
        """
        Get technology profile for competitor.

        Args:
            competitor_id: Competitor identifier

        Returns:
            TechnologyProfile or None if not found
        """
        return self.profiles.get(competitor_id)

    def get_all_profiles(self) -> List[TechnologyProfile]:
        """
        Get all technology profiles.

        Returns:
            List of TechnologyProfile objects
        """
        return list(self.profiles.values())


def identify_maturity_stage(features: List[str]) -> MaturityStage:
    """
    Identify technology maturity stage based on features.

    In real implementation, would use detailed analysis or ML.
    For now, uses keyword matching.

    Args:
        features: List of technology features/characteristics

    Returns:
        MaturityStage
    """
    features_text = " ".join(features).lower()

    # Keyword classifier pattern — duplicated across lens files for agent isolation.
    # Future: extract to shared KeywordClassifier class in a common module.
    # Keywords for each stage
    stage_keywords = {
        MaturityStage.EMERGING: ["emerging", "early", "experimental", "prototype", "beta"],
        MaturityStage.GROWTH: ["growing", "adoption", "rapid", "expanding"],
        MaturityStage.MAINSTREAM: ["mainstream", "widely adopted", "enterprise"],
        MaturityStage.MATURE: ["mature", "commoditized", "stable", "established", "standard", "fully adopted"],
        MaturityStage.DECLINING: ["declining", "legacy", "outdated", "replaced"]
    }

    # Check for matches (prioritize by stage order)
    for stage in [MaturityStage.EMERGING, MaturityStage.GROWTH,
                  MaturityStage.MAINSTREAM, MaturityStage.MATURE,
                  MaturityStage.DECLINING]:
        keywords = stage_keywords[stage]
        if any(keyword in features_text for keyword in keywords):
            return stage

    # Default to mainstream
    return MaturityStage.MAINSTREAM


def assess_disruption_potential(
    indicators: List[DisruptionIndicator]
) -> DisruptionPotential:
    """
    Assess disruption potential based on indicators.

    Args:
        indicators: List of disruption indicators

    Returns:
        DisruptionPotential level
    """
    if not indicators:
        return DisruptionPotential.LOW

    # Count present and strong indicators
    present_count = sum(1 for i in indicators if i.present)
    strong_count = sum(1 for i in indicators if i.present and i.strength == "strong")

    # Assess based on counts
    if strong_count >= 3:
        return DisruptionPotential.VERY_HIGH
    elif strong_count >= 2 or present_count >= 4:
        return DisruptionPotential.HIGH
    elif strong_count >= 1 or present_count >= 2:
        return DisruptionPotential.MODERATE
    else:
        return DisruptionPotential.LOW


def calculate_disruption_score(
    indicators: List[DisruptionIndicator]
) -> float:
    """
    Calculate quantitative disruption score.

    Score based on:
    - Number of indicators present
    - Strength of each indicator
    - Weight of different indicator types

    Args:
        indicators: List of disruption indicators

    Returns:
        Disruption score (0-1 scale)
    """
    if not indicators:
        return 0.0

    # Strength weights
    strength_weights = {
        "strong": 1.0,
        "moderate": 0.6,
        "weak": 0.3
    }

    # Calculate weighted score
    total_weight = 0.0
    max_possible = 0.0

    for indicator in indicators:
        weight = strength_weights.get(indicator.strength, 0.0)
        max_possible += 1.0

        if indicator.present:
            total_weight += weight

    # Normalize to 0-1
    if max_possible > 0:
        score = total_weight / max_possible
    else:
        score = 0.0

    return min(1.0, max(0.0, score))


def analyze_technology_disruption(
    job_statement: str,
    competitors: List[str],
    our_id: str = "us"
) -> Dict[str, Any]:
    """
    Analyze technology disruption across competitors.

    Args:
        job_statement: The job to be done
        competitors: List of competitor names
        our_id: Our identifier (default: "us")

    Returns:
        Dict with technology disruption analysis
    """
    lens = TechnologyDisruptionLens(job_statement=job_statement)

    # Generate placeholder disruption data
    # Real implementation would gather actual data

    innovation_types = [
        InnovationType.SUSTAINING,
        InnovationType.DISRUPTIVE,
        InnovationType.RADICAL
    ]

    maturity_stages = [
        MaturityStage.EMERGING,
        MaturityStage.GROWTH,
        MaturityStage.MAINSTREAM
    ]

    for i, comp in enumerate(competitors):
        # Assign innovation type and maturity (cycle through for variety)
        innovation_type = innovation_types[i % len(innovation_types)]
        maturity_stage = maturity_stages[i % len(maturity_stages)]

        # Create disruption indicators based on type
        indicators = []

        if innovation_type == InnovationType.DISRUPTIVE:
            indicators = [
                DisruptionIndicator("Lower cost entry point", True, "strong", []),
                DisruptionIndicator("Simpler to use", True, "moderate", []),
                DisruptionIndicator("Serves overlooked segment", True, "strong", [])
            ]
        elif innovation_type == InnovationType.RADICAL:
            indicators = [
                DisruptionIndicator("Breakthrough technology", True, "strong", []),
                DisruptionIndicator("New market creation", True, "strong", []),
                DisruptionIndicator("Paradigm shift", True, "moderate", [])
            ]
        else:  # SUSTAINING
            indicators = [
                DisruptionIndicator("Incremental improvement", True, "moderate", []),
                DisruptionIndicator("Serves existing customers", True, "weak", [])
            ]

        # Create profile
        profile = TechnologyProfile(
            competitor_id=comp,
            innovation_type=innovation_type,
            maturity_stage=maturity_stage,
            disruption_potential=DisruptionPotential.LOW,  # Will be calculated
            disruption_indicators=indicators,
            disruption_score=0.0  # Will be calculated
        )

        lens.add_profile(profile)

        # Assess disruption
        lens.assess_competitor(comp)

    # Build analysis result
    analysis = {
        "job_statement": job_statement,
        "competitor_profiles": []
    }

    # Add profile data for each competitor
    for profile in lens.get_all_profiles():
        profile_data = {
            "competitor_id": profile.competitor_id,
            "innovation_type": profile.innovation_type.value,
            "maturity_stage": profile.maturity_stage.value,
            "disruption_potential": profile.disruption_potential.name.lower(),
            "disruption_score": profile.disruption_score,
            "disruption_indicators": [
                {
                    "name": i.name,
                    "present": i.present,
                    "strength": i.strength,
                    "evidence": i.evidence
                }
                for i in profile.disruption_indicators
            ]
        }

        analysis["competitor_profiles"].append(profile_data)

    return analysis


# Convenience functions

def create_disruption_indicator(
    name: str,
    present: bool = False,
    strength: str = "moderate",
    evidence: Optional[List[str]] = None
) -> DisruptionIndicator:
    """
    Convenience function to create disruption indicator.

    Args:
        name: Indicator name
        present: Whether present
        strength: Strength level
        evidence: Supporting evidence

    Returns:
        DisruptionIndicator
    """
    return DisruptionIndicator(
        name=name,
        present=present,
        strength=strength,
        evidence=evidence or []
    )
