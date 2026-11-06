"""TechnologyAnalyzer for generating technology integration activities.

This analyzer generates 20-40 activities across 4 time periods focused on
technology systems, infrastructure, security, and technical integration.
"""

from corporate_development.integration_planning.base_analyzer import BaseDomainAnalyzer


class TechnologyAnalyzer(BaseDomainAnalyzer):
    """Generates technology and systems integration activities.

    Covers Days 1-100 across 4 time periods focused on:
    - Period 1 (Days 1-30): Infrastructure assessment, security audit
    - Period 2 (Days 31-60): System integration planning, data migration prep
    - Period 3 (Days 61-90): System cutover, data migration execution
    - Period 4 (Days 91-100): Optimization, decommissioning legacy systems

    The number and type of activities generated depends on input conditions,
    particularly tech_debt_level and integration_complexity.
    """

    DOMAIN_NAME = "Technology & Systems"
