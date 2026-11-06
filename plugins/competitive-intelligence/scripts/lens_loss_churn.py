"""
Competitive Intelligence Plugin - Loss/Churn Analysis Lens

Analyzes why customers leave competitors and retention vulnerabilities.

Key Concepts:
- Churn Reason: Why customers defect
- Win/Loss Analysis: Competitive deal outcomes
- Retention Risk: Likelihood of customer defection
- Vulnerability: Exploitable weakness
- Defection Pattern: Common reasons for leaving

Key Features:
- Churn reason classification (6 categories)
- Win/loss record tracking
- Churn rate calculation
- Retention risk assessment (4 levels)
- Vulnerability identification
- Defection pattern analysis
"""

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ChurnReasonCategory(Enum):
    """
    Categories of churn reasons.

    Why customers leave:
    - PRICING: Price too high, better pricing elsewhere
    - PRODUCT: Missing features, poor quality, bugs
    - SUPPORT: Poor service, slow response
    - COMPETITIVE: Competitor offers better solution
    - BUSINESS_CHANGE: Customer's business changes
    - OTHER: Other/unknown reasons
    """
    PRICING = "pricing"
    PRODUCT = "product"
    SUPPORT = "support"
    COMPETITIVE = "competitive"
    BUSINESS_CHANGE = "business_change"
    OTHER = "other"


class WinLossOutcome(Enum):
    """
    Outcome of competitive deal.

    - WIN: We won the deal
    - LOSS: We lost to competitor
    - NO_DECISION: No decision made
    """
    WIN = "win"
    LOSS = "loss"
    NO_DECISION = "no_decision"


# Note: Numeric values mirror ConfidenceLevel in confidence_scoring.py (HIGH=3, MEDIUM=2, LOW=1).
# For cross-lens aggregation, convert to ConfidenceLevel using: ConfidenceLevel(value)
class RetentionRisk(Enum):
    """
    Customer retention risk levels.

    Likelihood of customer defection:
    - VERY_HIGH: High churn rate, major vulnerabilities
    - HIGH: Elevated churn, significant vulnerabilities
    - MODERATE: Some churn, minor vulnerabilities
    - LOW: Low churn, stable retention
    """
    VERY_HIGH = 4
    HIGH = 3
    MODERATE = 2
    LOW = 1


@dataclass
class ChurnReason:
    """
    Reason for customer churn.

    Attributes:
        category: Category of churn reason
        description: Detailed description
        frequency: How often this reason occurs
        impact: Impact level (low/medium/high)
    """
    category: ChurnReasonCategory
    description: str
    frequency: int  # Number of times this reason cited
    impact: str  # "low", "medium", "high"


@dataclass
class WinLossRecord:
    """
    Record of competitive win/loss.

    Attributes:
        outcome: Win, loss, or no decision
        competitor_id: Competitor involved
        reason_category: Category of primary reason
        reason_description: Detailed reason
        deal_size: Size of deal (optional)
    """
    outcome: WinLossOutcome
    competitor_id: str
    reason_category: ChurnReasonCategory
    reason_description: str
    deal_size: Optional[float] = None


@dataclass
class VulnerabilityProfile:
    """
    Churn/vulnerability profile for competitor.

    Attributes:
        competitor_id: Competitor identifier
        churn_reasons: List of churn reasons
        churn_rate: Overall churn rate (0-1)
        retention_risk: Retention risk level
        vulnerabilities: List of identified vulnerabilities
    """
    competitor_id: str
    churn_reasons: List[ChurnReason]
    churn_rate: float  # 0-1 scale
    retention_risk: RetentionRisk
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)


class LossChurnLens:
    """
    Loss/Churn Analysis Lens.

    Analyzes customer defection patterns and vulnerabilities.

    Workflow:
    1. Collect win/loss records
    2. Classify churn reasons
    3. Calculate churn rates
    4. Assess retention risks
    5. Identify vulnerabilities
    6. Recommend actions
    """

    def __init__(self, job_statement: str):
        """
        Initialize loss/churn lens.

        Args:
            job_statement: The job customers are trying to get done
        """
        self.job_statement = job_statement
        self.profiles: Dict[str, VulnerabilityProfile] = {}
        self.win_loss_records: Dict[str, List[WinLossRecord]] = defaultdict(list)

    def add_win_loss_record(self, record: WinLossRecord):
        """
        Add win/loss record.

        Args:
            record: WinLossRecord to add
        """
        self.win_loss_records[record.competitor_id].append(record)

    def calculate_competitor_churn_rate(self, competitor_id: str) -> float:
        """
        Calculate churn rate for competitor.

        Args:
            competitor_id: Competitor identifier

        Returns:
            Churn rate (0-1)
        """
        records = self.win_loss_records.get(competitor_id, [])
        return calculate_churn_rate(competitor_id, records)

    def analyze_competitor(self, competitor_id: str):
        """
        Analyze churn for competitor.

        Args:
            competitor_id: Competitor identifier
        """
        records = self.win_loss_records.get(competitor_id, [])

        if not records:
            return

        # Calculate churn rate — delegates to calculate_competitor_churn_rate() which
        # calls the standalone calculate_churn_rate(), keeping all churn logic in one path.
        churn_rate = self.calculate_competitor_churn_rate(competitor_id)

        # Aggregate churn reasons
        reason_counts: Dict[ChurnReasonCategory, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "descriptions": []}
        )

        for record in records:
            if record.outcome == WinLossOutcome.LOSS:
                reason_counts[record.reason_category]["count"] += 1
                reason_counts[record.reason_category]["descriptions"].append(
                    record.reason_description
                )

        # Create churn reasons
        churn_reasons = []
        for category, data in reason_counts.items():
            if data["count"] > 0:
                reason = ChurnReason(
                    category=category,
                    description=", ".join(data["descriptions"][:3]),  # Top 3
                    frequency=data["count"],
                    impact="high" if data["count"] >= 3 else "medium" if data["count"] >= 2 else "low"
                )
                churn_reasons.append(reason)

        # Assess retention risk
        retention_risk = assess_retention_risk(churn_rate, churn_reasons)

        # Identify vulnerabilities
        vulnerabilities = identify_vulnerabilities(churn_reasons)

        # Create profile
        profile = VulnerabilityProfile(
            competitor_id=competitor_id,
            churn_reasons=churn_reasons,
            churn_rate=churn_rate,
            retention_risk=retention_risk,
            vulnerabilities=vulnerabilities
        )

        self.profiles[competitor_id] = profile

    def get_profile(self, competitor_id: str) -> Optional[VulnerabilityProfile]:
        """
        Get vulnerability profile for competitor.

        Args:
            competitor_id: Competitor identifier

        Returns:
            VulnerabilityProfile or None if not found
        """
        return self.profiles.get(competitor_id)

    def get_all_profiles(self) -> List[VulnerabilityProfile]:
        """
        Get all vulnerability profiles.

        Returns:
            List of VulnerabilityProfile objects
        """
        return list(self.profiles.values())


def classify_churn_reason(description: str) -> ChurnReasonCategory:
    """
    Classify churn reason from description.

    In real implementation, would use NLP or ML.
    For now, uses keyword matching.

    Args:
        description: Churn reason description

    Returns:
        ChurnReasonCategory
    """
    description_lower = description.lower()

    # Keyword classifier pattern — duplicated across lens files for agent isolation.
    # Future: extract to shared KeywordClassifier class in a common module.
    # Keywords for each category
    category_keywords = {
        ChurnReasonCategory.PRICING: ["price", "cost", "expensive", "budget", "affordable"],
        ChurnReasonCategory.PRODUCT: ["feature", "quality", "bug", "performance", "functionality", "missing"],
        ChurnReasonCategory.SUPPORT: ["support", "service", "help", "response", "assistance"],
        ChurnReasonCategory.COMPETITIVE: ["competitor", "alternative", "better solution"],
        ChurnReasonCategory.BUSINESS_CHANGE: ["business", "change", "restructure", "pivot", "acquired"]
    }

    # Check for matches
    for category, keywords in category_keywords.items():
        if any(keyword in description_lower for keyword in keywords):
            return category

    # Default to OTHER
    return ChurnReasonCategory.OTHER


def calculate_churn_rate(
    competitor_id: str,
    records: List[WinLossRecord]
) -> float:
    """
    Calculate churn rate from win/loss records.

    Churn rate = losses / (wins + losses)

    Args:
        competitor_id: Competitor identifier
        records: List of WinLossRecord

    Returns:
        Churn rate (0-1)
    """
    if not records:
        return 0.0

    # Count wins and losses
    wins = sum(1 for r in records if r.outcome == WinLossOutcome.WIN)
    losses = sum(1 for r in records if r.outcome == WinLossOutcome.LOSS)

    total_decisions = wins + losses

    if total_decisions == 0:
        return 0.0

    return losses / total_decisions


def assess_retention_risk(
    churn_rate: float,
    churn_reasons: List[ChurnReason]
) -> RetentionRisk:
    """
    Assess retention risk based on churn rate and reasons.

    Args:
        churn_rate: Churn rate (0-1)
        churn_reasons: List of ChurnReason

    Returns:
        RetentionRisk level
    """
    # Assess based on churn rate and impact
    if churn_rate >= 0.3:
        return RetentionRisk.VERY_HIGH
    elif churn_rate >= 0.2:
        return RetentionRisk.HIGH
    elif churn_rate >= 0.1:
        return RetentionRisk.MODERATE
    else:
        return RetentionRisk.LOW


def identify_vulnerabilities(
    churn_reasons: List[ChurnReason]
) -> List[Dict[str, Any]]:
    """
    Identify vulnerabilities from churn reasons.

    Vulnerabilities are areas where competitor is weak.

    Args:
        churn_reasons: List of ChurnReason

    Returns:
        List of vulnerability dicts
    """
    vulnerabilities = []

    # Group by category
    category_totals: Dict[ChurnReasonCategory, int] = defaultdict(int)
    for reason in churn_reasons:
        category_totals[reason.category] += reason.frequency

    # Identify major vulnerabilities (high frequency)
    for category, total_freq in category_totals.items():
        if total_freq >= 10:  # Threshold for major vulnerability
            severity = "high"
        elif total_freq >= 5:
            severity = "medium"
        else:
            severity = "low"

        vulnerability = {
            "category": category.value,
            "frequency": total_freq,
            "severity": severity,
            "description": f"Vulnerability in {category.value}"
        }

        vulnerabilities.append(vulnerability)

    return vulnerabilities


def analyze_loss_churn(
    job_statement: str,
    competitors: List[str],
    our_id: str = "us"
) -> Dict[str, Any]:
    """
    Analyze loss/churn across competitors.

    Args:
        job_statement: The job to be done
        competitors: List of competitor names
        our_id: Our identifier (default: "us")

    Returns:
        Dict with loss/churn analysis
    """
    lens = LossChurnLens(job_statement=job_statement)

    # Generate placeholder churn data
    # Real implementation would gather actual data

    for i, comp in enumerate(competitors):
        # Generate synthetic win/loss records
        # Vary churn rate by competitor (cycle through patterns)
        patterns = [
            # Pattern 1: High churn (pricing issues)
            [
                (WinLossOutcome.LOSS, ChurnReasonCategory.PRICING, "Price too high"),
                (WinLossOutcome.LOSS, ChurnReasonCategory.PRICING, "No budget option"),
                (WinLossOutcome.LOSS, ChurnReasonCategory.PRICING, "Competitor cheaper"),
                (WinLossOutcome.WIN, ChurnReasonCategory.PRODUCT, "Good features"),
            ],
            # Pattern 2: Moderate churn (product issues)
            [
                (WinLossOutcome.LOSS, ChurnReasonCategory.PRODUCT, "Missing features"),
                (WinLossOutcome.WIN, ChurnReasonCategory.PRICING, "Good price"),
                (WinLossOutcome.WIN, ChurnReasonCategory.SUPPORT, "Great support"),
            ],
            # Pattern 3: Low churn (solid product)
            [
                (WinLossOutcome.WIN, ChurnReasonCategory.PRODUCT, "Excellent features"),
                (WinLossOutcome.WIN, ChurnReasonCategory.SUPPORT, "Top support"),
                (WinLossOutcome.WIN, ChurnReasonCategory.PRICING, "Fair price"),
                (WinLossOutcome.LOSS, ChurnReasonCategory.COMPETITIVE, "Competitor better fit"),
            ]
        ]

        pattern = patterns[i % len(patterns)]

        for outcome, category, description in pattern:
            record = WinLossRecord(
                outcome=outcome,
                competitor_id=comp,
                reason_category=category,
                reason_description=description,
                deal_size=10000
            )
            lens.add_win_loss_record(record)

        # Analyze competitor
        lens.analyze_competitor(comp)

    # Build analysis result
    analysis = {
        "job_statement": job_statement,
        "competitor_profiles": []
    }

    # Add profile data for each competitor
    for profile in lens.get_all_profiles():
        profile_data = {
            "competitor_id": profile.competitor_id,
            "churn_rate": profile.churn_rate,
            "retention_risk": profile.retention_risk.name.lower(),
            "churn_reasons": [
                {
                    "category": r.category.value,
                    "description": r.description,
                    "frequency": r.frequency,
                    "impact": r.impact
                }
                for r in profile.churn_reasons
            ],
            "vulnerabilities": profile.vulnerabilities
        }

        analysis["competitor_profiles"].append(profile_data)

    return analysis


# Convenience functions

def create_churn_reason(
    category: ChurnReasonCategory,
    description: str,
    frequency: int = 1,
    impact: str = "medium"
) -> ChurnReason:
    """
    Convenience function to create churn reason.

    Args:
        category: Churn reason category
        description: Description
        frequency: Frequency count
        impact: Impact level

    Returns:
        ChurnReason
    """
    return ChurnReason(
        category=category,
        description=description,
        frequency=frequency,
        impact=impact
    )
