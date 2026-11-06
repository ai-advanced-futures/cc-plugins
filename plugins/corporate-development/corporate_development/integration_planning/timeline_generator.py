"""Timeline Generator for Phase 5 Integration Planning.

This module generates a structured JSON timeline from an IntegrationPlan.
The JSON format is designed for programmatic consumption and integration with
project management tools.

Output Format: timeline.json
- Structured data with periods, activities, and metadata
- Machine-readable format for downstream tools
- Complete activity details with dependencies

Example:
    >>> from corporate_development.integration_planning import (
    ...     IntegrationPlanner,
    ...     TimelineGenerator,
    ...     IntegrationPlanningInput,
    ... )
    >>>
    >>> planner = IntegrationPlanner()
    >>> plan = planner.generate_plan(input_data)
    >>>
    >>> generator = TimelineGenerator(target_name="TechCorp", output_base="/path/to/output")
    >>> timeline_path = generator.generate(plan)
    >>> print(f"Timeline written to: {timeline_path}")
"""

from pathlib import Path
from typing import Dict, List, Any
from corporate_development.integration_planning.types import (
    IntegrationPlan,
    TimePeriod,
    Activity,
)
from corporate_development.artifacts.artifact_builder import ArtifactBuilder


class TimelineGenerator:
    """Generates structured JSON timeline from IntegrationPlan."""

    def __init__(self, target_name: str, output_base: str = ".corporate-development"):
        """Initialize TimelineGenerator.

        Args:
            target_name: Name of target company (for directory structure).
            output_base: Base directory for output (default: .corporate-development).
        """
        self.target_name = target_name
        self.output_base = output_base

    def generate(self, plan: IntegrationPlan) -> Path:
        """Generate timeline.json from IntegrationPlan.

        Args:
            plan: Complete integration plan.

        Returns:
            Path to generated timeline.json file.
        """
        # Build timeline data structure
        timeline_data = self._build_timeline_data(plan)

        # Write using ArtifactBuilder
        builder = ArtifactBuilder(
            target_name=self.target_name,
            phase_name="phase_5_integration_planning",
            output_base=self.output_base,
        )
        return builder.write_json("timeline", timeline_data)

    def _build_timeline_data(self, plan: IntegrationPlan) -> Dict[str, Any]:
        """Build the complete timeline data structure.

        Args:
            plan: Complete integration plan.

        Returns:
            Dictionary representing the timeline in JSON-serializable format.
        """
        return {
            "metadata": self._build_metadata(plan),
            "periods": self._build_periods(plan.timeline),
            "summary": self._build_summary(plan),
        }

    def _build_metadata(self, plan: IntegrationPlan) -> Dict[str, Any]:
        """Build metadata section.

        Args:
            plan: Complete integration plan.

        Returns:
            Metadata dictionary.
        """
        return {
            "target_name": plan.target_name,
            "acquirer_name": plan.acquirer_name,
            "complexity_rating": plan.complexity_rating.value,
            "total_activities": plan.total_activities,
            "total_periods": len(plan.timeline),
            "critical_path_count": len(plan.critical_path_activities),
        }

    def _build_periods(self, timeline: List[TimePeriod]) -> List[Dict[str, Any]]:
        """Build periods array with activities.

        Args:
            timeline: List of time periods.

        Returns:
            List of period dictionaries.
        """
        periods = []
        for period in timeline:
            period_dict = {
                "period_name": period.period_name,
                "focus_theme": period.focus_theme,
                "start_day": period.start_day,
                "end_day": period.end_day,
                "duration_days": period.end_day - period.start_day + 1,
                "activities_by_domain": {},
            }

            # Add activities organized by domain
            for domain, activities in period.activities_by_domain.items():
                period_dict["activities_by_domain"][domain] = [
                    self._serialize_activity(activity) for activity in activities
                ]

            # Add summary counts
            total_activities = sum(
                len(acts) for acts in period.activities_by_domain.values()
            )
            period_dict["activity_count"] = total_activities

            periods.append(period_dict)

        return periods

    def _serialize_activity(self, activity: Activity) -> Dict[str, Any]:
        """Serialize an Activity to JSON-compatible dictionary.

        Args:
            activity: Activity instance.

        Returns:
            Dictionary representation of activity.
        """
        return {
            "id": activity.id,
            "domain": activity.domain,
            "title": activity.title,
            "description": activity.description,
            "owner": activity.owner,
            "day_range": activity.day_range,
            "priority": activity.priority.value,
            "dependencies": activity.dependencies,
            "success_criteria": activity.success_criteria,
            "estimated_hours": activity.estimated_hours,
        }

    def _build_summary(self, plan: IntegrationPlan) -> Dict[str, Any]:
        """Build summary statistics section.

        Args:
            plan: Complete integration plan.

        Returns:
            Summary dictionary.
        """
        # Calculate total estimated hours
        total_hours = 0
        for period in plan.timeline:
            for activities in period.activities_by_domain.values():
                for activity in activities:
                    if activity.estimated_hours:
                        total_hours += activity.estimated_hours

        # Count activities by priority
        priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for period in plan.timeline:
            for activities in period.activities_by_domain.values():
                for activity in activities:
                    priority_counts[activity.priority.value] += 1

        return {
            "total_activities": plan.total_activities,
            "activities_by_domain": plan.activities_by_domain,
            "total_estimated_hours": total_hours,
            "activities_by_priority": priority_counts,
            "critical_path_activities": plan.critical_path_activities,
        }
