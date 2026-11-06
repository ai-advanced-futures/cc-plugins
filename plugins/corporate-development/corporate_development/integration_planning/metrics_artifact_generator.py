"""Metrics Artifact Generator for Phase 5 Integration Planning.

This module generates a structured JSON file containing success metrics and KPIs
from an IntegrationPlan. The JSON format is designed for tracking and dashboard
integration.

Output Format: success_metrics.json
- JSON array of metrics with targets and measurement methods
- Organized by domain for easy filtering
- Review frequencies and ownership clearly defined
- Ready for integration with tracking dashboards

Example:
    >>> from corporate_development.integration_planning import (
    ...     IntegrationPlanner,
    ...     MetricsArtifactGenerator,
    ...     IntegrationPlanningInput,
    ... )
    >>>
    >>> planner = IntegrationPlanner()
    >>> plan = planner.generate_plan(input_data)
    >>>
    >>> generator = MetricsArtifactGenerator(target_name="TechCorp", output_base="/path/to/output")
    >>> metrics_path = generator.generate(plan)
    >>> print(f"Success metrics written to: {metrics_path}")
"""

from pathlib import Path
from typing import Dict, List, Any
from corporate_development.integration_planning.types import (
    IntegrationPlan,
    Metric,
)
from corporate_development.artifacts.artifact_builder import ArtifactBuilder


class MetricsArtifactGenerator:
    """Generates success metrics JSON artifact from IntegrationPlan."""

    def __init__(self, target_name: str, output_base: str = ".corporate-development"):
        """Initialize MetricsArtifactGenerator.

        Args:
            target_name: Name of target company (for directory structure).
            output_base: Base directory for output (default: .corporate-development).
        """
        self.target_name = target_name
        self.output_base = output_base

    def generate(self, plan: IntegrationPlan) -> Path:
        """Generate success_metrics.json from IntegrationPlan.

        Args:
            plan: Complete integration plan.

        Returns:
            Path to generated success_metrics.json file.
        """
        # Build metrics data structure
        metrics_data = self._build_metrics_data(plan)

        # Write using ArtifactBuilder
        builder = ArtifactBuilder(
            target_name=self.target_name,
            phase_name="phase_5_integration_planning",
            output_base=self.output_base,
        )
        return builder.write_json("success_metrics", metrics_data)

    def _build_metrics_data(self, plan: IntegrationPlan) -> Dict[str, Any]:
        """Build the complete metrics data structure.

        Args:
            plan: Complete integration plan.

        Returns:
            Dictionary representing metrics in JSON-serializable format.
        """
        return {
            "metadata": self._build_metadata(plan),
            "metrics": self._serialize_metrics(plan.success_metrics),
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
            "total_metrics": len(plan.success_metrics),
            "integration_complexity": plan.complexity_rating.value,
        }

    def _serialize_metrics(self, metrics: List[Metric]) -> List[Dict[str, Any]]:
        """Serialize metrics to JSON-compatible list.

        Args:
            metrics: List of Metric instances.

        Returns:
            List of metric dictionaries.
        """
        serialized = []
        for metric in metrics:
            serialized.append({
                "domain": metric.domain,
                "metric_name": metric.metric_name,
                "target_value": metric.target_value,
                "measurement_method": metric.measurement_method,
                "review_frequency": metric.review_frequency.value,
                "owner": metric.owner,
            })
        return serialized

    def _build_summary(self, plan: IntegrationPlan) -> Dict[str, Any]:
        """Build summary statistics section.

        Args:
            plan: Complete integration plan.

        Returns:
            Summary dictionary.
        """
        # Count metrics by domain
        metrics_by_domain = {}
        for metric in plan.success_metrics:
            domain = metric.domain
            metrics_by_domain[domain] = metrics_by_domain.get(domain, 0) + 1

        # Count metrics by review frequency
        metrics_by_frequency = {}
        for metric in plan.success_metrics:
            frequency = metric.review_frequency.value
            metrics_by_frequency[frequency] = metrics_by_frequency.get(frequency, 0) + 1

        # Identify key metric owners
        owners = set(metric.owner for metric in plan.success_metrics)

        return {
            "total_metrics": len(plan.success_metrics),
            "metrics_by_domain": metrics_by_domain,
            "metrics_by_review_frequency": metrics_by_frequency,
            "metric_owners": sorted(list(owners)),
        }
