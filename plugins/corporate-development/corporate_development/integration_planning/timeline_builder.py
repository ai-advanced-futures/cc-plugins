"""TimelineBuilder for organizing activities into 100-day timeline.

This module provides the TimelineBuilder class which organizes activities
into 4 sequential time periods, grouping activities by domain within each period.
"""

import re
from typing import List
from corporate_development.integration_planning.types import (
    Activity,
    TimePeriod,
)


class TimelineBuilder:
    """Builds a 100-day integration timeline from activities.

    The timeline is divided into 4 sequential periods:
    - Period 1: Days 1-30 (Foundation)
    - Period 2: Days 31-60 (Integration)
    - Period 3: Days 61-90 (Optimization)
    - Period 4: Days 91-100 (Completion)

    Activities are assigned to periods based on parsing their day_range field,
    and grouped by domain within each period.
    """

    # Period definitions: (period_name, focus_theme, start_day, end_day)
    PERIOD_DEFINITIONS = [
        (
            "Days 1-30",
            "Foundation & Stabilization - Establish communication, secure key relationships, and stabilize operations",
            1,
            30
        ),
        (
            "Days 31-60",
            "Integration & Alignment - Integrate systems, align processes, and unify teams",
            31,
            60
        ),
        (
            "Days 61-90",
            "Optimization & Acceleration - Optimize operations, accelerate synergies, and drive growth",
            61,
            90
        ),
        (
            "Days 91-100",
            "Completion & Transition - Complete integration milestones and transition to business-as-usual",
            91,
            100
        ),
    ]

    def __init__(self):
        """Initialize TimelineBuilder."""
        pass

    def build_timeline(self, activities: List[Activity]) -> List[TimePeriod]:
        """Build a 100-day timeline from activities.

        Args:
            activities: List of Activity instances to organize.

        Returns:
            List of 4 TimePeriod instances with activities grouped by domain.
        """
        # Create 4 empty time periods
        periods = []
        for period_name, focus_theme, start_day, end_day in self.PERIOD_DEFINITIONS:
            period = TimePeriod(
                period_name=period_name,
                focus_theme=focus_theme,
                start_day=start_day,
                end_day=end_day,
                activities_by_domain={}
            )
            periods.append(period)

        # Assign activities to periods
        for activity in activities:
            period_idx = self._determine_period_index(activity.day_range)
            if period_idx is not None:
                self._add_activity_to_period(periods[period_idx], activity)

        return periods

    def _determine_period_index(self, day_range: str) -> int:
        """Determine which period (0-3) an activity belongs to based on day_range.

        Args:
            day_range: Day range string (e.g., "Day 1", "Days 5-10", "Days 45-75")

        Returns:
            Period index (0-3) or None if cannot be determined.
        """
        # Parse the day range to get the start day
        start_day = self._parse_start_day(day_range)

        if start_day is None:
            return None

        # Determine which period based on start day
        if 1 <= start_day <= 30:
            return 0
        elif 31 <= start_day <= 60:
            return 1
        elif 61 <= start_day <= 90:
            return 2
        elif 91 <= start_day <= 100:
            return 3
        else:
            return None

    def _parse_start_day(self, day_range: str) -> int:
        """Parse day_range string to extract the start day number.

        Handles formats like:
        - "Day 1"
        - "Days 5-10"
        - "Days 45-75"

        Args:
            day_range: Day range string

        Returns:
            Start day number, or None if cannot be parsed.
        """
        # Try to match "Day X" or "Days X-Y" patterns
        # Pattern for "Day 1" or "Days 1-5"
        match = re.search(r'Days?\s+(\d+)', day_range, re.IGNORECASE)

        if match:
            return int(match.group(1))

        return None

    def _add_activity_to_period(self, period: TimePeriod, activity: Activity) -> None:
        """Add an activity to a period, grouping by domain.

        Args:
            period: TimePeriod to add activity to.
            activity: Activity to add.
        """
        domain = activity.domain

        if domain not in period.activities_by_domain:
            period.activities_by_domain[domain] = []

        period.activities_by_domain[domain].append(activity)
