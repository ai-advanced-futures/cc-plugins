"""
Core data structures for Value & IP analysis.

Implements dataclasses for all four framework analyses:
- Helmer's 7 Powers
- Blue Ocean ERRC
- Christensen Disruption Theory
- Moore Core vs. Context

Plus IPClaim, FrameworkVerdict, OverallVerdict, and ValueIPScorecard.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List


# ─── Helmer's 7 Powers ────────────────────────────────────────────────────────

class HelmerPower(Enum):
    SCALE_ECONOMIES = "scale_economies"
    NETWORK_EFFECTS = "network_effects"
    COUNTER_POSITIONING = "counter_positioning"
    SWITCHING_COSTS = "switching_costs"
    BRANDING = "branding"
    CORNERED_RESOURCE = "cornered_resource"
    PROCESS_POWER = "process_power"


@dataclass
class HelmerPowerResult:
    power: HelmerPower
    score: int  # 1-5
    evidence: str

    def __post_init__(self):
        if not 1 <= self.score <= 5:
            raise ValueError(f"Score must be 1-5, got {self.score}")


@dataclass
class HelmerAnalysis:
    powers_found: List[HelmerPowerResult]
    score: int  # 1-5 overall
    structural_barriers: List[str]
    verdict: str


# ─── Blue Ocean ERRC ──────────────────────────────────────────────────────────

class ERRCAction(Enum):
    ELIMINATE = "eliminate"
    REDUCE = "reduce"
    RAISE = "raise"
    CREATE = "create"


@dataclass
class BlueOceanAnalysis:
    eliminate: List[str]
    reduce: List[str]
    raise_factors: List[str]
    create: List[str]
    value_curve_differentiation: bool
    non_customer_opportunity: str
    score: int  # 1-5
    verdict: str


# ─── Christensen Disruption ───────────────────────────────────────────────────

class DisruptionType(Enum):
    DISRUPTIVE = "disruptive"
    SUSTAINING = "sustaining"
    NEW_MARKET = "new_market"


@dataclass
class ChristensenAnalysis:
    disruption_type: DisruptionType
    target_segment: str
    jobs_to_be_done: str
    incumbent_vulnerability: str
    score: int  # 1-5
    verdict: str


# ─── Moore Core vs. Context ───────────────────────────────────────────────────

class CoreContextClassification(Enum):
    CORE_DOMINANT = "core_dominant"       # >60% core
    BALANCED = "balanced"                  # 40-60% core
    CONTEXT_DOMINANT = "context_dominant"  # <40% core


@dataclass
class MooreAnalysis:
    core_elements: List[str]
    context_elements: List[str]
    core_percentage: int  # 0-100
    classification: CoreContextClassification
    score: int  # 1-5
    verdict: str


# ─── IP Claim ─────────────────────────────────────────────────────────────────

VALID_CONFIDENCE = {"high", "medium", "low"}


@dataclass
class IPClaim:
    name: str
    description: str
    helmer_power: str
    blue_ocean_value: str
    disruption_type: str
    core_or_context: str
    confidence: str  # high/medium/low

    def __post_init__(self):
        if self.confidence not in VALID_CONFIDENCE:
            raise ValueError(f"confidence must be one of {VALID_CONFIDENCE}, got '{self.confidence}'")


# ─── Scorecard ────────────────────────────────────────────────────────────────

class OverallVerdict(Enum):
    PASS = "PASS"
    CONDITIONAL = "CONDITIONAL"
    FAIL = "FAIL"


@dataclass
class FrameworkVerdict:
    framework: str
    score: int
    power_found: str
    notes: str


@dataclass
class ValueIPScorecard:
    artifact_name: str
    helmer: HelmerAnalysis
    blue_ocean: BlueOceanAnalysis
    christensen: ChristensenAnalysis
    moore: MooreAnalysis
    ip_claims: List[IPClaim]
    commodities_detected: int
    date: str = ""

    @property
    def average_score(self) -> float:
        return (
            self.helmer.score
            + self.blue_ocean.score
            + self.christensen.score
            + self.moore.score
        ) / 4.0

    @property
    def true_differentiators(self) -> int:
        return len(self.ip_claims)

    @property
    def overall_verdict(self) -> OverallVerdict:
        avg = self.average_score
        if avg >= 3.5:
            return OverallVerdict.PASS
        elif avg >= 2.0:
            return OverallVerdict.CONDITIONAL
        else:
            return OverallVerdict.FAIL
