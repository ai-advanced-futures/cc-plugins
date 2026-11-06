"""
Competitive Intelligence Plugin - Phase 5: Synthesis & Assessment

Synthesizes findings from multiple lenses and assesses analysis quality.

Key Features:
- Multi-lens finding synthesis
- Key insight identification
- Overall confidence calculation
- Completeness assessment
- Gap analysis
- Insight prioritization

Insights identified:
- OPPORTUNITY: Favorable gaps to exploit
- THREAT: Risks from competitors
- STRENGTH: Our competitive advantages
- WEAKNESS: Our vulnerabilities
- TREND: Market/technology trends
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class InsightType(Enum):
    """
    Types of insights.

    - OPPORTUNITY: Favorable gap or weakness to exploit
    - THREAT: Risk from competitor or market
    - STRENGTH: Our competitive advantage
    - WEAKNESS: Our competitive vulnerability
    - TREND: Market or technology trend
    """
    OPPORTUNITY = "opportunity"
    THREAT = "threat"
    STRENGTH = "strength"
    WEAKNESS = "weakness"
    TREND = "trend"


class CompletionStatus(Enum):
    """
    Analysis completion status.

    - COMPLETE: All expected lenses executed
    - PARTIAL: Some lenses executed
    - INCOMPLETE: Few or no lenses executed
    """
    COMPLETE = "complete"
    PARTIAL = "partial"
    INCOMPLETE = "incomplete"


@dataclass
class Insight:
    """
    Key insight from analysis.

    Attributes:
        insight_type: Type of insight
        description: Detailed description
        confidence: Confidence level (high/medium/low)
        supporting_evidence: List of supporting evidence
        affected_competitors: Competitor IDs this affects
    """
    insight_type: InsightType
    description: str
    confidence: str  # "high", "medium", "low"
    supporting_evidence: List[str]
    affected_competitors: List[str]


@dataclass
class SynthesisResult:
    """
    Synthesis result.

    Attributes:
        insights: List of key insights
        overall_confidence: Overall confidence level
        completion_status: Analysis completion status
        gaps: List of gaps/missing data
        summary: Executive summary
    """
    insights: List[Insight]
    overall_confidence: str  # "high", "medium", "low"
    completion_status: CompletionStatus
    gaps: List[str]
    summary: str


class Synthesizer:
    """
    Findings synthesizer.

    Synthesizes findings from multiple analytical lenses.

    Workflow:
    1. Collect results from all lenses
    2. Identify cross-lens patterns and insights
    3. Calculate overall confidence
    4. Assess analysis completeness
    5. Identify gaps and missing data
    6. Prioritize insights
    7. Generate executive summary
    """

    def __init__(self, engine):
        """
        Initialize synthesizer.

        Args:
            engine: WorkflowEngine instance
        """
        self.engine = engine
        self.insights: List[Insight] = []

    def add_insight(self, insight: Insight):
        """
        Add insight.

        Args:
            insight: Insight to add
        """
        self.insights.append(insight)

    def get_insights_by_type(self, insight_type: InsightType) -> List[Insight]:
        """
        Get insights by type.

        Args:
            insight_type: Type to filter by

        Returns:
            List of insights of that type
        """
        return [i for i in self.insights if i.insight_type == insight_type]

    def run_synthesis(self) -> SynthesisResult:
        """
        Run synthesis process.

        Returns:
            SynthesisResult
        """
        # Get lens results from engine state
        lens_results = {}
        lenses_applied = self.engine.state.data.get("lenses_applied", [])

        for lens in lenses_applied:
            # Get lens results from engine data
            lens_data = self.engine.state.data.get(f"{lens}_results", {})
            lens_results[lens] = lens_data

        # Identify key insights
        insights = identify_key_insights(lens_results)
        self.insights.extend(insights)

        # Calculate overall confidence
        lens_confidence = {}
        for lens, results in lens_results.items():
            if isinstance(results, dict):
                lens_confidence[lens] = results.get("confidence", "medium")
            else:
                lens_confidence[lens] = "low"

        overall_confidence = calculate_overall_confidence(lens_confidence)

        # Assess completeness
        expected_lenses = 6  # All 6 analytical lenses
        completion_status, gaps = assess_completeness(lens_results, expected_lenses)

        # Generate summary
        summary = self._generate_summary(insights, overall_confidence, completion_status)

        # Update engine state
        self.engine.update_data({
            "synthesis_complete": True,
            "overall_confidence": overall_confidence,
            "completion_status": completion_status.value
        })

        return SynthesisResult(
            insights=self.insights,
            overall_confidence=overall_confidence,
            completion_status=completion_status,
            gaps=gaps,
            summary=summary
        )

    def _generate_summary(
        self,
        insights: List[Insight],
        confidence: str,
        status: CompletionStatus
    ) -> str:
        """
        Generate executive summary.

        Args:
            insights: List of insights
            confidence: Overall confidence
            status: Completion status

        Returns:
            Summary text
        """
        # Count insights by type
        opportunities = len([i for i in insights if i.insight_type == InsightType.OPPORTUNITY])
        threats = len([i for i in insights if i.insight_type == InsightType.THREAT])
        strengths = len([i for i in insights if i.insight_type == InsightType.STRENGTH])
        weaknesses = len([i for i in insights if i.insight_type == InsightType.WEAKNESS])

        summary = f"Analysis {status.value} with {confidence} confidence. "
        summary += f"Identified {opportunities} opportunities, {threats} threats, "
        summary += f"{strengths} strengths, and {weaknesses} weaknesses."

        return summary


def identify_key_insights(lens_results: Dict[str, Any]) -> List[Insight]:
    """
    Identify key insights from lens results.

    Args:
        lens_results: Results from all lenses

    Returns:
        List of Insight objects
    """
    insights = []

    # Analyze JTBD Performance lens
    if "jtbd_performance" in lens_results:
        jtbd = lens_results["jtbd_performance"]
        if isinstance(jtbd, dict) and "gaps" in jtbd:
            for gap in jtbd.get("gaps", []):
                if isinstance(gap, dict) and gap.get("gap", 0) < -1.0:
                    # Competitor significantly behind
                    insights.append(Insight(
                        insight_type=InsightType.OPPORTUNITY,
                        description=f"Performance gap in {gap.get('step', 'unknown')}",
                        confidence="high",
                        supporting_evidence=["JTBD analysis"],
                        affected_competitors=[]
                    ))

    # Analyze Forces lens
    if "forces" in lens_results:
        forces = lens_results["forces"]
        if isinstance(forces, dict) and "momentum" in forces:
            momentum = forces["momentum"]
            if isinstance(momentum, dict):
                direction = momentum.get("direction", "")
                if direction == "toward_switch":
                    insights.append(Insight(
                        insight_type=InsightType.OPPORTUNITY,
                        description="Strong switching momentum in our favor",
                        confidence="high",
                        supporting_evidence=["Forces analysis"],
                        affected_competitors=[]
                    ))

    # Analyze Technology Disruption lens
    if "technology_disruption" in lens_results:
        tech = lens_results["technology_disruption"]
        if isinstance(tech, dict):
            disruption = tech.get("disruption_potential", "")
            if disruption in ["very_high", "high"]:
                insights.append(Insight(
                    insight_type=InsightType.THREAT,
                    description="High disruption potential identified",
                    confidence="high",
                    supporting_evidence=["Technology disruption analysis"],
                    affected_competitors=[]
                ))

    # Analyze Economic Value lens
    if "economic_value" in lens_results:
        value = lens_results["economic_value"]
        if isinstance(value, dict) and "moats" in value:
            moats = value.get("moats", [])
            if len(moats) >= 2:
                insights.append(Insight(
                    insight_type=InsightType.STRENGTH,
                    description="Multiple economic moats identified",
                    confidence="medium",
                    supporting_evidence=["Economic value analysis"],
                    affected_competitors=[]
                ))

    return insights


def assess_completeness(
    lens_results: Dict[str, Any],
    expected_lenses: int = 6
) -> Tuple[CompletionStatus, List[str]]:
    """
    Assess analysis completeness.

    Args:
        lens_results: Results from lenses
        expected_lenses: Expected number of lenses

    Returns:
        Tuple of (CompletionStatus, list of gaps)
    """
    executed_lenses = len([r for r in lens_results.values() if r is not None])
    gaps = []

    # Determine completion status
    completion_percentage = executed_lenses / expected_lenses if expected_lenses > 0 else 0

    if completion_percentage >= 1.0:
        status = CompletionStatus.COMPLETE
    elif completion_percentage >= 0.3:  # 30% threshold for partial (2+ out of 6)
        status = CompletionStatus.PARTIAL
        gaps.append(f"Only {executed_lenses}/{expected_lenses} lenses executed")
    else:
        status = CompletionStatus.INCOMPLETE
        gaps.append(f"Insufficient analysis: {executed_lenses}/{expected_lenses} lenses")

    # Identify specific missing lenses
    all_lenses = [
        "jtbd_performance",
        "forces",
        "economic_value",
        "strategic_positioning",
        "technology_disruption",
        "loss_churn"
    ]

    for lens in all_lenses:
        if lens not in lens_results or lens_results[lens] is None:
            gaps.append(f"Missing {lens} analysis")

    return status, gaps


def calculate_overall_confidence(lens_confidence: Dict[str, str]) -> str:
    """
    Calculate overall confidence from lens confidences.

    Args:
        lens_confidence: Dict mapping lens name to confidence level

    Returns:
        Overall confidence level (high/medium/low)
    """
    if not lens_confidence:
        return "low"

    # Map confidence to numeric scores
    confidence_scores = {
        "high": 3,
        "medium": 2,
        "low": 1
    }

    # Calculate average score
    total_score = 0
    count = 0

    for lens, confidence in lens_confidence.items():
        score = confidence_scores.get(confidence, 1)
        total_score += score
        count += 1

    if count == 0:
        return "low"

    avg_score = total_score / count

    # Map back to confidence level
    if avg_score >= 2.5:
        return "high"
    elif avg_score >= 1.5:
        return "medium"
    else:
        return "low"


def synthesize_findings(lens_results: Dict[str, Any]) -> SynthesisResult:
    """
    Synthesize findings from all lenses.

    Args:
        lens_results: Results from all lenses

    Returns:
        SynthesisResult
    """
    # Identify insights
    insights = identify_key_insights(lens_results)

    # Calculate overall confidence
    lens_confidence = {}
    for lens, results in lens_results.items():
        if isinstance(results, dict):
            lens_confidence[lens] = results.get("confidence", "medium")
        else:
            lens_confidence[lens] = "low"

    overall_confidence = calculate_overall_confidence(lens_confidence)

    # Assess completeness
    completion_status, gaps = assess_completeness(lens_results, expected_lenses=6)

    # Generate summary
    opportunities = len([i for i in insights if i.insight_type == InsightType.OPPORTUNITY])
    threats = len([i for i in insights if i.insight_type == InsightType.THREAT])
    strengths = len([i for i in insights if i.insight_type == InsightType.STRENGTH])
    weaknesses = len([i for i in insights if i.insight_type == InsightType.WEAKNESS])

    summary = f"Analysis {completion_status.value} with {overall_confidence} confidence. "
    summary += f"Identified {opportunities} opportunities, {threats} threats, "
    summary += f"{strengths} strengths, and {weaknesses} weaknesses."

    return SynthesisResult(
        insights=insights,
        overall_confidence=overall_confidence,
        completion_status=completion_status,
        gaps=gaps,
        summary=summary
    )


# Convenience functions

def create_insight(
    insight_type: InsightType,
    description: str,
    confidence: str = "medium",
    evidence: Optional[List[str]] = None,
    competitors: Optional[List[str]] = None
) -> Insight:
    """
    Convenience function to create insight.

    Args:
        insight_type: Type of insight
        description: Description
        confidence: Confidence level
        evidence: Supporting evidence
        competitors: Affected competitors

    Returns:
        Insight
    """
    return Insight(
        insight_type=insight_type,
        description=description,
        confidence=confidence,
        supporting_evidence=evidence or [],
        affected_competitors=competitors or []
    )
