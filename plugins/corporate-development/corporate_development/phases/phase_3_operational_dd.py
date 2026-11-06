"""Phase 3: Operational Due Diligence implementation."""

from typing import Dict, Any, Union
from corporate_development.core.phase import Phase, PhaseGate, PhaseInput, PhaseOutput
from corporate_development.artifacts.artifact_builder import ArtifactBuilder
from corporate_development.operational_dd import (
    TeamAssessmentInput,
    TechnologyAssessmentInput,
    ProductAssessmentInput,
    OperationsAssessmentInput,
    MarketPositionInput,
    TeamAnalyzer,
    TechnologyAnalyzer,
    ProductAnalyzer,
    OperationsAnalyzer,
    MarketAnalyzer,
    HealthScorer,
    RiskAnalyzer,
)


class Phase3OperationalDD(Phase):
    """Phase 3: Operational Due Diligence.

    Assesses operational health across 5 dimensions:
    - Team (25%)
    - Technology (25%)
    - Product (20%)
    - Operations (20%)
    - Market Position (10%)
    """

    name = "Phase 3: Operational Due Diligence"
    description = "Assess operational health across 5 dimensions"

    def run(self, inputs: Union[PhaseInput, Dict[str, Any]]) -> Union[PhaseOutput, Dict[str, Any]]:
        """Execute operational due diligence assessment.

        Args:
            inputs: Either PhaseInput containing user_input Dict, or raw Dict with:
                - target_name: Name of target company
                - team: TeamAssessmentInput fields
                - technology: TechnologyAssessmentInput fields
                - product: ProductAssessmentInput fields
                - operations: OperationsAssessmentInput fields
                - market: MarketPositionInput fields

        Returns:
            PhaseOutput (if PhaseInput provided) or Dict (if Dict provided) containing:
                - overall_score: Operational health score (0-100)
                - gate_decision: GO/CONDITIONAL/NO_GO
                - dimension_scores: List of dimension scores
                - risk_summary: Summary of risks
                - critical_count: Number of critical risks
                - warning_count: Number of warning risks
                - info_count: Number of info risks
        """
        # Handle both PhaseInput and raw dict for backwards compatibility
        if isinstance(inputs, dict):
            input_data = inputs
            return_dict = True
        else:
            input_data = inputs.user_input
            return_dict = False
        # Support both 'target_name' and 'company_name' for backwards compatibility
        target_name = input_data.get('target_name') or input_data.get('company_name', 'Unknown')

        # Initialize artifact builder
        artifact_builder = ArtifactBuilder(
            target_name=target_name,
            phase_name="phase_3_operational_dd"
        )

        # Check if all required dimension data is present
        required_dimensions = ['team', 'technology', 'product', 'operations', 'market']
        missing_dimensions = [dim for dim in required_dimensions if dim not in input_data]

        if missing_dimensions:
            # Return placeholder when dimension data is missing
            summary = f"# Phase 3: Operational DD - {target_name}\n\n"
            summary += "⚠️ **Placeholder Mode**\n\n"
            summary += f"Missing dimension data: {', '.join(missing_dimensions)}\n\n"
            summary += "To perform full operational assessment, provide:\n"
            for dim in required_dimensions:
                summary += f"- {dim}: Assessment data\n"

            summary_path = artifact_builder.write_markdown("summary", summary)

            if return_dict:
                return {
                    "status": "placeholder",
                    "missing_dimensions": missing_dimensions,
                    "phase_3_not_assessed": True,
                }
            else:
                return PhaseOutput(
                    data={
                        "status": "placeholder",
                        "missing_dimensions": missing_dimensions,
                        "phase_3_not_assessed": True,
                    },
                    gate=PhaseGate.CONDITIONAL,
                    artifacts={"summary": str(summary_path)},
                    reasoning=(
                        "Operational due diligence not assessed — provide dimension data "
                        "(team, technology, product, operations, market) for full assessment. "
                        f"Missing: {', '.join(missing_dimensions)}"
                    ),
                )

        # Analyze each dimension
        dimension_scores = []

        # 1. Team Assessment (25%)
        team_input = TeamAssessmentInput(**input_data['team'])
        team_analyzer = TeamAnalyzer()
        team_score = team_analyzer.analyze(team_input)
        dimension_scores.append(team_score)

        # 2. Technology Assessment (25%)
        tech_input = TechnologyAssessmentInput(**input_data['technology'])
        tech_analyzer = TechnologyAnalyzer()
        tech_score = tech_analyzer.analyze(tech_input)
        dimension_scores.append(tech_score)

        # 3. Product Assessment (20%)
        product_input = ProductAssessmentInput(**input_data['product'])
        product_analyzer = ProductAnalyzer()
        product_score = product_analyzer.analyze(product_input)
        dimension_scores.append(product_score)

        # 4. Operations Assessment (20%)
        ops_input = OperationsAssessmentInput(**input_data['operations'])
        ops_analyzer = OperationsAnalyzer()
        ops_score = ops_analyzer.analyze(ops_input)
        dimension_scores.append(ops_score)

        # 5. Market Position Assessment (10%)
        market_input = MarketPositionInput(**input_data['market'])
        market_analyzer = MarketAnalyzer()
        market_score = market_analyzer.analyze(market_input)
        dimension_scores.append(market_score)

        # Calculate overall health
        health_scorer = HealthScorer()
        health_result = health_scorer.calculate_health(dimension_scores)

        # Generate reports
        artifacts = self._generate_reports(artifact_builder, health_result, target_name)

        # Build result data
        result_data = {
            'overall_score': health_result.overall_score,
            'gate_decision': health_result.gate_decision.value,
            'dimension_scores': [
                {
                    'dimension': ds.dimension,
                    'score': ds.score,
                    'weight': ds.weight,
                    'strengths': ds.strengths,
                    'concerns': ds.concerns
                }
                for ds in health_result.dimension_scores
            ],
            'risk_summary': health_result.risk_summary,
            'critical_count': health_result.critical_count,
            'warning_count': health_result.warning_count,
            'info_count': health_result.info_count
        }

        # Return structured result (backwards compatible)
        if return_dict:
            return result_data
        else:
            return PhaseOutput(
                data=result_data,
                gate=health_result.gate_decision,
                artifacts=artifacts,
                reasoning=f"Operational health score: {health_result.overall_score}/100. "
                         f"Critical risks: {health_result.critical_count}, "
                         f"Warning risks: {health_result.warning_count}"
            )

    def _generate_reports(
        self,
        artifact_builder: ArtifactBuilder,
        health_result: Any,
        target_name: str
    ) -> Dict[str, str]:
        """Generate Phase 3 report artifacts.

        Args:
            artifact_builder: Artifact builder instance
            health_result: OperationalHealthResult
            target_name: Target company name

        Returns:
            Dict mapping artifact names to file paths
        """
        artifacts = {}

        # Main summary
        summary = self._build_summary_report(health_result, target_name)
        summary_path = artifact_builder.write_markdown("summary", summary)
        artifacts["summary"] = str(summary_path)

        # Results JSON
        results_data = {
            'target': target_name,
            'overall_score': health_result.overall_score,
            'gate_decision': health_result.gate_decision.value,
            'dimension_scores': [
                {
                    'dimension': ds.dimension,
                    'score': ds.score,
                    'weight': ds.weight,
                    'strengths': ds.strengths,
                    'concerns': ds.concerns,
                    'risk_count': len(ds.risk_flags)
                }
                for ds in health_result.dimension_scores
            ],
            'risk_summary': health_result.risk_summary
        }
        results_path = artifact_builder.write_json("results", results_data)
        artifacts["results"] = str(results_path)

        # Detailed dimension reports
        for idx, dim_score in enumerate(health_result.dimension_scores, 1):
            filename = f"{idx:02d}_{dim_score.dimension.lower().replace(' ', '_')}_assessment"
            content = self._build_dimension_report(dim_score)
            path = artifact_builder.write_markdown(filename, content)
            artifacts[filename] = str(path)

        # Compute risk data once — reused by both risk and recommendations reports
        analyzer = RiskAnalyzer()
        all_risks = analyzer.aggregate_all_risks(health_result.dimension_scores)
        grouped = analyzer.group_by_severity(all_risks)
        top_risks = analyzer.get_top_risks(all_risks, top_n=5)

        # Risk analysis report
        risk_report = self._build_risk_report(health_result, all_risks, grouped)
        risk_path = artifact_builder.write_markdown("06_risk_analysis", risk_report)
        artifacts["risk_analysis"] = str(risk_path)

        # Recommendations report
        recommendations = self._build_recommendations_report(health_result, top_risks)
        rec_path = artifact_builder.write_markdown("07_recommendations", recommendations)
        artifacts["recommendations"] = str(rec_path)

        return artifacts

    def _build_summary_report(self, health_result: Any, target_name: str) -> str:
        """Build summary markdown report.

        Args:
            health_result: OperationalHealthResult
            target_name: Target company name

        Returns:
            Markdown report content
        """
        gate_emoji = {
            PhaseGate.GO: "✅",
            PhaseGate.CONDITIONAL: "⚠️",
            PhaseGate.NO_GO: "❌"
        }

        report = f"""# Phase 3: Operational Due Diligence

**Target:** {target_name}

## Overall Assessment

**Operational Health Score:** {health_result.overall_score}/100

**Gate Decision:** {gate_emoji.get(health_result.gate_decision, "")} {health_result.gate_decision.value}

**Risk Summary:** {health_result.risk_summary}

## Dimension Scores

"""

        for dim_score in health_result.dimension_scores:
            report += f"### {dim_score.dimension} ({int(dim_score.weight * 100)}% weight)\n\n"
            report += f"**Score:** {dim_score.score}/100\n\n"

            if dim_score.strengths:
                report += "**Strengths:**\n"
                for strength in dim_score.strengths:
                    report += f"- {strength}\n"
                report += "\n"

            if dim_score.concerns:
                report += "**Concerns:**\n"
                for concern in dim_score.concerns:
                    report += f"- {concern}\n"
                report += "\n"

            if dim_score.risk_flags:
                report += f"**Risks:** {len(dim_score.risk_flags)} identified\n\n"

        return report

    def _build_dimension_report(self, dim_score: Any) -> str:
        """Build detailed dimension report.

        Args:
            dim_score: DimensionScore instance

        Returns:
            Markdown report content
        """
        report = f"""# {dim_score.dimension} Assessment

**Score:** {dim_score.score}/100 (Weight: {int(dim_score.weight * 100)}%)

## Strengths

"""
        if dim_score.strengths:
            for strength in dim_score.strengths:
                report += f"- {strength}\n"
        else:
            report += "- No significant strengths identified\n"

        report += "\n## Concerns\n\n"
        if dim_score.concerns:
            for concern in dim_score.concerns:
                report += f"- {concern}\n"
        else:
            report += "- No significant concerns identified\n"

        report += "\n## Risks\n\n"
        if dim_score.risk_flags:
            for risk in dim_score.risk_flags:
                report += f"### [{risk.severity}] {risk.title}\n\n"
                report += f"**Description:** {risk.description}\n\n"
                report += f"**Recommendation:** {risk.recommendation}\n\n"
        else:
            report += "- No risks identified\n"

        return report

    def _build_risk_report(self, health_result: Any, all_risks: list, grouped: dict) -> str:
        """Build risk analysis report.

        Args:
            health_result: OperationalHealthResult
            all_risks: Pre-aggregated list of all RiskFlag instances
            grouped: Pre-grouped risks dict keyed by severity (CRITICAL/WARNING/INFO)

        Returns:
            Markdown report content
        """
        report = """# Risk Analysis

## Risk Summary

"""
        report += f"**Total Risks:** {len(all_risks)}\n\n"
        report += f"- CRITICAL: {len(grouped['CRITICAL'])}\n"
        report += f"- WARNING: {len(grouped['WARNING'])}\n"
        report += f"- INFO: {len(grouped['INFO'])}\n\n"

        for severity in ["CRITICAL", "WARNING", "INFO"]:
            if grouped[severity]:
                report += f"## {severity} Risks\n\n"
                for risk in grouped[severity]:
                    report += f"### {risk.title}\n\n"
                    report += f"**Category:** {risk.category}\n\n"
                    report += f"**Description:** {risk.description}\n\n"
                    report += f"**Recommendation:** {risk.recommendation}\n\n"

        return report

    def _build_recommendations_report(self, health_result: Any, top_risks: list) -> str:
        """Build recommendations report.

        Args:
            health_result: OperationalHealthResult
            top_risks: Pre-computed list of top RiskFlag instances (top_n=5)

        Returns:
            Markdown report content
        """
        report = """# Recommendations

## Gate Decision

"""
        if health_result.gate_decision == PhaseGate.GO:
            report += "**Recommendation:** PROCEED with acquisition\n\n"
            report += "The target demonstrates strong operational health across all dimensions. "
            report += "No critical blockers identified.\n\n"
        elif health_result.gate_decision == PhaseGate.CONDITIONAL:
            report += "**Recommendation:** PROCEED WITH CONDITIONS\n\n"
            report += "The target shows acceptable operational health but has areas requiring attention. "
            report += "Address identified concerns before finalizing acquisition.\n\n"
        else:
            report += "**Recommendation:** DO NOT PROCEED\n\n"
            report += "The target has significant operational challenges that pose unacceptable risk. "
            report += "Consider alternatives or negotiate substantial risk mitigation.\n\n"

        report += "## Key Actions\n\n"

        for idx, risk in enumerate(top_risks, 1):
            report += f"{idx}. **{risk.title}** ({risk.severity})\n"
            report += f"   - {risk.recommendation}\n\n"

        return report
