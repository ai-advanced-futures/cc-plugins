"""
Opportunity profile definitions based on Buy Then Build framework.

The 2x2 matrix classifies M&A opportunities by:
- Value creation potential (horizontal axis): Low to High
- Growth potential (vertical axis): Low to High

This creates four distinct opportunity profiles, each with different
characteristics, risk levels, and strategic implications.

Reference: Buy Then Build, Chapter 4 - The 2x2 Matrix
"""

from typing import Dict, Optional


class OpportunityProfiles:
    """
    Defines the four opportunity profiles from the Buy Then Build 2x2 matrix.

    Each profile represents a different combination of value creation and
    growth potential, requiring different strategic approaches.
    """

    PROFILES: Dict[str, Dict] = {
        "eternally_profitable": {
            "name": "Eternally Profitable",
            "growth_potential": "low",
            "value_potential": "high",
            "risk_level": "low",
            "characteristics": [
                "Stable, predictable cash flows",
                "Mature markets with limited growth",
                "Strong competitive moats",
                "High margins and ROIC",
                "Defensible market positions",
                "Minimal capital requirements for maintenance"
            ],
            "examples": [
                "Niche software companies with locked-in customers",
                "Specialized manufacturing with proprietary processes",
                "Regional monopolies in mature industries",
                "Legacy systems with high switching costs"
            ],
            "ideal_for": [
                "Acquiring proven cash-generating businesses",
                "Portfolio diversification with stable returns",
                "Funding growth initiatives elsewhere",
                "Building financial resilience"
            ]
        },
        "turnaround": {
            "name": "Turnaround",
            "growth_potential": "low",
            "value_potential": "low",
            "risk_level": "high",
            "characteristics": [
                "Underperforming relative to potential",
                "Operational inefficiencies present",
                "Declining market position",
                "Management or execution challenges",
                "Distressed or motivated sellers",
                "Requires significant post-acquisition work"
            ],
            "examples": [
                "Companies with outdated technology needing modernization",
                "Family businesses lacking professional management",
                "Declining brands with potential for repositioning",
                "Operationally inefficient businesses in stable markets"
            ],
            "ideal_for": [
                "Buyers with operational expertise",
                "Platform companies seeking bolt-ons for efficiency",
                "Investors comfortable with restructuring risk",
                "Situations with clear improvement levers"
            ]
        },
        "high_growth": {
            "name": "High Growth",
            "growth_potential": "high",
            "value_potential": "low",
            "risk_level": "medium",
            "characteristics": [
                "Rapidly expanding markets",
                "Unproven business models or unit economics",
                "High revenue growth, low/negative profitability",
                "Significant capital requirements",
                "Competitive markets with low barriers",
                "Execution risk remains high"
            ],
            "examples": [
                "Early-stage SaaS companies in emerging categories",
                "Consumer brands with viral growth but unproven retention",
                "Technology companies in nascent markets",
                "Businesses scaling before achieving product-market fit"
            ],
            "ideal_for": [
                "Buyers seeking market share in growth categories",
                "Companies with capital to fund growth losses",
                "Strategic acquirers adding new capabilities",
                "Situations where speed to market matters"
            ]
        },
        "platform": {
            "name": "Platform",
            "growth_potential": "high",
            "value_potential": "high",
            "risk_level": "low",
            "characteristics": [
                "Scalable business models with network effects",
                "Proven unit economics and profitability",
                "Large addressable markets with room to grow",
                "Strong competitive advantages",
                "Multiple expansion opportunities",
                "High strategic value"
            ],
            "examples": [
                "Market-leading SaaS platforms with expansion potential",
                "Businesses with proven playbooks for new markets",
                "Companies with strong brands entering adjacent categories",
                "Technology platforms with ecosystem advantages"
            ],
            "ideal_for": [
                "Building long-term strategic platforms",
                "Anchoring M&A strategies and bolt-on acquisitions",
                "Justifying premium valuations",
                "Creating transformational value"
            ]
        }
    }

    @classmethod
    def get_profile(cls, profile_name: str) -> Optional[Dict]:
        """
        Retrieve a specific opportunity profile by name.

        Args:
            profile_name: The key name of the profile
                         (eternally_profitable, turnaround, high_growth, platform)

        Returns:
            Dictionary containing profile details, or None if not found
        """
        return cls.PROFILES.get(profile_name)

    @classmethod
    def get_all_profiles(cls) -> Dict[str, Dict]:
        """
        Get all opportunity profiles.

        Returns:
            Dictionary of all profiles with their complete definitions
        """
        return cls.PROFILES

    @classmethod
    def classify_opportunity(
        cls,
        growth_potential: str,
        value_potential: str
    ) -> Optional[str]:
        """
        Classify an opportunity based on growth and value potential.

        Args:
            growth_potential: 'high' or 'low'
            value_potential: 'high' or 'low'

        Returns:
            Profile name key, or None if invalid inputs
        """
        classification_map = {
            ("low", "high"): "eternally_profitable",
            ("low", "low"): "turnaround",
            ("high", "low"): "high_growth",
            ("high", "high"): "platform"
        }

        return classification_map.get((growth_potential, value_potential))
