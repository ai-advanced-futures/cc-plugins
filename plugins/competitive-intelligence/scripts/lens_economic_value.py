"""
Competitive Intelligence Plugin - Economic Value Analysis Lens

Analyzes economic value creation, capture, and distribution.

Key Concepts:
- Value Creation: Total value delivered to customers
- Value Capture: Portion of value captured as revenue (pricing)
- Value Distribution: How value is shared across stakeholders
- Willingness To Pay (WTP): Maximum customers will pay
- Total Cost of Ownership (TCO): Full cost over time
- Return on Investment (ROI): Benefit relative to cost
- Economic Moats: Sustainable competitive advantages

Key Features:
- Value driver identification (creation/capture/distribution)
- WTP measurement and comparison
- TCO calculation (3-year standard)
- ROI and payback period analysis
- Economic moat assessment
- Value gap analysis
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# Standard analysis period for TCO and ROI calculations.
# Both calculate_tco() and the ROI call site must use this constant so that
# changing the period only requires updating one value.
ANALYSIS_YEARS = 3


class ValueDriverType(Enum):
    """
    Types of value drivers.

    - VALUE_CREATION: Creates new value for customers
    - VALUE_CAPTURE: Captures value as revenue (pricing)
    - VALUE_DISTRIBUTION: Distributes value to stakeholders
    """
    VALUE_CREATION = "value_creation"
    VALUE_CAPTURE = "value_capture"
    VALUE_DISTRIBUTION = "value_distribution"


class MoatType(Enum):
    """
    Types of economic moats (sustainable competitive advantages).

    Based on Morningstar's 5 moat sources:
    - NETWORK_EFFECTS: Value increases with more users
    - SWITCHING_COSTS: High cost to switch to competitor
    - COST_ADVANTAGES: Structural cost advantages
    - INTANGIBLE_ASSETS: Patents, brands, regulatory licenses
    - BRAND: Strong brand recognition and loyalty
    """
    NETWORK_EFFECTS = "network_effects"
    SWITCHING_COSTS = "switching_costs"
    COST_ADVANTAGES = "cost_advantages"
    INTANGIBLE_ASSETS = "intangible_assets"
    BRAND = "brand"


@dataclass
class ValueDriver:
    """
    Value driver (source of economic value).

    Attributes:
        driver_type: Type of value driver
        description: Description of value driver
        annual_value: Annual economic value ($)
        confidence: Confidence in estimate (high/medium/low)
    """
    driver_type: ValueDriverType
    description: str
    annual_value: float  # Annual value in dollars
    confidence: str  # "high", "medium", "low"


@dataclass
class WillingnessToPay:
    """
    Customer willingness to pay assessment.

    Attributes:
        competitor_id: Competitor identifier
        pricing_tier: Pricing tier (enterprise/standard/basic)
        annual_price: Actual annual price ($)
        perceived_value: Customer perceived value ($)
        value_to_price_ratio: Perceived value / price ratio
    """
    competitor_id: str
    pricing_tier: str
    annual_price: float
    perceived_value: float
    value_to_price_ratio: float


@dataclass
class TotalCostOfOwnership:
    """
    Total cost of ownership over 3 years.

    Attributes:
        competitor_id: Competitor identifier
        initial_cost: One-time initial cost ($)
        annual_licensing: Annual licensing/subscription ($)
        annual_maintenance: Annual maintenance/support ($)
        annual_operational: Annual operational costs ($)
        migration_cost: One-time migration cost ($)
        training_cost: One-time training cost ($)
        three_year_tco: Total 3-year cost ($)
    """
    competitor_id: str
    initial_cost: float
    annual_licensing: float
    annual_maintenance: float
    annual_operational: float
    migration_cost: float = 0
    training_cost: float = 0
    three_year_tco: float = 0


@dataclass
class ROIAnalysis:
    """
    Return on investment analysis.

    Attributes:
        competitor_id: Competitor identifier
        total_benefit: Total benefit over period ($)
        total_cost: Total cost over period ($)
        net_benefit: Net benefit (benefit - cost) ($)
        roi_percentage: ROI as percentage
        payback_months: Months to break even
    """
    competitor_id: str
    total_benefit: float
    total_cost: float
    net_benefit: float
    roi_percentage: float
    payback_months: Optional[float] = None


@dataclass
class EconomicMoat:
    """
    Economic moat (sustainable competitive advantage).

    Attributes:
        moat_type: Type of moat
        description: Description of moat
        strength: Strength of moat (strong/moderate/weak)
        durability: How long moat will last (high/medium/low)
    """
    moat_type: MoatType
    description: str
    strength: str  # "strong", "moderate", "weak"
    durability: str  # "high", "medium", "low"


@dataclass
class ValueProfile:
    """
    Economic value profile for competitor.

    Attributes:
        competitor_id: Competitor identifier
        value_drivers: List of value drivers
        wtp: Willingness to pay assessment
        tco: Total cost of ownership
        roi: ROI analysis
        economic_moats: List of economic moats
    """
    competitor_id: str
    value_drivers: List[ValueDriver]
    wtp: Optional[WillingnessToPay] = None
    tco: Optional[TotalCostOfOwnership] = None
    roi: Optional[ROIAnalysis] = None
    economic_moats: List[EconomicMoat] = field(default_factory=list)


class EconomicValueLens:
    """
    Economic Value Analysis Lens.

    Analyzes economic value drivers and competitive positioning.

    Workflow:
    1. Identify value drivers for each competitor
    2. Measure willingness to pay (WTP)
    3. Calculate total cost of ownership (TCO)
    4. Calculate ROI and payback period
    5. Assess economic moats
    6. Compare value gaps
    """

    def __init__(self, job_statement: str):
        """
        Initialize economic value lens.

        Args:
            job_statement: The job customers are trying to get done
        """
        self.job_statement = job_statement
        self.profiles: Dict[str, ValueProfile] = {}

    def add_value_driver(
        self,
        competitor_id: str,
        driver_type: ValueDriverType,
        description: str,
        annual_value: float,
        confidence: str = "medium"
    ):
        """
        Add value driver to competitor profile.

        Args:
            competitor_id: Competitor identifier
            driver_type: Type of value driver
            description: Driver description
            annual_value: Annual economic value
            confidence: Confidence level
        """
        # Create profile if doesn't exist
        if competitor_id not in self.profiles:
            self.profiles[competitor_id] = ValueProfile(
                competitor_id=competitor_id,
                value_drivers=[],
                economic_moats=[]
            )

        # Create value driver
        driver = ValueDriver(
            driver_type=driver_type,
            description=description,
            annual_value=annual_value,
            confidence=confidence
        )

        # Add to profile
        self.profiles[competitor_id].value_drivers.append(driver)

    def set_wtp(self, competitor_id: str, wtp: WillingnessToPay):
        """
        Set willingness to pay for competitor.

        Args:
            competitor_id: Competitor identifier
            wtp: WillingnessToPay object
        """
        if competitor_id not in self.profiles:
            self.profiles[competitor_id] = ValueProfile(
                competitor_id=competitor_id,
                value_drivers=[],
                economic_moats=[]
            )

        self.profiles[competitor_id].wtp = wtp

    def set_tco(self, competitor_id: str, tco: TotalCostOfOwnership):
        """
        Set TCO for competitor.

        Args:
            competitor_id: Competitor identifier
            tco: TotalCostOfOwnership object
        """
        if competitor_id not in self.profiles:
            self.profiles[competitor_id] = ValueProfile(
                competitor_id=competitor_id,
                value_drivers=[],
                economic_moats=[]
            )

        self.profiles[competitor_id].tco = tco

    def calculate_roi(self, competitor_id: str) -> Optional[ROIAnalysis]:
        """
        Calculate ROI for competitor.

        Args:
            competitor_id: Competitor identifier

        Returns:
            ROIAnalysis or None if insufficient data
        """
        if competitor_id not in self.profiles:
            return None

        profile = self.profiles[competitor_id]

        # Need both value drivers and TCO
        if not profile.value_drivers or not profile.tco:
            return None

        # Calculate total benefit over the standard analysis period
        annual_benefit = sum(d.annual_value for d in profile.value_drivers)
        total_benefit = annual_benefit * ANALYSIS_YEARS

        # Get total cost from TCO
        total_cost = profile.tco.three_year_tco

        # Calculate ROI
        roi = calculate_roi(
            total_benefit=total_benefit,
            total_cost=total_cost,
            annual_benefit=annual_benefit
        )

        roi.competitor_id = competitor_id

        # Store in profile
        profile.roi = roi

        return roi

    def add_economic_moat(
        self,
        competitor_id: str,
        moat: EconomicMoat
    ):
        """
        Add economic moat to competitor profile.

        Args:
            competitor_id: Competitor identifier
            moat: EconomicMoat object
        """
        if competitor_id not in self.profiles:
            self.profiles[competitor_id] = ValueProfile(
                competitor_id=competitor_id,
                value_drivers=[],
                economic_moats=[]
            )

        self.profiles[competitor_id].economic_moats.append(moat)

    def get_profile(self, competitor_id: str) -> Optional[ValueProfile]:
        """
        Get value profile for competitor.

        Args:
            competitor_id: Competitor identifier

        Returns:
            ValueProfile or None if not found
        """
        return self.profiles.get(competitor_id)

    def get_all_profiles(self) -> List[ValueProfile]:
        """
        Get all competitor profiles.

        Returns:
            List of ValueProfile objects
        """
        return list(self.profiles.values())


def calculate_tco(
    initial_cost: float,
    annual_licensing: float,
    annual_maintenance: float,
    annual_operational: float,
    years: int = 3,
    migration_cost: float = 0,
    training_cost: float = 0
) -> TotalCostOfOwnership:
    """
    Calculate total cost of ownership.

    Args:
        initial_cost: One-time initial cost
        annual_licensing: Annual licensing cost
        annual_maintenance: Annual maintenance cost
        annual_operational: Annual operational cost
        years: Number of years (default 3)
        migration_cost: One-time migration cost
        training_cost: One-time training cost

    Returns:
        TotalCostOfOwnership
    """
    # Calculate recurring costs
    annual_total = annual_licensing + annual_maintenance + annual_operational
    recurring_costs = annual_total * years

    # Calculate total
    total = initial_cost + migration_cost + training_cost + recurring_costs

    return TotalCostOfOwnership(
        competitor_id="",  # Will be set by caller
        initial_cost=initial_cost,
        annual_licensing=annual_licensing,
        annual_maintenance=annual_maintenance,
        annual_operational=annual_operational,
        migration_cost=migration_cost,
        training_cost=training_cost,
        three_year_tco=total
    )


def calculate_roi(
    total_benefit: float,
    total_cost: float,
    annual_benefit: float
) -> ROIAnalysis:
    """
    Calculate return on investment.

    Args:
        total_benefit: Total benefit over period
        total_cost: Total cost over period
        annual_benefit: Annual benefit (for payback calculation)

    Returns:
        ROIAnalysis
    """
    # Calculate net benefit
    net_benefit = total_benefit - total_cost

    # Calculate ROI percentage
    if total_cost > 0:
        roi_percentage = (net_benefit / total_cost) * 100
    else:
        roi_percentage = 0 if net_benefit == 0 else float('inf')

    # Calculate payback period (months)
    if annual_benefit > 0:
        monthly_benefit = annual_benefit / 12
        payback_months = total_cost / monthly_benefit
    else:
        payback_months = None

    return ROIAnalysis(
        competitor_id="",  # Will be set by caller
        total_benefit=total_benefit,
        total_cost=total_cost,
        net_benefit=net_benefit,
        roi_percentage=roi_percentage,
        payback_months=payback_months
    )


def assess_economic_moats(
    competitor_id: str,
    features: List[str]
) -> List[EconomicMoat]:
    """
    Assess economic moats based on features.

    In real implementation, would use detailed analysis or ML.
    For now, uses keyword matching.

    Args:
        competitor_id: Competitor identifier
        features: List of features/characteristics

    Returns:
        List of EconomicMoat objects
    """
    moats = []

    # Combine features into single string for matching
    features_text = " ".join(features).lower()

    # Keyword classifier pattern — duplicated across lens files for agent isolation.
    # Future: extract to shared KeywordClassifier class in a common module.
    # Keywords for each moat type
    moat_keywords = {
        MoatType.NETWORK_EFFECTS: {
            "keywords": ["network", "users", "marketplace", "platform", "ecosystem"],
            "strength": "moderate",
            "durability": "high"
        },
        MoatType.SWITCHING_COSTS: {
            "keywords": ["integration", "migration", "proprietary", "lock-in", "complex"],
            "strength": "moderate",
            "durability": "medium"
        },
        MoatType.COST_ADVANTAGES: {
            "keywords": ["scale", "efficient", "automated", "optimized"],
            "strength": "moderate",
            "durability": "medium"
        },
        MoatType.INTANGIBLE_ASSETS: {
            "keywords": ["patent", "license", "proprietary", "technology", "ip"],
            "strength": "moderate",
            "durability": "high"
        },
        MoatType.BRAND: {
            "keywords": ["brand", "recognized", "trusted", "reputation", "leader"],
            "strength": "moderate",
            "durability": "high"
        }
    }

    # Check for matches
    for moat_type, config in moat_keywords.items():
        if any(keyword in features_text for keyword in config["keywords"]):
            moat = EconomicMoat(
                moat_type=moat_type,
                description=f"{moat_type.value.replace('_', ' ').title()} identified",
                strength=config["strength"],
                durability=config["durability"]
            )
            moats.append(moat)

    return moats


def calculate_value_gap(our_value: float, their_value: float) -> Dict[str, Any]:
    """
    Calculate value gap between us and competitor.

    Args:
        our_value: Our delivered value
        their_value: Their delivered value

    Returns:
        Dict with gap analysis
    """
    value_gap = our_value - their_value

    if their_value > 0:
        gap_percentage = (value_gap / their_value) * 100
    else:
        gap_percentage = 0

    return {
        "our_value": our_value,
        "their_value": their_value,
        "value_gap": value_gap,
        "gap_percentage": gap_percentage,
        "favorable": value_gap > 0
    }


def analyze_economic_value(
    job_statement: str,
    competitors: List[str],
    our_id: str = "us"
) -> Dict[str, Any]:
    """
    Analyze economic value across competitors.

    Args:
        job_statement: The job to be done
        competitors: List of competitor names
        our_id: Our identifier (default: "us")

    Returns:
        Dict with economic value analysis
    """
    lens = EconomicValueLens(job_statement=job_statement)

    # Generate placeholder data for testing
    # Real implementation would gather actual data

    for comp in competitors:
        # Add value drivers
        lens.add_value_driver(
            competitor_id=comp,
            driver_type=ValueDriverType.VALUE_CREATION,
            description=f"Value creation for {comp}",
            annual_value=50000,
            confidence="medium"
        )

        # Set WTP
        wtp = WillingnessToPay(
            competitor_id=comp,
            pricing_tier="standard",
            annual_price=20000,
            perceived_value=50000,
            value_to_price_ratio=2.5
        )
        lens.set_wtp(comp, wtp)

        # Calculate TCO
        tco = calculate_tco(
            initial_cost=10000,
            annual_licensing=20000,
            annual_maintenance=5000,
            annual_operational=5000,
            years=3
        )
        tco.competitor_id = comp
        lens.set_tco(comp, tco)

        # Calculate ROI
        lens.calculate_roi(comp)

        # Assess moats
        moats = assess_economic_moats(comp, ["Platform with network effects"])
        for moat in moats:
            lens.add_economic_moat(comp, moat)

    # Build analysis result
    analysis = {
        "job_statement": job_statement,
        "competitor_profiles": []
    }

    # Add profile data for each competitor
    for profile in lens.get_all_profiles():
        profile_data = {
            "competitor_id": profile.competitor_id,
            "value_drivers": [
                {
                    "type": d.driver_type.value,
                    "description": d.description,
                    "annual_value": d.annual_value,
                    "confidence": d.confidence
                }
                for d in profile.value_drivers
            ]
        }

        # Add WTP
        if profile.wtp:
            w = profile.wtp
            profile_data["wtp"] = {
                "pricing_tier": w.pricing_tier,
                "annual_price": w.annual_price,
                "perceived_value": w.perceived_value,
                "value_to_price_ratio": w.value_to_price_ratio
            }

        # Add TCO
        if profile.tco:
            t = profile.tco
            profile_data["tco"] = {
                "initial_cost": t.initial_cost,
                "annual_licensing": t.annual_licensing,
                "annual_maintenance": t.annual_maintenance,
                "annual_operational": t.annual_operational,
                "three_year_tco": t.three_year_tco
            }

        # Add ROI
        if profile.roi:
            r = profile.roi
            profile_data["roi"] = {
                "total_benefit": r.total_benefit,
                "total_cost": r.total_cost,
                "net_benefit": r.net_benefit,
                "roi_percentage": r.roi_percentage,
                "payback_months": r.payback_months
            }

        # Add economic moats
        profile_data["economic_moats"] = [
            {
                "type": m.moat_type.value,
                "description": m.description,
                "strength": m.strength,
                "durability": m.durability
            }
            for m in profile.economic_moats
        ]

        analysis["competitor_profiles"].append(profile_data)

    return analysis


# Convenience functions

def create_value_driver(
    driver_type: ValueDriverType,
    description: str,
    annual_value: float,
    confidence: str = "medium"
) -> ValueDriver:
    """
    Convenience function to create value driver.

    Args:
        driver_type: Type of value driver
        description: Description
        annual_value: Annual value
        confidence: Confidence level

    Returns:
        ValueDriver
    """
    return ValueDriver(
        driver_type=driver_type,
        description=description,
        annual_value=annual_value,
        confidence=confidence
    )
