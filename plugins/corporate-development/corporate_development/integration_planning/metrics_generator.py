"""MetricsGenerator for generating success metrics.

This module provides the MetricsGenerator class which generates success metrics
and KPIs balanced across 6 integration domains with measurement methods,
review frequencies, and owner assignments.
"""

from typing import List
from corporate_development.integration_planning.types import (
    IntegrationPlanningInput,
    Metric,
    ReviewFrequency,
)


class MetricsGenerator:
    """Generates success metrics and KPIs for integration tracking.

    This generator creates 15-20 metrics balanced across 6 domains:
    - Team & Leadership
    - Technology
    - Product
    - Customer Success
    - Operations
    - Finance

    Each metric includes:
    - Target value to achieve
    - Measurement method
    - Review frequency (daily/weekly/monthly)
    - Owner assignment
    """

    def __init__(self):
        """Initialize MetricsGenerator."""
        pass

    def generate_metrics(self, input_data: IntegrationPlanningInput) -> List[Metric]:
        """Generate success metrics based on input conditions.

        Args:
            input_data: Integration planning input with conditions.

        Returns:
            List of 15-20 Metric instances balanced across domains.
        """
        metrics = []

        # Generate metrics for each domain
        metrics.extend(self._generate_team_metrics())
        metrics.extend(self._generate_technology_metrics())
        metrics.extend(self._generate_product_metrics())
        metrics.extend(self._generate_customer_metrics())
        metrics.extend(self._generate_operations_metrics())
        metrics.extend(self._generate_finance_metrics())

        return metrics[:20]

    def _generate_team_metrics(self) -> List[Metric]:
        """Generate team and leadership metrics.

        Returns:
            List of team-related metrics
        """
        return [
            Metric(
                domain="Team & Leadership",
                metric_name="Employee Retention Rate",
                target_value="95% retention of key employees through Day 100",
                measurement_method="Track departures weekly, compare against baseline attrition rate",
                review_frequency=ReviewFrequency.WEEKLY,
                owner="CHRO"
            ),
            Metric(
                domain="Team & Leadership",
                metric_name="Employee Engagement Score",
                target_value="Maintain or improve engagement score by 10%",
                measurement_method="Conduct pulse surveys every 2 weeks, track eNPS trend",
                review_frequency=ReviewFrequency.WEEKLY,
                owner="CHRO"
            ),
            Metric(
                domain="Team & Leadership",
                metric_name="Leadership Alignment Score",
                target_value="90% alignment on strategic priorities by Day 30",
                measurement_method="Survey leadership team monthly on priority alignment",
                review_frequency=ReviewFrequency.MONTHLY,
                owner="CEO"
            ),
            Metric(
                domain="Team & Leadership",
                metric_name="Cross-functional Meeting Participation",
                target_value="80% attendance at integration meetings",
                measurement_method="Track meeting attendance and participation rates",
                review_frequency=ReviewFrequency.WEEKLY,
                owner="Integration Lead"
            ),
        ]

    def _generate_technology_metrics(self) -> List[Metric]:
        """Generate technology and systems metrics.

        Returns:
            List of technology-related metrics
        """
        return [
            Metric(
                domain="Technology",
                metric_name="System Uptime During Integration",
                target_value="99.5% uptime for critical systems",
                measurement_method="Monitor system availability continuously, report daily",
                review_frequency=ReviewFrequency.DAILY,
                owner="CTO"
            ),
            Metric(
                domain="Technology",
                metric_name="Integration Milestones Completion",
                target_value="Complete 100% of planned tech integration milestones on schedule",
                measurement_method="Track milestone completion against integration roadmap",
                review_frequency=ReviewFrequency.WEEKLY,
                owner="VP Engineering"
            ),
            Metric(
                domain="Technology",
                metric_name="Technical Debt Reduction",
                target_value="Reduce critical technical debt items by 30%",
                measurement_method="Track resolution of high-priority tech debt tickets",
                review_frequency=ReviewFrequency.MONTHLY,
                owner="CTO"
            ),
        ]

    def _generate_product_metrics(self) -> List[Metric]:
        """Generate product development metrics.

        Returns:
            List of product-related metrics
        """
        return [
            Metric(
                domain="Product",
                metric_name="Product Release Velocity",
                target_value="Maintain 80% of pre-acquisition release velocity",
                measurement_method="Track feature releases and deployment frequency",
                review_frequency=ReviewFrequency.WEEKLY,
                owner="CPO"
            ),
            Metric(
                domain="Product",
                metric_name="Product Quality Score",
                target_value="Keep bug escape rate below 5% of releases",
                measurement_method="Monitor bug reports, track defect density per release",
                review_frequency=ReviewFrequency.WEEKLY,
                owner="VP Engineering"
            ),
            Metric(
                domain="Product",
                metric_name="Roadmap Alignment Achievement",
                target_value="Deliver 90% of planned integration-related features",
                measurement_method="Track feature completion against integrated roadmap",
                review_frequency=ReviewFrequency.MONTHLY,
                owner="CPO"
            ),
        ]

    def _generate_customer_metrics(self) -> List[Metric]:
        """Generate customer success metrics.

        Returns:
            List of customer-related metrics
        """
        return [
            Metric(
                domain="Customer Success",
                metric_name="Customer Retention Rate",
                target_value="Maintain 98% customer retention during integration",
                measurement_method="Track customer churn monthly, identify integration-related departures",
                review_frequency=ReviewFrequency.MONTHLY,
                owner="VP Customer Success"
            ),
            Metric(
                domain="Customer Success",
                metric_name="Net Promoter Score (NPS)",
                target_value="Maintain or improve NPS by 5 points",
                measurement_method="Conduct NPS surveys monthly, track trend and responses",
                review_frequency=ReviewFrequency.MONTHLY,
                owner="VP Customer Success"
            ),
            Metric(
                domain="Customer Success",
                metric_name="Support Response Time",
                target_value="Maintain <2 hour first response time",
                measurement_method="Track support ticket response times daily",
                review_frequency=ReviewFrequency.DAILY,
                owner="VP Customer Success"
            ),
            Metric(
                domain="Customer Success",
                metric_name="Customer Satisfaction Score",
                target_value="Achieve 4.5/5.0 average satisfaction rating",
                measurement_method="Survey customers after interactions, calculate CSAT score",
                review_frequency=ReviewFrequency.WEEKLY,
                owner="VP Customer Success"
            ),
        ]

    def _generate_operations_metrics(self) -> List[Metric]:
        """Generate operational efficiency metrics.

        Returns:
            List of operations-related metrics
        """
        return [
            Metric(
                domain="Operations",
                metric_name="Process Integration Completion",
                target_value="Complete 100% of planned process integrations by Day 90",
                measurement_method="Track process integration milestones, document completion",
                review_frequency=ReviewFrequency.WEEKLY,
                owner="COO"
            ),
            Metric(
                domain="Operations",
                metric_name="Operational Efficiency Ratio",
                target_value="Improve operational efficiency by 15% by Day 100",
                measurement_method="Calculate output per FTE, track operational KPIs",
                review_frequency=ReviewFrequency.MONTHLY,
                owner="COO"
            ),
            Metric(
                domain="Operations",
                metric_name="Vendor Consolidation Savings",
                target_value="Achieve 20% cost reduction through vendor consolidation",
                measurement_method="Track vendor spend reduction, calculate savings",
                review_frequency=ReviewFrequency.MONTHLY,
                owner="Procurement Manager"
            ),
        ]

    def _generate_finance_metrics(self) -> List[Metric]:
        """Generate financial performance metrics.

        Returns:
            List of finance-related metrics
        """
        return [
            Metric(
                domain="Finance",
                metric_name="Revenue Synergy Achievement",
                target_value="Achieve 25% of planned annual revenue synergies in first 100 days",
                measurement_method="Track cross-sell revenue, upsell opportunities, new customer acquisitions",
                review_frequency=ReviewFrequency.MONTHLY,
                owner="CFO"
            ),
            Metric(
                domain="Finance",
                metric_name="Cost Synergy Realization",
                target_value="Realize 40% of planned annual cost synergies by Day 100",
                measurement_method="Calculate cost reductions against baseline, track savings initiatives",
                review_frequency=ReviewFrequency.MONTHLY,
                owner="CFO"
            ),
            Metric(
                domain="Finance",
                metric_name="Integration Budget Adherence",
                target_value="Stay within 110% of planned integration budget",
                measurement_method="Track integration expenses weekly against budget",
                review_frequency=ReviewFrequency.WEEKLY,
                owner="CFO"
            ),
        ]
