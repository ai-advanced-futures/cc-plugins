"""Action Tracker Generator for Phase 5 Integration Planning.

This module generates a CSV action tracker from an IntegrationPlan.
The CSV format is designed for tracking execution progress in spreadsheet tools
or project management systems.

Output Format: action_tracker.csv
- CSV with columns: ID, Activity, Domain, Priority, Owner, Day Range, Status, Est Hours
- Sortable and filterable in Excel/Sheets
- Ready for status tracking during execution

Example:
    >>> from corporate_development.integration_planning import (
    ...     IntegrationPlanner,
    ...     ActionTrackerGenerator,
    ...     IntegrationPlanningInput,
    ... )
    >>>
    >>> planner = IntegrationPlanner()
    >>> plan = planner.generate_plan(input_data)
    >>>
    >>> generator = ActionTrackerGenerator(target_name="TechCorp", output_base="/path/to/output")
    >>> tracker_path = generator.generate(plan)
    >>> print(f"Action tracker written to: {tracker_path}")
"""

import csv
from io import StringIO
from pathlib import Path
from typing import List
from corporate_development.integration_planning.types import (
    IntegrationPlan,
    Activity,
)
from corporate_development.artifacts.artifact_builder import ArtifactBuilder


class ActionTrackerGenerator:
    """Generates CSV action tracker from IntegrationPlan."""

    # CSV column headers
    HEADERS = [
        "ID",
        "Activity",
        "Domain",
        "Priority",
        "Owner",
        "Day Range",
        "Status",
        "Est Hours",
        "Success Criteria",
        "Dependencies",
    ]

    def __init__(self, target_name: str, output_base: str = ".corporate-development"):
        """Initialize ActionTrackerGenerator.

        Args:
            target_name: Name of target company (for directory structure).
            output_base: Base directory for output (default: .corporate-development).
        """
        self.target_name = target_name
        self.output_base = output_base

    def generate(self, plan: IntegrationPlan) -> Path:
        """Generate action_tracker.csv from IntegrationPlan.

        Args:
            plan: Complete integration plan.

        Returns:
            Path to generated action_tracker.csv file.
        """
        # Build CSV content
        csv_content = self._build_csv_content(plan)

        # Write using ArtifactBuilder
        builder = ArtifactBuilder(
            target_name=self.target_name,
            phase_name="phase_5_integration_planning",
            output_base=self.output_base,
        )
        return builder.write_csv("action_tracker", csv_content)

    def _build_csv_content(self, plan: IntegrationPlan) -> str:
        """Build CSV content from IntegrationPlan.

        Args:
            plan: Complete integration plan.

        Returns:
            CSV content as string.
        """
        # Collect all activities from all periods
        all_activities = self._collect_all_activities(plan)

        # Sort activities by ID for consistent ordering
        all_activities.sort(key=lambda a: a.id)

        # Build CSV using StringIO
        output = StringIO()
        writer = csv.writer(output)

        # Write header row
        writer.writerow(self.HEADERS)

        # Write activity rows
        for activity in all_activities:
            writer.writerow(self._activity_to_row(activity))

        return output.getvalue()

    def _collect_all_activities(self, plan: IntegrationPlan) -> List[Activity]:
        """Collect all activities from all periods.

        Args:
            plan: Complete integration plan.

        Returns:
            List of all activities.
        """
        all_activities = []
        for period in plan.timeline:
            for activities in period.activities_by_domain.values():
                all_activities.extend(activities)
        return all_activities

    def _activity_to_row(self, activity: Activity) -> List[str]:
        """Convert an Activity to a CSV row.

        Args:
            activity: Activity instance.

        Returns:
            List of strings representing the CSV row.
        """
        return [
            activity.id,
            activity.title,
            activity.domain,
            activity.priority.value.upper(),
            activity.owner,
            activity.day_range,
            "Not Started",  # Default status
            str(activity.estimated_hours) if activity.estimated_hours else "",
            activity.success_criteria,
            ", ".join(activity.dependencies) if activity.dependencies else "",
        ]
