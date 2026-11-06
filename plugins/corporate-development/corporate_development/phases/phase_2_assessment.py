from typing import Any, Dict
from corporate_development.core.phase import Phase, PhaseInput, PhaseOutput, PhaseGate
from corporate_development.artifacts.artifact_builder import ArtifactBuilder


class Phase2TargetAssessment(Phase):
    """Phase 2: Target Assessment"""

    name = "Phase 2: Target Assessment"
    description = "Determine if target merits deeper due diligence"

    def run(self, inputs: PhaseInput) -> PhaseOutput:
        """Execute Phase 2 target assessment."""
        user_input = inputs.user_input

        # Structural disqualifier: company_name is always required
        company_name = user_input.get("company_name", "")
        if not company_name or not str(company_name).strip():
            return PhaseOutput(
                data={"assessment_mode": "NO_GO", "reason": "company_name is required"},
                gate=PhaseGate.NO_GO,
                artifacts={},
                reasoning="Missing required input: company_name is required for target evaluation.",
            )

        # Structural disqualifier: need at least industry OR motivation to assess strategic fit
        target_industry = (
            user_input.get("industry")
            or user_input.get("target_industry")
        )
        motivation = (
            user_input.get("strategic_motivation")
            or user_input.get("motivation")
            or user_input.get("acquisition_motivation")
        )
        if not target_industry and not motivation:
            return PhaseOutput(
                data={"assessment_mode": "NO_GO", "reason": "target_industry or motivation required"},
                gate=PhaseGate.NO_GO,
                artifacts={},
                reasoning=(
                    "Assessment cannot proceed: either target_industry or motivation is required "
                    "to evaluate strategic fit."
                ),
            )

        # Resolve optional fields with aliases
        industry = target_industry or "Unknown"

        # Assess strategic fit (placeholder)
        strategic_fit = self._assess_strategic_fit(company_name, industry, motivation or "Unknown")

        # Identify initial red flags (placeholder)
        risk_flags = self._identify_red_flags(company_name, user_input)

        # Determine gate — critical flags still produce NO_GO; otherwise CONDITIONAL in placeholder mode
        gate = self._determine_gate(strategic_fit, risk_flags)

        # Generate assessment summary
        summary = self._generate_assessment_summary(company_name, strategic_fit, risk_flags)

        artifact_builder = ArtifactBuilder(
            target_name=company_name,
            phase_name="phase_2_assessment"
        )

        summary_path = artifact_builder.write_markdown(
            "assessment_summary",
            summary
        )

        risk_path = artifact_builder.write_json(
            "risk_flags",
            {"critical": risk_flags.get("critical", []), "warning": risk_flags.get("warning", [])}
        )

        return PhaseOutput(
            data={
                "status": "complete",
                "assessment_mode": "PLACEHOLDER",
                "company_name": company_name,
                "strategic_fit": strategic_fit,
                "risk_flags": risk_flags,
                "investigation_scope": "conditional" if gate == PhaseGate.CONDITIONAL else "none",
            },
            gate=gate,
            artifacts={
                "assessment_summary": str(summary_path),
                "risk_flags": str(risk_path),
            },
            reasoning=(
                "PLACEHOLDER MODE: Strategic assessment not performed. "
                "Scores are default values only. "
                "Results must not be used for investment decisions. "
                "Provide real strategic assessment data or integrate with an assessment tool "
                "before making deal decisions. "
                f"Strategic fit: {strategic_fit['score']}/10. "
                f"Risk flags: {len(risk_flags.get('critical', []))} critical."
            ),
            next_actions=["Integrate real assessment data before proceeding to Phase 3"] if gate == PhaseGate.CONDITIONAL else []
        )

    def _assess_strategic_fit(self, company: str, industry: str, motivation: str) -> Dict[str, Any]:
        """Assess strategic fit (placeholder for plugin integration)."""
        return {
            "company": company,
            "industry_match": True,
            "capability_gap_fit": True,
            "market_position_relevant": True,
            "score": 8,
            "rationale": f"Company operates in {industry} and addresses {motivation} opportunity."
        }

    def _identify_red_flags(self, company: str, inputs: Dict[str, Any]) -> Dict[str, list]:
        """Identify initial red flags (placeholder)."""
        return {
            "critical": [],
            "warning": [],
            "notes": "Placeholder - will be replaced with plugin integration"
        }

    def _determine_gate(self, fit: Dict, flags: Dict) -> PhaseGate:
        """Determine gate decision based on fit and flags.

        In placeholder mode, critical flags still produce NO_GO (data integrity failures
        detected upstream).  All other outcomes are capped at CONDITIONAL — GO is never
        emitted while strategic assessment is unimplemented.
        """
        if len(flags.get("critical", [])) > 0:
            return PhaseGate.NO_GO
        # Placeholder cap: real assessment not performed, so never GO
        return PhaseGate.CONDITIONAL

    def _generate_assessment_summary(self, company: str, fit: Dict, flags: Dict) -> str:
        """Generate assessment summary document."""
        return f"""# Phase 2: Target Assessment - {company}

## Assessment Mode

**WARNING: PLACEHOLDER MODE** — Strategic assessment not performed. Scores are default values
only. Do not use for investment decisions.

## Strategic Fit

**Overall Score:** {fit.get('score', 'N/A')}/10

**Rationale:** {fit.get('rationale', 'N/A')}

## Red Flags

**Critical Issues:** {len(flags.get('critical', []))}

**Warnings:** {len(flags.get('warning', []))}

## Recommendation

- Industry Match: {fit.get('industry_match', False)}
- Capability Fit: {fit.get('capability_gap_fit', False)}
- Market Relevance: {fit.get('market_position_relevant', False)}

## Next Steps

1. Integrate real strategic assessment data before proceeding to Phase 3
2. Coordinate with competitive-intelligence plugin for market analysis
3. Validate strategic assumptions with product team
"""
