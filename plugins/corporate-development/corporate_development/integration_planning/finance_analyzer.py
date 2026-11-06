"""FinanceAnalyzer for generating finance and reporting integration activities.

This analyzer generates 20-40 activities across 4 time periods focused on
financial systems, reporting, accounting, compliance, and budgeting.
"""

from corporate_development.integration_planning.base_analyzer import BaseDomainAnalyzer


class FinanceAnalyzer(BaseDomainAnalyzer):
    """Generates finance and reporting integration activities.

    Covers Days 1-100 across 4 time periods focused on:
    - Period 1 (Days 1-30): Financial systems assessment, accounting policies
    - Period 2 (Days 31-60): Systems integration, reporting consolidation
    - Period 3 (Days 61-90): Unified financial close, compliance verification
    - Period 4 (Days 91-100): Long-term planning, performance management

    The number and type of activities generated depends on input conditions,
    particularly financial_health_score and annual_revenue.
    """

    DOMAIN_NAME = "Finance"
