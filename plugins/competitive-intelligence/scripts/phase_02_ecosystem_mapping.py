"""
Competitive Intelligence Plugin - Phase 2: Ecosystem Mapping

Maps the competitive landscape with multi-dimensional classification.

Key Features:
- Competitor identification (from user input or discovery)
- 6-dimensional classification system:
  1. Type (direct, indirect, substitute, potential)
  2. JTBD Alternative (product, service, DIY, consume workaround, not doing)
  3. Threat Level (high, medium, low)
  4. Market Stage (emerging, growth, mature, declining)
  5. Market Overlap (0.0 to 1.0)
  6. Tech Disruption Risk (high, medium, low, none)
- Threat level assessment
- Tiered prioritization
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class CompetitorType(Enum):
    """Type of competitor."""
    DIRECT = "direct"
    INDIRECT = "indirect"
    SUBSTITUTE = "substitute"
    POTENTIAL = "potential"


class JTBDAlternative(Enum):
    """How competitor serves the Job To Be Done."""
    PRODUCT_SOLUTION = "product_solution"
    SERVICE_SOLUTION = "service_solution"
    DIY_APPROACH = "diy_approach"
    CONSUME_WORKAROUND = "consume_workaround"
    NOT_DOING_JOB = "not_doing_job"


# Note: Numeric values mirror ConfidenceLevel in confidence_scoring.py (HIGH=3, MEDIUM=2, LOW=1).
# For cross-lens aggregation, convert to ConfidenceLevel using: ConfidenceLevel(value)
class ThreatLevel(Enum):
    """Overall threat assessment."""
    HIGH = 3
    MEDIUM = 2
    LOW = 1


class MarketStage(Enum):
    """Market maturity stage."""
    EMERGING = "emerging"
    GROWTH = "growth"
    MATURE = "mature"
    DECLINING = "declining"


class TechDisruptionRisk(Enum):
    """Technology disruption risk level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class Competitor:
    """
    Competitor with 6-dimensional classification.

    Dimensions:
    1. type: Competitor type
    2. jtbd_alternative: How they serve the JTBD
    3. threat_level: Overall threat
    4. stage: Market stage
    5. market_overlap: Market overlap (0.0-1.0)
    6. tech_disruption_risk: Tech disruption risk
    """
    id: str
    name: str
    type: CompetitorType
    jtbd_alternative: JTBDAlternative
    threat_level: ThreatLevel
    stage: MarketStage
    market_overlap: float  # 0.0 to 1.0
    tech_disruption_risk: TechDisruptionRisk

    # Optional fields
    description: Optional[str] = None
    website: Optional[str] = None
    key_features: List[str] = None
    business_model: Optional[str] = None

    def __post_init__(self):
        if self.key_features is None:
            self.key_features = []


class EcosystemMapper:
    """
    Maps competitive ecosystem through identification and classification.

    Workflow:
    1. Identify competitors (from user input or discovery)
    2. Classify each competitor (6 dimensions)
    3. Assess threat levels
    4. Prioritize competitors (tiered by threat)
    5. Generate ecosystem summary
    """

    def __init__(self, engine):
        """
        Initialize ecosystem mapper.

        Args:
            engine: WorkflowEngine instance
        """
        self.engine = engine
        self.competitors: List[Competitor] = []

    def add_competitor(self, competitor: Competitor):
        """
        Add competitor to ecosystem.

        Args:
            competitor: Competitor to add
        """
        self.competitors.append(competitor)

    def add_competitors(self, competitors: List[Competitor]):
        """
        Add multiple competitors.

        Args:
            competitors: List of competitors
        """
        self.competitors.extend(competitors)

    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate ecosystem summary statistics.

        Returns:
            Dict with summary stats
        """
        summary = {
            "total_competitors": len(self.competitors),
            "direct_count": 0,
            "indirect_count": 0,
            "substitute_count": 0,
            "potential_count": 0,
            "high_threat_count": 0,
            "medium_threat_count": 0,
            "low_threat_count": 0
        }

        for comp in self.competitors:
            # Count by type
            if comp.type == CompetitorType.DIRECT:
                summary["direct_count"] += 1
            elif comp.type == CompetitorType.INDIRECT:
                summary["indirect_count"] += 1
            elif comp.type == CompetitorType.SUBSTITUTE:
                summary["substitute_count"] += 1
            elif comp.type == CompetitorType.POTENTIAL:
                summary["potential_count"] += 1

            # Count by threat
            if comp.threat_level == ThreatLevel.HIGH:
                summary["high_threat_count"] += 1
            elif comp.threat_level == ThreatLevel.MEDIUM:
                summary["medium_threat_count"] += 1
            elif comp.threat_level == ThreatLevel.LOW:
                summary["low_threat_count"] += 1

        return summary

    def get_competitors_by_threat(self, threat: ThreatLevel) -> List[Competitor]:
        """
        Get competitors filtered by threat level.

        Args:
            threat: Threat level to filter by

        Returns:
            List of competitors with that threat level
        """
        return [c for c in self.competitors if c.threat_level == threat]

    def run_mapping(self, competitor_names: List[str]) -> List[Competitor]:
        """
        Run the ecosystem mapping process.

        Args:
            competitor_names: List of competitor names

        Returns:
            List of classified competitors
        """
        # Identify competitors
        competitors = identify_competitors(competitor_names)

        # Add to ecosystem
        self.add_competitors(competitors)

        # Prioritize
        prioritized = prioritize_competitors(self.competitors)
        self.competitors = prioritized

        # Update engine state
        self.engine.update_data({
            "competitors": [c.id for c in self.competitors],
            "ecosystem_summary": self.generate_summary()
        })

        return self.competitors


def identify_competitors(competitor_names: List[str]) -> List[Competitor]:
    """
    Identify competitors from names.

    Creates Competitor objects with default classifications.
    Real implementation would query databases or use ML.

    Args:
        competitor_names: List of competitor names

    Returns:
        List of Competitor objects with default values
    """
    competitors = []

    for name in competitor_names:
        # Generate ID from name
        comp_id = name.lower().replace(" ", "-")

        # Create competitor with defaults
        # Real implementation would classify based on data
        comp = Competitor(
            id=comp_id,
            name=name,
            type=CompetitorType.DIRECT,  # Default
            jtbd_alternative=JTBDAlternative.PRODUCT_SOLUTION,  # Default
            threat_level=ThreatLevel.MEDIUM,  # Default
            stage=MarketStage.GROWTH,  # Default
            market_overlap=0.5,  # Default
            tech_disruption_risk=TechDisruptionRisk.MEDIUM  # Default
        )

        competitors.append(comp)

    return competitors


def classify_competitor(competitor: Competitor) -> Dict[str, Any]:
    """
    Get 6-dimensional classification of competitor.

    Args:
        competitor: Competitor to classify

    Returns:
        Dict with all 6 dimensions
    """
    classification = {
        "type": competitor.type.value,
        "jtbd_alternative": competitor.jtbd_alternative.value,
        "threat_level": competitor.threat_level.name.lower(),
        "stage": competitor.stage.value,
        "market_overlap": competitor.market_overlap,
        "tech_disruption_risk": competitor.tech_disruption_risk.value,
        "dimensions": 6
    }

    return classification


def assess_threat_level(competitor: Competitor) -> ThreatLevel:
    """
    Assess threat level based on multiple factors.

    Factors:
    - Competitor type (direct = higher)
    - Market overlap (higher = higher threat)
    - Market stage (mature = higher threat)
    - Tech disruption risk (higher = higher threat)

    Args:
        competitor: Competitor to assess

    Returns:
        ThreatLevel assessment
    """
    # Adjust based on factors
    threat_score = 0

    # Type factor
    if competitor.type == CompetitorType.DIRECT:
        threat_score += 2
    elif competitor.type == CompetitorType.INDIRECT:
        threat_score += 1

    # Market overlap factor
    if competitor.market_overlap >= 0.8:
        threat_score += 2
    elif competitor.market_overlap >= 0.5:
        threat_score += 1

    # Stage factor (mature competitors are more threatening)
    if competitor.stage == MarketStage.MATURE:
        threat_score += 1

    # Map score to threat level
    if threat_score >= 4:
        return ThreatLevel.HIGH
    elif threat_score >= 2:
        return ThreatLevel.MEDIUM
    else:
        return ThreatLevel.LOW


def prioritize_competitors(competitors: List[Competitor]) -> List[Competitor]:
    """
    Prioritize competitors by threat level, then market overlap.

    Tiered prioritization:
    1. HIGH threat (threat_level = HIGH)
    2. MEDIUM threat
    3. LOW threat

    Within each tier, sort by market_overlap descending.

    Args:
        competitors: List of competitors

    Returns:
        Sorted list of competitors
    """
    def sort_key(comp: Competitor) -> tuple:
        # Primary: threat level (descending)
        # Secondary: market overlap (descending)
        return (-comp.threat_level.value, -comp.market_overlap)

    return sorted(competitors, key=sort_key)


# Convenience functions

def create_competitor(
    name: str,
    type: CompetitorType = CompetitorType.DIRECT,
    jtbd_alternative: JTBDAlternative = JTBDAlternative.PRODUCT_SOLUTION,
    threat_level: ThreatLevel = ThreatLevel.MEDIUM,
    stage: MarketStage = MarketStage.GROWTH,
    market_overlap: float = 0.5,
    tech_disruption_risk: TechDisruptionRisk = TechDisruptionRisk.MEDIUM,
    **kwargs
) -> Competitor:
    """
    Convenience function to create a competitor.

    Args:
        name: Competitor name
        type: Competitor type
        jtbd_alternative: JTBD alternative
        threat_level: Threat level
        stage: Market stage
        market_overlap: Market overlap (0.0-1.0)
        tech_disruption_risk: Tech disruption risk
        **kwargs: Additional fields

    Returns:
        Competitor object
    """
    comp_id = kwargs.pop("id", name.lower().replace(" ", "-"))

    return Competitor(
        id=comp_id,
        name=name,
        type=type,
        jtbd_alternative=jtbd_alternative,
        threat_level=threat_level,
        stage=stage,
        market_overlap=market_overlap,
        tech_disruption_risk=tech_disruption_risk,
        **kwargs
    )
