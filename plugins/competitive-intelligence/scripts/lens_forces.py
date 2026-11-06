"""
Competitive Intelligence Plugin - Forces Analysis Lens

Analyzes the 4 forces that drive or inhibit customer switching behavior.

Based on Jobs To Be Done Forces framework:
- PUSH forces: Pain with current solution (drives switching)
- PULL forces: Attraction to new solution (drives switching)
- ANXIETY forces: Fear of change/unknown (inhibits switching)
- HABIT forces: Comfort with current state (inhibits switching)

Key Features:
- 4 forces identification and measurement
- Force strength scoring (1-5 scale)
- Switching momentum calculation
- Feature-to-force mapping
- Competitor force profiles
- Force balance assessment
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ForceType(Enum):
    """
    4 forces that drive or inhibit switching.

    Switching forces (drive change):
    - PUSH: Pain/frustration with current solution
    - PULL: Attraction/benefits of new solution

    Resistance forces (inhibit change):
    - ANXIETY: Fear of change, uncertainty, risk
    - HABIT: Comfort with status quo, switching costs
    """
    PUSH = "push"
    PULL = "pull"
    ANXIETY = "anxiety"
    HABIT = "habit"


class ForceStrength(Enum):
    """
    Force strength measurement (1-5 scale).

    1 = Very weak force
    2 = Weak force
    3 = Moderate force
    4 = Strong force
    5 = Very strong force
    """
    VERY_WEAK = 1
    WEAK = 2
    MODERATE = 3
    STRONG = 4
    VERY_STRONG = 5


@dataclass
class Force:
    """
    Individual force affecting switching behavior.

    Attributes:
        force_type: Type of force (push/pull/anxiety/habit)
        description: Description of this force
        strength: How strong this force is (1-5)
        evidence: Supporting evidence for this force
    """
    force_type: ForceType
    description: str
    strength: ForceStrength
    evidence: List[str] = field(default_factory=list)


@dataclass
class SwitchingMomentum:
    """
    Net momentum toward or against switching.

    Calculated as:
    momentum = (push + pull) - (anxiety + habit)

    Positive momentum = toward switching
    Negative momentum = against switching
    Zero momentum = balanced (unlikely to switch)

    Attributes:
        push_strength: Push force strength (1-5)
        pull_strength: Pull force strength (1-5)
        anxiety_strength: Anxiety force strength (1-5)
        habit_strength: Habit force strength (1-5)
        net_momentum: Net momentum score
        direction: Direction of momentum (toward_switch/against_switch/neutral)
    """
    push_strength: float
    pull_strength: float
    anxiety_strength: float
    habit_strength: float
    net_momentum: float
    direction: str  # "toward_switch", "against_switch", "neutral"


@dataclass
class ForcesProfile:
    """
    Forces profile for a competitor.

    Contains all forces affecting switching to/from this competitor.

    Attributes:
        competitor_id: Competitor identifier
        push_forces: Forces pushing away from current solution
        pull_forces: Forces pulling toward new solution
        anxiety_forces: Forces creating fear/uncertainty
        habit_forces: Forces keeping with current solution
        switching_momentum: Calculated switching momentum
    """
    competitor_id: str
    push_forces: List[Force]
    pull_forces: List[Force]
    anxiety_forces: List[Force]
    habit_forces: List[Force]
    switching_momentum: Optional[SwitchingMomentum] = None


class ForcesLens:
    """
    Forces Analysis Lens.

    Analyzes the forces driving or inhibiting customer switching.

    Workflow:
    1. Identify forces for each competitor
    2. Measure force strengths (1-5 scale)
    3. Calculate switching momentum
    4. Assess force balance
    5. Identify opportunities to strengthen/weaken forces
    """

    def __init__(self, job_statement: str):
        """
        Initialize forces lens.

        Args:
            job_statement: The job customers are trying to get done
        """
        self.job_statement = job_statement
        self.profiles: Dict[str, ForcesProfile] = {}

    def add_force(
        self,
        competitor_id: str,
        force_type: ForceType,
        description: str,
        strength: ForceStrength,
        evidence: Optional[List[str]] = None
    ):
        """
        Add a force to competitor profile.

        Args:
            competitor_id: Competitor identifier
            force_type: Type of force
            description: Force description
            strength: Force strength (1-5)
            evidence: Supporting evidence
        """
        # Create profile if doesn't exist
        if competitor_id not in self.profiles:
            self.profiles[competitor_id] = ForcesProfile(
                competitor_id=competitor_id,
                push_forces=[],
                pull_forces=[],
                anxiety_forces=[],
                habit_forces=[],
                switching_momentum=None
            )

        # Create force
        force = Force(
            force_type=force_type,
            description=description,
            strength=strength,
            evidence=evidence or []
        )

        # Add to appropriate list
        profile = self.profiles[competitor_id]
        if force_type == ForceType.PUSH:
            profile.push_forces.append(force)
        elif force_type == ForceType.PULL:
            profile.pull_forces.append(force)
        elif force_type == ForceType.ANXIETY:
            profile.anxiety_forces.append(force)
        elif force_type == ForceType.HABIT:
            profile.habit_forces.append(force)

    def calculate_momentum(self, competitor_id: str) -> Optional[SwitchingMomentum]:
        """
        Calculate switching momentum for competitor.

        Args:
            competitor_id: Competitor identifier

        Returns:
            SwitchingMomentum or None if profile doesn't exist
        """
        if competitor_id not in self.profiles:
            return None

        profile = self.profiles[competitor_id]

        # Calculate average strength for each force type
        push_avg = self._calculate_average_strength(profile.push_forces)
        pull_avg = self._calculate_average_strength(profile.pull_forces)
        anxiety_avg = self._calculate_average_strength(profile.anxiety_forces)
        habit_avg = self._calculate_average_strength(profile.habit_forces)

        # Calculate momentum
        momentum = calculate_switching_momentum(
            push_strength=push_avg,
            pull_strength=pull_avg,
            anxiety_strength=anxiety_avg,
            habit_strength=habit_avg
        )

        # Store in profile
        profile.switching_momentum = momentum

        return momentum

    def _calculate_average_strength(self, forces: List[Force]) -> float:
        """
        Calculate average strength of forces.

        Args:
            forces: List of forces

        Returns:
            Average strength (0 if no forces)
        """
        if not forces:
            return 0.0

        total = sum(f.strength.value for f in forces)
        return total / len(forces)

    def get_profile(self, competitor_id: str) -> Optional[ForcesProfile]:
        """
        Get forces profile for competitor.

        Args:
            competitor_id: Competitor identifier

        Returns:
            ForcesProfile or None if not found
        """
        return self.profiles.get(competitor_id)

    def get_all_profiles(self) -> List[ForcesProfile]:
        """
        Get all competitor profiles.

        Returns:
            List of ForcesProfile objects
        """
        return list(self.profiles.values())


def calculate_switching_momentum(
    push_strength: float,
    pull_strength: float,
    anxiety_strength: float,
    habit_strength: float
) -> SwitchingMomentum:
    """
    Calculate net switching momentum.

    Formula: (push + pull) - (anxiety + habit)

    Args:
        push_strength: Push force strength (1-5)
        pull_strength: Pull force strength (1-5)
        anxiety_strength: Anxiety force strength (1-5)
        habit_strength: Habit force strength (1-5)

    Returns:
        SwitchingMomentum with direction
    """
    # Calculate net momentum
    switching_forces = push_strength + pull_strength
    resistance_forces = anxiety_strength + habit_strength
    net_momentum = switching_forces - resistance_forces

    # Determine direction
    if net_momentum > 0:
        direction = "toward_switch"
    elif net_momentum < 0:
        direction = "against_switch"
    else:
        direction = "neutral"

    return SwitchingMomentum(
        push_strength=push_strength,
        pull_strength=pull_strength,
        anxiety_strength=anxiety_strength,
        habit_strength=habit_strength,
        net_momentum=net_momentum,
        direction=direction
    )


def map_feature_to_forces(feature: str) -> List[Force]:
    """
    Map a feature to forces it affects.

    In real implementation, would use ML or detailed analysis.
    For now, uses keyword matching.

    Args:
        feature: Feature name/description

    Returns:
        List of Force objects this feature affects
    """
    feature_lower = feature.lower()
    forces = []

    # Keyword classifier pattern — duplicated across lens files for agent isolation.
    # Future: extract to shared KeywordClassifier class in a common module.
    # Keywords for each force type
    force_keywords = {
        ForceType.PUSH: {
            "keywords": ["slow", "expensive", "cost", "difficult", "complex", "hard", "frustrat", "pain", "problem"],
            "strength": ForceStrength.MODERATE
        },
        ForceType.PULL: {
            "keywords": ["fast", "easy", "simple", "cheap", "affordable", "benefit", "better", "improv"],
            "strength": ForceStrength.MODERATE
        },
        ForceType.ANXIETY: {
            "keywords": ["complex", "migration", "uncertain", "risk", "difficult", "unknown"],
            "strength": ForceStrength.MODERATE
        },
        ForceType.HABIT: {
            "keywords": ["familiar", "existing", "current", "established", "proven"],
            "strength": ForceStrength.MODERATE
        }
    }

    # Check for matches
    for force_type, config in force_keywords.items():
        if any(keyword in feature_lower for keyword in config["keywords"]):
            force = Force(
                force_type=force_type,
                description=f"{force_type.value.title()} force from: {feature}",
                strength=config["strength"],
                evidence=[feature]
            )
            forces.append(force)

    # If no matches, assume it's a pull force (benefit)
    if not forces:
        forces.append(Force(
            force_type=ForceType.PULL,
            description=f"Pull force from: {feature}",
            strength=ForceStrength.MODERATE,
            evidence=[feature]
        ))

    return forces


def assess_force_balance(profile: ForcesProfile) -> Dict[str, Any]:
    """
    Assess force balance for a competitor.

    Args:
        profile: ForcesProfile to assess

    Returns:
        Dict with balance assessment
    """
    if profile.switching_momentum is None:
        return {
            "favorable": None,
            "net_momentum": 0,
            "assessment": "No momentum calculated"
        }

    momentum = profile.switching_momentum

    assessment = {
        "favorable": momentum.net_momentum > 0,
        "net_momentum": momentum.net_momentum,
        "direction": momentum.direction,
        "switching_forces": momentum.push_strength + momentum.pull_strength,
        "resistance_forces": momentum.anxiety_strength + momentum.habit_strength
    }

    # Add interpretation
    if momentum.net_momentum > 2:
        assessment["assessment"] = "Strong momentum toward switching"
    elif momentum.net_momentum > 0:
        assessment["assessment"] = "Moderate momentum toward switching"
    elif momentum.net_momentum == 0:
        assessment["assessment"] = "Balanced forces - unlikely to switch"
    elif momentum.net_momentum > -2:
        assessment["assessment"] = "Moderate resistance to switching"
    else:
        assessment["assessment"] = "Strong resistance to switching"

    return assessment


def analyze_forces(
    job_statement: str,
    competitors: List[str],
    our_id: str = "us"
) -> Dict[str, Any]:
    """
    Analyze forces across competitors.

    Args:
        job_statement: The job to be done
        competitors: List of competitor names
        our_id: Our identifier (default: "us")

    Returns:
        Dict with forces analysis results
    """
    lens = ForcesLens(job_statement=job_statement)

    # Generate placeholder forces for testing
    # Real implementation would gather actual data

    for comp in competitors:
        # Add default forces (would be real data in production)
        lens.add_force(
            competitor_id=comp,
            force_type=ForceType.PUSH,
            description=f"Push force for {comp}",
            strength=ForceStrength.MODERATE,
            evidence=[]
        )

        lens.add_force(
            competitor_id=comp,
            force_type=ForceType.PULL,
            description=f"Pull force for {comp}",
            strength=ForceStrength.MODERATE,
            evidence=[]
        )

        lens.add_force(
            competitor_id=comp,
            force_type=ForceType.ANXIETY,
            description=f"Anxiety force for {comp}",
            strength=ForceStrength.MODERATE,
            evidence=[]
        )

        lens.add_force(
            competitor_id=comp,
            force_type=ForceType.HABIT,
            description=f"Habit force for {comp}",
            strength=ForceStrength.MODERATE,
            evidence=[]
        )

        # Calculate momentum
        lens.calculate_momentum(comp)

    # Build analysis result
    analysis = {
        "job_statement": job_statement,
        "competitor_profiles": []
    }

    # Add profile data for each competitor
    for profile in lens.get_all_profiles():
        profile_data = {
            "competitor_id": profile.competitor_id,
            "push_forces": [
                {
                    "description": f.description,
                    "strength": f.strength.value,
                    "evidence": f.evidence
                }
                for f in profile.push_forces
            ],
            "pull_forces": [
                {
                    "description": f.description,
                    "strength": f.strength.value,
                    "evidence": f.evidence
                }
                for f in profile.pull_forces
            ],
            "anxiety_forces": [
                {
                    "description": f.description,
                    "strength": f.strength.value,
                    "evidence": f.evidence
                }
                for f in profile.anxiety_forces
            ],
            "habit_forces": [
                {
                    "description": f.description,
                    "strength": f.strength.value,
                    "evidence": f.evidence
                }
                for f in profile.habit_forces
            ]
        }

        # Add momentum if calculated
        if profile.switching_momentum:
            m = profile.switching_momentum
            profile_data["switching_momentum"] = {
                "push_strength": m.push_strength,
                "pull_strength": m.pull_strength,
                "anxiety_strength": m.anxiety_strength,
                "habit_strength": m.habit_strength,
                "net_momentum": m.net_momentum,
                "direction": m.direction
            }

            # Add balance assessment
            profile_data["force_balance"] = assess_force_balance(profile)

        analysis["competitor_profiles"].append(profile_data)

    return analysis


# Convenience functions

def create_force(
    force_type: ForceType,
    description: str,
    strength: ForceStrength,
    evidence: Optional[List[str]] = None
) -> Force:
    """
    Convenience function to create a force.

    Args:
        force_type: Type of force
        description: Force description
        strength: Force strength
        evidence: Supporting evidence (optional)

    Returns:
        Force object
    """
    return Force(
        force_type=force_type,
        description=description,
        strength=strength,
        evidence=evidence or []
    )
