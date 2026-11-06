"""CustomerAnalyzer for generating customer and market integration activities.

This analyzer generates 20-40 activities across 4 time periods focused on
customer retention, market positioning, sales integration, and customer success.
"""

from corporate_development.integration_planning.base_analyzer import BaseDomainAnalyzer


class CustomerAnalyzer(BaseDomainAnalyzer):
    """Generates customer and market integration activities.

    Covers Days 1-100 across 4 time periods focused on:
    - Period 1 (Days 1-30): Customer communication, risk assessment
    - Period 2 (Days 31-60): Sales integration, account management
    - Period 3 (Days 61-90): Customer success programs, retention initiatives
    - Period 4 (Days 91-100): Market strategy, growth planning

    The number and type of activities generated depends on input conditions,
    particularly critical_risks and annual_revenue.
    """

    DOMAIN_NAME = "Customers"
