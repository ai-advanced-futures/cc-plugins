"""
Dual output generator for Value & IP analysis.

Produces:
1. VALUE & IP SCORECARD — structured markdown for committing
2. DEVIL'S ADVOCATE REPORT — challenge list requiring team response
"""
from dataclasses import dataclass
from typing import List

from .frameworks import ValueIPScorecard


@dataclass
class Challenge:
    agent: str
    challenge: str
    team_response: str = ""


@dataclass
class DevilsAdvocateReport:
    scorecard: ValueIPScorecard
    challenges: List[Challenge]



class ScorecardGenerator:
    def generate_scorecard(self, scorecard: ValueIPScorecard) -> str:
        verdict = scorecard.overall_verdict.value
        lines = [
            f"# Value & IP Analysis — {scorecard.artifact_name}",
            f"Date: {scorecard.date}  |  Analyst: value-ip plugin  |  Version: 1.0",
            "",
            "## FRAMEWORK VERDICTS",
            "",
            "| Framework | Score (1-5) | Structural Power Found | Notes |",
            "|-----------|-------------|------------------------|-------|",
            f"| Helmer 7 Powers | {scorecard.helmer.score}/5 | "
            f"{', '.join(p.power.value for p in scorecard.helmer.powers_found) or 'none'} | "
            f"{scorecard.helmer.verdict} |",
            f"| Blue Ocean ERRC | {scorecard.blue_ocean.score}/5 | "
            f"{'New value curve' if scorecard.blue_ocean.value_curve_differentiation else 'No new curve'} | "
            f"{scorecard.blue_ocean.verdict} |",
            f"| Christensen | {scorecard.christensen.score}/5 | "
            f"{scorecard.christensen.disruption_type.value} | "
            f"{scorecard.christensen.verdict} |",
            f"| Moore Core/Context | {scorecard.moore.score}/5 | "
            f"{scorecard.moore.core_percentage}% core | "
            f"{scorecard.moore.verdict} |",
            "",
            "## IP CLAIMS (True Differentiators)",
            "> IP claims listed here only if they survive ALL 4 framework tests.",
            "",
        ]

        if scorecard.ip_claims:
            for i, claim in enumerate(scorecard.ip_claims, 1):
                lines += [
                    f"{i}. **{claim.name}** — {claim.description}",
                    f"   - Helmer power: {claim.helmer_power}",
                    f"   - Blue Ocean: {claim.blue_ocean_value}",
                    f"   - Disruption type: {claim.disruption_type}",
                    f"   - Core vs. context: {claim.core_or_context} — protectable",
                    "",
                ]
        else:
            lines.append("_No IP claims survived all 4 framework tests._\n")

        lines += [
            "## OVERALL VERDICT",
            f"- TRUE DIFFERENTIATORS: {scorecard.true_differentiators}",
            f"- COMMODITIES POSING AS DIFFERENTIATORS: {scorecard.commodities_detected}",
            f"- RECOMMENDATION: **{verdict}**",
        ]

        return "\n".join(lines)

    def generate_devils_advocate(self, report: DevilsAdvocateReport) -> str:
        lines = [
            "## DEVIL'S ADVOCATE CHALLENGES",
            "> The team MUST respond to each challenge before this work is marked complete.",
            "",
        ]
        for i, challenge in enumerate(report.challenges, 1):
            lines += [
                f"### Challenge {i} — {challenge.agent}",
                f'"{challenge.challenge}"',
                "- [ ] Team response: _______________",
                "",
            ]
        return "\n".join(lines)
