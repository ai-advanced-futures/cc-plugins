from typing import Any, Dict
from corporate_development.core.phase import Phase, PhaseInput, PhaseOutput, PhaseGate
from corporate_development.artifacts.artifact_builder import ArtifactBuilder


class Phase1DealSourcing(Phase):
    """Phase 1: Deal Sourcing & Pipeline Management"""

    name = "Phase 1: Deal Sourcing & Pipeline Management"
    description = "Systematically identify and pre-screen M&A targets"

    def run(self, inputs: PhaseInput) -> PhaseOutput:
        """Execute Phase 1 deal sourcing."""
        user_input = inputs.user_input

        # Validate required inputs
        required_fields = ["target_markets", "strategic_focus", "budget_range"]
        missing = [f for f in required_fields if f not in user_input]

        if missing:
            return PhaseOutput(
                data={"status": "incomplete"},
                gate=PhaseGate.NO_GO,
                artifacts={},
                reasoning=f"Missing required input: {', '.join(missing)}"
            )

        # Extract inputs
        target_markets = user_input.get("target_markets", [])
        strategic_focus = user_input.get("strategic_focus", "")
        budget_range = user_input.get("budget_range", "")
        capability_gaps = user_input.get("capability_gaps", [])

        # Generate target profile
        target_profile = self._generate_target_profile(
            target_markets, strategic_focus, budget_range, capability_gaps
        )

        # Generate market opportunity map
        market_opportunities = self._generate_market_opportunities(target_markets)

        # Generate initial pipeline
        pipeline_data = self._generate_pipeline_dashboard(target_markets, strategic_focus)

        # Create artifacts — use company_name if provided, fall back to strategic_focus
        run_identifier = user_input.get("company_name") or user_input.get("strategic_focus", "Pipeline")
        artifact_builder = ArtifactBuilder(
            target_name=run_identifier,
            phase_name="phase_1_sourcing"
        )

        target_profile_path = artifact_builder.write_markdown(
            "target_profile",
            target_profile
        )

        pipeline_path = artifact_builder.write_json(
            "pipeline_dashboard",
            pipeline_data
        )

        return PhaseOutput(
            data={
                "status": "complete",
                "target_profile": target_profile,
                "market_opportunities": market_opportunities,
                "pipeline": pipeline_data,
            },
            gate=PhaseGate.GO,
            artifacts={
                "target_profile": str(target_profile_path),
                "pipeline_dashboard": str(pipeline_path),
            },
            reasoning="Target profile and market analysis complete. Ready for deal assessment."
        )

    def _generate_target_profile(
        self,
        markets: list[str],
        focus: str,
        budget: str,
        capability_gaps: list[str]
    ) -> str:
        """Generate target profile document."""
        return f"""# Target Acquisition Profile

## Strategic Context

**Target Markets:** {', '.join(markets)}

**Strategic Focus:** {focus}

**Budget Range:** {budget}

## Capability Gaps

{chr(10).join(f"- {gap}" for gap in capability_gaps) if capability_gaps else "None identified"}

## Ideal Target Characteristics

- Operates in {markets[0] if markets else 'target market'}
- Addresses {focus} opportunity
- Valued between {budget}
- Fills {len(capability_gaps)} critical capability gaps

## Next Steps

1. Conduct competitive landscape analysis
2. Identify specific companies matching profile
3. Establish monitoring for market signals
4. Prepare for Phase 2 assessment
"""

    def _generate_market_opportunities(self, markets: list[str]) -> Dict[str, Any]:
        """Identify market consolidation opportunities."""
        return {
            "target_markets": markets,
            "consolidation_signals": [
                "Fragmented market structure",
                "Increasing scale advantages",
                "Technology consolidation trends",
            ],
            "growth_trends": [
                "Market expansion potential",
                "Customer demand growth",
                "Emerging use cases",
            ],
        }

    def _generate_pipeline_dashboard(self, markets: list[str], focus: str) -> Dict[str, Any]:
        """Generate initial pipeline dashboard structure."""
        return {
            "stage": "pipeline_building",
            "target_markets": markets,
            "strategic_rationale": focus,
            "candidates": [],
            "pipeline_stages": {
                "early_interest": [],
                "monitored": [],
                "ready_for_assessment": [],
                "under_negotiation": [],
            },
        }
