"""Playbook Generator for Phase 5 Integration Planning.

This module generates a comprehensive executive markdown playbook from an IntegrationPlan.
The playbook is designed for executive review and provides a narrative overview of the
100-day integration plan.

Output Format: playbook.md (10-15 pages)
- Executive Summary
- Timeline Overview
- Activities by Period and Domain
- Risk Overview
- Success Metrics

Example:
    >>> from corporate_development.integration_planning import (
    ...     IntegrationPlanner,
    ...     PlaybookGenerator,
    ...     IntegrationPlanningInput,
    ... )
    >>>
    >>> planner = IntegrationPlanner()
    >>> plan = planner.generate_plan(input_data)
    >>>
    >>> generator = PlaybookGenerator(target_name="TechCorp", output_base="/path/to/output")
    >>> playbook_path = generator.generate(plan)
    >>> print(f"Playbook written to: {playbook_path}")
"""

from pathlib import Path
from typing import Dict, List
from corporate_development.integration_planning.types import (
    IntegrationPlan,
    Activity,
    Risk,
    Metric,
    Priority,
    Severity,
)
from corporate_development.artifacts.artifact_builder import ArtifactBuilder


class PlaybookGenerator:
    """Generates executive markdown playbook from IntegrationPlan."""

    def __init__(self, target_name: str, output_base: str = ".corporate-development"):
        """Initialize PlaybookGenerator.

        Args:
            target_name: Name of target company (for directory structure).
            output_base: Base directory for output (default: .corporate-development).
        """
        self.target_name = target_name
        self.output_base = output_base

    def generate(self, plan: IntegrationPlan) -> Path:
        """Generate playbook.md from IntegrationPlan.

        Args:
            plan: Complete integration plan.

        Returns:
            Path to generated playbook.md file.
        """
        # Build playbook content
        content = self._build_playbook_content(plan)

        # Write using ArtifactBuilder
        builder = ArtifactBuilder(
            target_name=self.target_name,
            phase_name="phase_5_integration_planning",
            output_base=self.output_base,
        )
        return builder.write_markdown("playbook", content)

    def _build_playbook_content(self, plan: IntegrationPlan) -> str:
        """Build the complete playbook markdown content.

        Args:
            plan: Complete integration plan.

        Returns:
            Formatted markdown string.
        """
        sections = [
            self._build_header(plan),
            self._build_executive_summary(plan),
            self._build_timeline_overview(plan),
            self._build_activities_by_period(plan),
            self._build_risk_overview(plan),
            self._build_success_metrics(plan),
            self._build_appendix(plan),
        ]
        return "\n\n".join(sections)

    def _build_header(self, plan: IntegrationPlan) -> str:
        """Build playbook header."""
        return f"""# 100-Day Integration Playbook

**Target Company:** {plan.target_name}
**Acquiring Company:** {plan.acquirer_name}
**Integration Complexity:** {plan.complexity_rating.value.upper()}
**Total Activities:** {plan.total_activities}
**Critical Path Items:** {len(plan.critical_path_activities)}
**Integration Risks:** {len(plan.integration_risks)}
**Success Metrics:** {len(plan.success_metrics)}"""

    def _build_executive_summary(self, plan: IntegrationPlan) -> str:
        """Build executive summary section."""
        # Determine narrative based on complexity
        if plan.complexity_rating.value == "high":
            complexity_note = (
                "This integration presents significant challenges requiring "
                "careful orchestration across all domains."
            )
        elif plan.complexity_rating.value == "medium":
            complexity_note = (
                "This integration requires moderate coordination with manageable "
                "complexity across domains."
            )
        else:
            complexity_note = (
                "This integration presents relatively low complexity with "
                "straightforward integration activities."
            )

        # Summarize risk landscape
        high_severity_count = plan.risk_count_by_severity.get("high", 0) + \
                             plan.risk_count_by_severity.get("critical", 0)
        risk_note = (
            f"The plan identifies {len(plan.integration_risks)} risks, "
            f"with {high_severity_count} classified as high or critical severity."
        )

        return f"""## Executive Summary

This 100-day integration playbook provides a comprehensive roadmap for integrating
{plan.target_name} into {plan.acquirer_name}. The plan encompasses {plan.total_activities}
activities organized across 6 key domains: Team & Leadership, Technology & Systems,
Product, Customers, Operations, and Finance.

**Integration Complexity:** {complexity_note}

**Activity Distribution:**
{self._format_domain_distribution(plan.activities_by_domain)}

**Risk Landscape:** {risk_note}

**Success Framework:** The plan defines {len(plan.success_metrics)} success metrics
with clear targets and measurement methods to track integration progress.

**Critical Path:** {len(plan.critical_path_activities)} activities are identified as
critical path items that must be completed on time to ensure integration success."""

    def _format_domain_distribution(self, activities_by_domain: Dict[str, int]) -> str:
        """Format activity counts by domain."""
        lines = []
        for domain, count in sorted(activities_by_domain.items()):
            lines.append(f"- **{domain}:** {count} activities")
        return "\n".join(lines)

    def _build_timeline_overview(self, plan: IntegrationPlan) -> str:
        """Build timeline overview section."""
        sections = ["""## Timeline Overview

The 100-day integration is organized into 4 strategic periods, each with a specific focus:
"""]

        for i, period in enumerate(plan.timeline, 1):
            activity_count = sum(len(acts) for acts in period.activities_by_domain.values())
            sections.append(
                f"### Period {i}: {period.period_name}\n"
                f"**Focus:** {period.focus_theme}  \n"
                f"**Activities:** {activity_count}\n"
            )

        return "\n".join(sections)

    def _build_activities_by_period(self, plan: IntegrationPlan) -> str:
        """Build detailed activities by period section."""
        sections = ["## Activities by Period\n"]

        for period in plan.timeline:
            sections.append(f"### {period.period_name}: {period.focus_theme}\n")

            # Sort domains for consistent output
            for domain in sorted(period.activities_by_domain.keys()):
                activities = period.activities_by_domain[domain]
                sections.append(f"#### {domain} ({len(activities)} activities)\n")

                # Group activities by priority
                by_priority = self._group_by_priority(activities)

                for priority in [Priority.CRITICAL, Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
                    priority_activities = by_priority.get(priority, [])
                    if priority_activities:
                        sections.append(f"**{priority.value.upper()} Priority:**\n")
                        for activity in priority_activities:
                            sections.append(self._format_activity(activity))
                        sections.append("")  # Blank line

        return "\n".join(sections)

    def _group_by_priority(self, activities: List[Activity]) -> Dict[Priority, List[Activity]]:
        """Group activities by priority level."""
        by_priority = {}
        for activity in activities:
            if activity.priority not in by_priority:
                by_priority[activity.priority] = []
            by_priority[activity.priority].append(activity)
        return by_priority

    def _format_activity(self, activity: Activity) -> str:
        """Format a single activity for the playbook."""
        critical_marker = " 🔴" if activity.priority == Priority.CRITICAL else ""
        dependencies = (
            f"\n  - **Dependencies:** {', '.join(activity.dependencies)}"
            if activity.dependencies else ""
        )
        hours = (
            f" ({activity.estimated_hours}h)"
            if activity.estimated_hours else ""
        )

        return (
            f"- **{activity.id}: {activity.title}**{critical_marker}\n"
            f"  - **Day Range:** {activity.day_range}{hours}\n"
            f"  - **Owner:** {activity.owner}\n"
            f"  - **Description:** {activity.description}"
            f"{dependencies}\n"
        )

    def _build_risk_overview(self, plan: IntegrationPlan) -> str:
        """Build risk overview section."""
        sections = [
            "## Risk Overview\n",
            f"This section outlines {len(plan.integration_risks)} identified integration risks "
            "organized by severity level.\n",
            "**Risk Distribution:**"
        ]

        # Add risk counts by severity
        for severity in ["critical", "high", "medium", "low"]:
            count = plan.risk_count_by_severity.get(severity, 0)
            if count > 0:
                sections.append(f"- **{severity.upper()}:** {count} risks")

        sections.append("")  # Blank line

        # Group risks by severity
        by_severity = self._group_risks_by_severity(plan.integration_risks)

        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            risks = by_severity.get(severity, [])
            if risks:
                sections.append(f"### {severity.value.upper()} Severity Risks\n")
                for risk in risks:
                    sections.append(self._format_risk(risk))
                sections.append("")  # Blank line

        return "\n".join(sections)

    def _group_risks_by_severity(self, risks: List[Risk]) -> Dict[Severity, List[Risk]]:
        """Group risks by severity level."""
        by_severity = {}
        for risk in risks:
            if risk.severity not in by_severity:
                by_severity[risk.severity] = []
            by_severity[risk.severity].append(risk)
        return by_severity

    def _format_risk(self, risk: Risk) -> str:
        """Format a single risk for the playbook."""
        return (
            f"**{risk.id}: {risk.description}**\n"
            f"- **Domain:** {risk.domain}\n"
            f"- **Likelihood:** {risk.likelihood.value} | **Impact:** {risk.impact.value}\n"
            f"- **Owner:** {risk.owner}\n"
            f"- **Mitigation:** {risk.mitigation_strategy}\n"
        )

    def _build_success_metrics(self, plan: IntegrationPlan) -> str:
        """Build success metrics section."""
        sections = [
            "## Success Metrics\n",
            f"This section defines {len(plan.success_metrics)} key performance indicators (KPIs) "
            "to measure integration success.\n"
        ]

        # Group metrics by domain
        by_domain = self._group_metrics_by_domain(plan.success_metrics)

        for domain in sorted(by_domain.keys()):
            metrics = by_domain[domain]
            sections.append(f"### {domain} Metrics\n")
            for metric in metrics:
                sections.append(self._format_metric(metric))
            sections.append("")  # Blank line

        return "\n".join(sections)

    def _group_metrics_by_domain(self, metrics: List[Metric]) -> Dict[str, List[Metric]]:
        """Group metrics by domain."""
        by_domain = {}
        for metric in metrics:
            if metric.domain not in by_domain:
                by_domain[metric.domain] = []
            by_domain[metric.domain].append(metric)
        return by_domain

    def _format_metric(self, metric: Metric) -> str:
        """Format a single metric for the playbook."""
        return (
            f"**{metric.metric_name}**\n"
            f"- **Target:** {metric.target_value}\n"
            f"- **Measurement:** {metric.measurement_method}\n"
            f"- **Review Frequency:** {metric.review_frequency.value}\n"
            f"- **Owner:** {metric.owner}\n"
        )

    def _build_appendix(self, plan: IntegrationPlan) -> str:
        """Build appendix section."""
        return f"""## Appendix

### Critical Path Activities

The following {len(plan.critical_path_activities)} activities are on the critical path
and must be completed on schedule:

{self._format_critical_path_list(plan.critical_path_activities)}

### Document Notes

- **Generated:** This playbook was automatically generated from integration planning analysis
- **Audience:** Executive leadership and integration stakeholders
- **Purpose:** Strategic overview and execution roadmap
- **Updates:** This is a living document that should be updated as integration progresses"""

    def _format_critical_path_list(self, critical_path: List[str]) -> str:
        """Format critical path activity list."""
        if not critical_path:
            return "- None identified"
        return "\n".join(f"- {activity_id}" for activity_id in sorted(critical_path))
