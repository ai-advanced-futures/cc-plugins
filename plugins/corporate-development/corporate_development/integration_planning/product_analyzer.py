"""ProductAnalyzer for generating product and innovation integration activities.

This analyzer generates 20-40 activities across 4 time periods focused on
product strategy, roadmap alignment, R&D integration, and innovation.
"""

from corporate_development.integration_planning.base_analyzer import BaseDomainAnalyzer


class ProductAnalyzer(BaseDomainAnalyzer):
    """Generates product and innovation integration activities.

    Covers Days 1-100 across 4 time periods focused on:
    - Period 1 (Days 1-30): Product portfolio review, roadmap assessment
    - Period 2 (Days 31-60): Roadmap integration, feature prioritization
    - Period 3 (Days 61-90): Product launches, R&D consolidation
    - Period 4 (Days 91-100): Innovation strategy, long-term planning

    The number and type of activities generated depends on input conditions,
    particularly strategic_fit and annual_revenue.
    """

    DOMAIN_NAME = "Product"
