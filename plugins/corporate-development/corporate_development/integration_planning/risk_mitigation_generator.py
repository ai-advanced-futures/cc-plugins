"""Risk Mitigation Generator for Phase 5 Integration Planning.

This module generates a comprehensive risk mitigation plan in markdown format
from an IntegrationPlan. The document organizes risks by severity and provides
detailed mitigation strategies for each risk.

Output Format: risk_mitigation.md
- Risk tables organized by severity (Critical, High, Medium, Low)
- Detailed mitigation strategies
- Risk ownership and accountability
- Likelihood and impact assessments

Example:
    >>> from corporate_development.integration_planning import (
    ...     IntegrationPlanner,
    ...     RiskMitigationGenerator,
    ...     IntegrationPlanningInput,
    ... )
    >>>
    >>> planner = IntegrationPlanner()
    >>> plan = planner.generate_plan(input_data)
    >>>
    >>> generator = RiskMitigationGenerator(target_name="TechCorp", output_base="/path/to/output")
    >>> risk_path = generator.generate(plan)
    >>> print(f"Risk mitigation plan written to: {risk_path}")
"""

from pathlib import Path
from typing import Dict, List
from corporate_development.integration_planning.types import (
    IntegrationPlan,
    Risk,
    Severity,
)
from corporate_development.artifacts.artifact_builder import ArtifactBuilder


class RiskMitigationGenerator:
    """Generates risk mitigation markdown document from IntegrationPlan."""

    def __init__(self, target_name: str, output_base: str = ".corporate-development"):
        """Initialize RiskMitigationGenerator.

        Args:
            target_name: Name of target company (for directory structure).
            output_base: Base directory for output (default: .corporate-development).
        """
        self.target_name = target_name
        self.output_base = output_base

    def generate(self, plan: IntegrationPlan) -> Path:
        """Generate risk_mitigation.md from IntegrationPlan.

        Args:
            plan: Complete integration plan.

        Returns:
            Path to generated risk_mitigation.md file.
        """
        # Build risk mitigation content
        content = self._build_risk_mitigation_content(plan)

        # Write using ArtifactBuilder
        builder = ArtifactBuilder(
            target_name=self.target_name,
            phase_name="phase_5_integration_planning",
            output_base=self.output_base,
        )
        return builder.write_markdown("risk_mitigation", content)

    def _build_risk_mitigation_content(self, plan: IntegrationPlan) -> str:
        """Build the complete risk mitigation markdown content.

        Args:
            plan: Complete integration plan.

        Returns:
            Formatted markdown string.
        """
        sections = [
            self._build_header(plan),
            self._build_executive_overview(plan),
            self._build_risk_summary(plan),
            self._build_risks_by_severity(plan),
            self._build_mitigation_approach(plan),
        ]
        return "\n\n".join(sections)

    def _build_header(self, plan: IntegrationPlan) -> str:
        """Build document header."""
        return f"""# Risk Mitigation Plan

**Target Company:** {plan.target_name}
**Acquiring Company:** {plan.acquirer_name}
**Integration Complexity:** {plan.complexity_rating.value.upper()}
**Total Identified Risks:** {len(plan.integration_risks)}
**Document Purpose:** Integration risk management and mitigation strategies"""

    def _build_executive_overview(self, plan: IntegrationPlan) -> str:
        """Build executive overview section."""
        high_severity_count = plan.risk_count_by_severity.get("critical", 0) + \
                             plan.risk_count_by_severity.get("high", 0)

        overview_text = f"""## Executive Overview

This risk mitigation plan identifies {len(plan.integration_risks)} potential risks
associated with the integration of {plan.target_name} into {plan.acquirer_name}.
Risks are categorized by severity and assigned clear ownership and mitigation strategies.

**Risk Profile:**
- {high_severity_count} high-severity risks requiring immediate attention
- Comprehensive mitigation strategies for all identified risks
- Clear ownership and accountability for risk management

**Key Focus Areas:**
This plan prioritizes CRITICAL and HIGH severity risks that could significantly
impact the integration timeline, employee retention, customer satisfaction,
or financial performance."""

        return overview_text

    def _build_risk_summary(self, plan: IntegrationPlan) -> str:
        """Build risk summary section with counts by severity."""
        sections = ["## Risk Summary\n"]

        # Risk distribution table
        sections.append("### Risk Distribution by Severity\n")
        sections.append("| Severity | Count | Priority |")
        sections.append("|----------|-------|----------|")

        severity_order = [
            (Severity.CRITICAL, "critical", "Immediate Action Required"),
            (Severity.HIGH, "high", "High Priority"),
            (Severity.MEDIUM, "medium", "Monitor & Manage"),
            (Severity.LOW, "low", "Track & Review"),
        ]

        for severity_enum, severity_str, priority_label in severity_order:
            count = plan.risk_count_by_severity.get(severity_str, 0)
            sections.append(f"| {severity_str.upper()} | {count} | {priority_label} |")

        sections.append(f"\n**Total Risks:** {len(plan.integration_risks)}")

        return "\n".join(sections)

    def _build_risks_by_severity(self, plan: IntegrationPlan) -> str:
        """Build detailed risk sections organized by severity."""
        sections = ["## Detailed Risk Analysis\n"]

        # Group risks by severity
        by_severity = self._group_risks_by_severity(plan.integration_risks)

        # Process each severity level
        severity_order = [
            (Severity.CRITICAL, "🔴 CRITICAL", "Immediate action required to prevent integration failure"),
            (Severity.HIGH, "🟠 HIGH", "High priority risks requiring prompt attention"),
            (Severity.MEDIUM, "🟡 MEDIUM", "Moderate risks requiring active management"),
            (Severity.LOW, "🟢 LOW", "Low-priority risks to monitor"),
        ]

        for severity, display_label, description in severity_order:
            risks = by_severity.get(severity, [])
            if risks:
                sections.append(f"### {display_label} Severity Risks\n")
                sections.append(f"*{description}*\n")

                for risk in risks:
                    sections.append(self._format_risk_detail(risk))
                    sections.append("")  # Blank line between risks

        return "\n".join(sections)

    def _group_risks_by_severity(self, risks: List[Risk]) -> Dict[Severity, List[Risk]]:
        """Group risks by severity level.

        Args:
            risks: List of Risk instances.

        Returns:
            Dictionary mapping Severity to list of risks.
        """
        by_severity = {}
        for risk in risks:
            if risk.severity not in by_severity:
                by_severity[risk.severity] = []
            by_severity[risk.severity].append(risk)
        return by_severity

    def _format_risk_detail(self, risk: Risk) -> str:
        """Format detailed risk information.

        Args:
            risk: Risk instance.

        Returns:
            Formatted markdown string for the risk.
        """
        return f"""#### {risk.id}: {risk.description}

**Domain:** {risk.domain}
**Likelihood:** {risk.likelihood.value.upper()}
**Impact:** {risk.impact.value.upper()}
**Risk Owner:** {risk.owner}

**Mitigation Strategy:**
{risk.mitigation_strategy}

**Action Items:**
- Assign {risk.owner} as risk owner
- Implement mitigation strategy immediately
- Monitor risk indicators throughout integration
- Escalate to leadership if risk materializes"""

    def _build_mitigation_approach(self, plan: IntegrationPlan) -> str:
        """Build overall mitigation approach section."""
        return """## Risk Management Approach

### Monitoring and Review

**Weekly Risk Reviews:**
- Review all CRITICAL and HIGH severity risks
- Update mitigation status
- Escalate emerging risks

**Monthly Risk Assessment:**
- Comprehensive review of all risks
- Update risk ratings based on progress
- Identify new risks as integration evolves

### Escalation Protocol

1. **CRITICAL Risks:** Immediate escalation to executive leadership
2. **HIGH Risks:** Escalate to integration steering committee within 24 hours
3. **MEDIUM Risks:** Report to integration manager within 72 hours
4. **LOW Risks:** Include in weekly status reports

### Risk Mitigation Success Criteria

- All CRITICAL risks have active mitigation plans
- HIGH risks are trending toward resolution
- No new CRITICAL risks emerge during integration
- Risk owners report weekly on status
- Mitigation strategies show measurable progress

### Documentation and Reporting

- Weekly risk status reports to integration leadership
- Monthly risk dashboards for executive review
- Risk register maintained and updated continuously
- Post-integration risk retrospective and lessons learned"""
