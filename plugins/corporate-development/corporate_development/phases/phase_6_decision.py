"""Phase 6: Deal Decision & Recommendation"""

import json
from corporate_development.core.phase import Phase, PhaseInput, PhaseOutput, PhaseGate
from corporate_development.artifacts.artifact_builder import ArtifactBuilder
from corporate_development.decision_framework.types import DealRecommendationInput
from corporate_development.decision_framework.score_aggregator import ScoreAggregator
from corporate_development.decision_framework.strategy_evaluator import StrategyEvaluator
from corporate_development.decision_framework.recommendation_synthesizer import RecommendationSynthesizer
from corporate_development.decision_framework.executive_summary_generator import ExecutiveSummaryGenerator
from corporate_development.decision_framework.scorecard_generator import ScorecardGenerator
from corporate_development.decision_framework.risk_register_generator import RiskRegisterGenerator
from pydantic import ValidationError


class Phase6DealDecision(Phase):
    """Phase 6: Deal Decision & Recommendation - synthesis and go/no-go."""

    name = "Phase 6: Deal Decision & Recommendation"
    description = "Synthesize findings and provide clear go/no-go recommendation"

    def run(self, inputs: PhaseInput) -> PhaseOutput:
        """Execute Phase 6 deal decision.

        Orchestrates all 6 components:
        1. Validate input (DealRecommendationInput)
        2. Aggregate scores (ScoreAggregator)
        3. Evaluate strategy (StrategyEvaluator)
        4. Synthesize recommendation (RecommendationSynthesizer)
        5. Generate artifacts (3 generators)

        Outputs:
        - Executive summary (markdown)
        - Deal scorecard (JSON)
        - Risk register (CSV)
        """
        company_name = inputs.user_input.get("company_name", "Unknown")

        # Initialize artifact builder
        artifact_builder = ArtifactBuilder(
            target_name=company_name,
            phase_name="phase_6_decision"
        )

        try:
            # Step 1: Validate and parse input
            deal_input = DealRecommendationInput(**inputs.user_input)

        except ValidationError as e:
            # Input validation failed - check if missing required fields
            missing_fields = []
            for error in e.errors():
                if error["type"] == "missing":
                    missing_fields.append(error["loc"][0])

            if "operational_health_score" in missing_fields or "financial_health_score" in missing_fields:
                # Missing required Phase 3/4 data
                summary = (
                    f"# Phase 6: Deal Decision - {company_name}\n\n"
                    "⚠️ **Missing Required Data**\n\n"
                    "Phase 6 requires operational and financial health scores.\n\n"
                    "**Next Steps:**\n"
                    "1. Complete Phase 3: Operational Due Diligence\n"
                    "2. Complete Phase 4: Financial Due Diligence\n"
                    "3. Re-run Phase 6 with complete data\n"
                )

                summary_path = artifact_builder.write_markdown("incomplete_data", summary)

                return PhaseOutput(
                    data={"status": "incomplete_data", "missing_fields": missing_fields},
                    gate=PhaseGate.CONDITIONAL,
                    artifacts={"summary": str(summary_path)},
                    reasoning="Complete Phase 3 (Operational DD) and Phase 4 (Financial DD) before final recommendation"
                )
            else:
                # Other validation errors
                raise

        # Step 2: Aggregate quantitative scores
        aggregator = ScoreAggregator()
        aggregation_result = aggregator.aggregate_scores(deal_input)

        # Step 3: Evaluate qualitative strategic factors
        evaluator = StrategyEvaluator()
        qualitative_assessment = evaluator.evaluate_strategic_factors(deal_input)

        # Step 4: Synthesize final recommendation
        synthesizer = RecommendationSynthesizer()
        final_recommendation = synthesizer.synthesize_recommendation(
            aggregation_result,
            qualitative_assessment
        )

        # Step 5: Generate artifacts
        artifacts = {}

        # 5a. Executive Summary (markdown)
        summary_generator = ExecutiveSummaryGenerator()
        summary_content = summary_generator.generate(deal_input, final_recommendation)
        summary_path = artifact_builder.write_markdown("executive_summary", summary_content)
        artifacts["executive_summary"] = str(summary_path)

        # 5b. Deal Scorecard (JSON)
        scorecard_generator = ScorecardGenerator()
        scorecard_json_str = scorecard_generator.generate(deal_input, final_recommendation)
        scorecard_data = json.loads(scorecard_json_str)
        scorecard_path = artifact_builder.write_json("deal_scorecard", scorecard_data)
        artifacts["scorecard"] = str(scorecard_path)

        # 5c. Risk Register (CSV)
        risk_generator = RiskRegisterGenerator()
        risk_content = risk_generator.generate(deal_input, final_recommendation)
        risk_path = artifact_builder.write_csv("risk_register", risk_content)
        artifacts["risk_register"] = str(risk_path)

        # Build output data
        output_data = {
            "recommendation": final_recommendation.gate.value,
            "overall_score": final_recommendation.overall_score,
            "quantitative_assessment": final_recommendation.quantitative_assessment,
            "confidence_level": final_recommendation.confidence_level,
            "critical_blockers": final_recommendation.qualitative_blockers,
            "major_concerns": final_recommendation.qualitative_concerns,
            "conditions": final_recommendation.conditions,
        }

        return PhaseOutput(
            data=output_data,
            gate=final_recommendation.gate,
            artifacts=artifacts,
            reasoning=final_recommendation.recommendation_rationale
        )
