"""TeamAnalyzer for generating team integration activities.

This analyzer generates 20-40 activities across 4 time periods focused on
team integration, leadership alignment, organizational design, and culture.
"""

from corporate_development.integration_planning.base_analyzer import BaseDomainAnalyzer


class TeamAnalyzer(BaseDomainAnalyzer):
    """Generates team and leadership integration activities.

    Covers Days 1-100 across 4 time periods focused on:
    - Period 1 (Days 1-30): Announcements, retention, leadership alignment
    - Period 2 (Days 31-60): Org design, culture workshops
    - Period 3 (Days 61-90): Org structure implementation, role transitions
    - Period 4 (Days 91-100): Team building, performance reviews

    The number and type of activities generated depends on input conditions,
    particularly team_strength.
    """

    DOMAIN_NAME = "Team & Leadership"
