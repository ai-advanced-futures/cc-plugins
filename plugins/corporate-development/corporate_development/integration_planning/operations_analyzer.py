"""OperationsAnalyzer for generating operations and process integration activities.

This analyzer generates 20-40 activities across 4 time periods focused on
operational processes, facilities, supply chain, and business operations.
"""

from corporate_development.integration_planning.base_analyzer import BaseDomainAnalyzer


class OperationsAnalyzer(BaseDomainAnalyzer):
    """Generates operations and process integration activities.

    Covers Days 1-100 across 4 time periods focused on:
    - Period 1 (Days 1-30): Operations assessment, process mapping
    - Period 2 (Days 31-60): Process harmonization, facility planning
    - Period 3 (Days 61-90): Process cutover, efficiency optimization
    - Period 4 (Days 91-100): Performance review, continuous improvement

    The number and type of activities generated depends on input conditions,
    particularly operational_health_score and integration_complexity.
    """

    DOMAIN_NAME = "Operations"
