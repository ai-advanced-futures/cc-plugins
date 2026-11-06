"""
Competitive Intelligence Plugin - JTBD Performance Analysis Lens

Analyzes competitor performance on Job-To-Be-Done steps.

Based on Outcome-Driven Innovation (ODI) framework:
- Jobs have 6 universal phases (Define, Locate, Prepare, Confirm, Execute, Monitor)
- Each phase has specific steps
- Performance measured on speed and accuracy (1-5 scale)
- Gaps identify competitive advantages and disadvantages

Key Features:
- Job decomposition into steps
- Speed/accuracy scoring (1-5)
- Performance gap calculation
- Customer impact assessment
- Feature-to-job-step mapping
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class UniversalJobPhase(Enum):
    """
    6 universal phases that all jobs go through.

    Based on ODI framework:
    1. DEFINE: Define what needs to be done
    2. LOCATE: Locate resources/inputs needed
    3. PREPARE: Prepare environment/setup
    4. CONFIRM: Confirm readiness to execute
    5. EXECUTE: Execute the main task
    6. MONITOR: Monitor results and completion
    """
    DEFINE = 1
    LOCATE = 2
    PREPARE = 3
    CONFIRM = 4
    EXECUTE = 5
    MONITOR = 6


@dataclass
class JobStep:
    """
    Individual step within a job.

    Attributes:
        step_number: Sequential step number
        phase: Which universal phase this belongs to
        step_name: Name of the step
        needs: Customer needs for this step (outcome statements)
    """
    step_number: int
    phase: UniversalJobPhase
    step_name: str
    needs: List[str] = field(default_factory=list)


@dataclass
class PerformanceScore:
    """
    Performance score for a job step.

    Scored on 1-5 scale:
    1 = Very Poor
    2 = Poor
    3 = Average
    4 = Good
    5 = Excellent

    Attributes:
        speed: How fast the step can be completed (1-5)
        accuracy: How accurately the step can be completed (1-5)
        overall: Overall score (average of speed and accuracy)
    """
    speed: float
    accuracy: float
    overall: float


@dataclass
class PerformanceGap:
    """
    Gap between our performance and competitor's.

    Positive gap = we're ahead
    Negative gap = we're behind

    Attributes:
        step_number: Job step number
        step_name: Job step name
        speed_gap: Difference in speed (ours - theirs)
        accuracy_gap: Difference in accuracy
        overall_gap: Difference in overall
    """
    step_number: int
    step_name: str
    speed_gap: float
    accuracy_gap: float
    overall_gap: float


class JTBDLens:
    """
    JTBD Performance Analysis Lens.

    Analyzes how well competitors help customers complete a job.

    Workflow:
    1. Decompose job into steps (across 6 universal phases)
    2. Score each competitor's performance on each step
    3. Calculate performance gaps
    4. Assess customer impact
    5. Identify opportunities
    """

    def __init__(self, job_statement: str):
        """
        Initialize JTBD lens.

        Args:
            job_statement: The job to be done (e.g., "Get user authentication set up")
        """
        self.job_statement = job_statement
        self.job_steps: List[JobStep] = []
        self.performance_scores: Dict[str, Dict[int, PerformanceScore]] = {}

    def add_job_step(self, step: JobStep):
        """
        Add a job step.

        Args:
            step: JobStep to add
        """
        self.job_steps.append(step)

    def decompose_job(self) -> List[JobStep]:
        """
        Decompose job into steps across 6 universal phases.

        In real implementation, this would use domain knowledge or ML.
        For now, generates generic steps for each phase.

        Returns:
            List of JobStep objects
        """
        steps = []

        # Generic decomposition (real implementation would be job-specific)
        phase_templates = {
            UniversalJobPhase.DEFINE: [
                "Define requirements and objectives",
                "Define success criteria"
            ],
            UniversalJobPhase.LOCATE: [
                "Locate necessary resources",
                "Locate required information"
            ],
            UniversalJobPhase.PREPARE: [
                "Prepare environment",
                "Prepare tools and inputs"
            ],
            UniversalJobPhase.CONFIRM: [
                "Confirm readiness",
                "Confirm prerequisites met"
            ],
            UniversalJobPhase.EXECUTE: [
                "Execute main task",
                "Execute verification"
            ],
            UniversalJobPhase.MONITOR: [
                "Monitor progress",
                "Monitor results and outcomes"
            ]
        }

        step_num = 1
        for phase in UniversalJobPhase:
            for template in phase_templates[phase]:
                step = JobStep(
                    step_number=step_num,
                    phase=phase,
                    step_name=template,
                    needs=[f"Minimize time to {template.lower()}"]
                )
                steps.append(step)
                self.add_job_step(step)
                step_num += 1

        return steps

    def score_competitor_performance(
        self,
        competitor_id: str,
        step_number: int,
        speed: float,
        accuracy: float
    ) -> PerformanceScore:
        """
        Score a competitor's performance on a job step.

        Args:
            competitor_id: Competitor identifier
            step_number: Job step number
            speed: Speed score (1-5)
            accuracy: Accuracy score (1-5)

        Returns:
            PerformanceScore
        """
        overall = calculate_overall_score(speed, accuracy)

        score = PerformanceScore(
            speed=speed,
            accuracy=accuracy,
            overall=overall
        )

        # Store score
        if competitor_id not in self.performance_scores:
            self.performance_scores[competitor_id] = {}

        self.performance_scores[competitor_id][step_number] = score

        return score

    def calculate_gaps(
        self,
        our_id: str,
        their_id: str
    ) -> List[PerformanceGap]:
        """
        Calculate performance gaps against a competitor.

        Args:
            our_id: Our competitor ID
            their_id: Their competitor ID

        Returns:
            List of PerformanceGap objects
        """
        gaps = []

        # Get scores
        our_scores = self.performance_scores.get(our_id, {})
        their_scores = self.performance_scores.get(their_id, {})

        # Calculate gaps for each step
        for step in self.job_steps:
            step_num = step.step_number

            # Skip if either competitor not scored for this step
            if step_num not in our_scores or step_num not in their_scores:
                continue

            our_score = our_scores[step_num]
            their_score = their_scores[step_num]

            gap = PerformanceGap(
                step_number=step_num,
                step_name=step.step_name,
                speed_gap=our_score.speed - their_score.speed,
                accuracy_gap=our_score.accuracy - their_score.accuracy,
                overall_gap=our_score.overall - their_score.overall
            )

            gaps.append(gap)

        return gaps

    def get_step_by_number(self, step_number: int) -> Optional[JobStep]:
        """
        Get job step by number.

        Args:
            step_number: Step number

        Returns:
            JobStep or None if not found
        """
        for step in self.job_steps:
            if step.step_number == step_number:
                return step
        return None


def calculate_overall_score(speed: float, accuracy: float) -> float:
    """
    Calculate overall score from speed and accuracy.

    Args:
        speed: Speed score (1-5)
        accuracy: Accuracy score (1-5)

    Returns:
        Overall score (average)
    """
    return (speed + accuracy) / 2.0


def calculate_performance_gap(
    our_score: PerformanceScore,
    their_score: PerformanceScore
) -> PerformanceGap:
    """
    Calculate performance gap.

    Args:
        our_score: Our performance score
        their_score: Their performance score

    Returns:
        PerformanceGap (positive = we're ahead, negative = we're behind)
    """
    return PerformanceGap(
        step_number=0,  # Will be set by caller
        step_name="",  # Will be set by caller
        speed_gap=our_score.speed - their_score.speed,
        accuracy_gap=our_score.accuracy - their_score.accuracy,
        overall_gap=our_score.overall - their_score.overall
    )


def assess_customer_impact(gap: PerformanceGap) -> str:
    """
    Assess customer impact of a performance gap.

    Args:
        gap: PerformanceGap

    Returns:
        Impact level: "high", "medium", or "low"
    """
    # Use overall gap to determine impact
    abs_gap = abs(gap.overall_gap)

    if abs_gap >= 2.0:
        return "high"
    elif abs_gap >= 1.0:
        return "medium"
    else:
        return "low"


def map_feature_to_steps(feature: str) -> List[JobStep]:
    """
    Map a feature to job steps it affects.

    In real implementation, would use feature analysis or ML.
    For now, uses keyword matching.

    Args:
        feature: Feature name/description

    Returns:
        List of JobStep objects this feature affects
    """
    feature_lower = feature.lower()

    # Keyword classifier pattern — duplicated across lens files for agent isolation.
    # Future: extract to shared KeywordClassifier class in a common module.
    # Keyword mapping (simplified)
    phase_keywords = {
        UniversalJobPhase.DEFINE: ["define", "requirement", "specification"],
        UniversalJobPhase.LOCATE: ["search", "find", "locate", "discover"],
        UniversalJobPhase.PREPARE: ["setup", "configure", "prepare", "install"],
        UniversalJobPhase.CONFIRM: ["verify", "validate", "confirm", "check", "auth"],
        UniversalJobPhase.EXECUTE: ["run", "execute", "process", "test", "deploy"],
        UniversalJobPhase.MONITOR: ["monitor", "track", "observe", "alert", "log"]
    }

    affected_phases = []
    for phase, keywords in phase_keywords.items():
        if any(keyword in feature_lower for keyword in keywords):
            affected_phases.append(phase)

    # Create generic steps for affected phases
    steps = []
    for phase in affected_phases:
        step = JobStep(
            step_number=0,  # Will be assigned properly in real usage
            phase=phase,
            step_name=f"{phase.name.title()} step affected by {feature}",
            needs=[f"Minimize time with {feature}"]
        )
        steps.append(step)

    # If no matches, default to EXECUTE phase
    if not steps:
        steps.append(JobStep(
            step_number=0,
            phase=UniversalJobPhase.EXECUTE,
            step_name=f"Execute with {feature}",
            needs=[]
        ))

    return steps


def analyze_jtbd_performance(
    job_statement: str,
    competitors: List[str],
    our_id: str = "us"
) -> Dict[str, Any]:
    """
    Analyze JTBD performance across competitors.

    Args:
        job_statement: The job to be done
        competitors: List of competitor names
        our_id: Our identifier (default: "us")

    Returns:
        Dict with analysis results
    """
    lens = JTBDLens(job_statement=job_statement)

    # Decompose job
    steps = lens.decompose_job()

    # Generate placeholder scores (real implementation would gather data)
    # For testing, assign default scores
    for step in steps:
        # Score ourselves (default: 3/3)
        lens.score_competitor_performance(
            competitor_id=our_id,
            step_number=step.step_number,
            speed=3.0,
            accuracy=3.0
        )

        # Score competitors (default: 3/3)
        for comp in competitors:
            lens.score_competitor_performance(
                competitor_id=comp,
                step_number=step.step_number,
                speed=3.0,
                accuracy=3.0
            )

    # Build analysis result
    analysis = {
        "job_statement": job_statement,
        "job_steps": [
            {
                "step_number": s.step_number,
                "phase": s.phase.name,
                "step_name": s.step_name,
                "needs": s.needs
            }
            for s in steps
        ],
        "competitor_performance": []
    }

    # Add performance data for each competitor
    for comp in competitors:
        comp_data = {
            "competitor_id": comp,
            "step_scores": []
        }

        for step in steps:
            if step.step_number in lens.performance_scores.get(comp, {}):
                score = lens.performance_scores[comp][step.step_number]
                comp_data["step_scores"].append({
                    "step_number": step.step_number,
                    "speed": score.speed,
                    "accuracy": score.accuracy,
                    "overall": score.overall
                })

        # Calculate overall score
        if comp_data["step_scores"]:
            avg_overall = sum(s["overall"] for s in comp_data["step_scores"]) / len(comp_data["step_scores"])
            comp_data["overall_score"] = avg_overall

        analysis["competitor_performance"].append(comp_data)

    return analysis


# Convenience functions

def create_job_step(
    step_number: int,
    phase: UniversalJobPhase,
    step_name: str,
    needs: Optional[List[str]] = None
) -> JobStep:
    """
    Convenience function to create job step.

    Args:
        step_number: Step number
        phase: Universal phase
        step_name: Step name
        needs: Customer needs (optional)

    Returns:
        JobStep
    """
    return JobStep(
        step_number=step_number,
        phase=phase,
        step_name=step_name,
        needs=needs or []
    )
