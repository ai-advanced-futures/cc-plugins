"""
IP claim extraction logic.

An IP claim is only listed if it survives ALL 4 framework tests.
Confidence is derived from the average framework score.
"""
from dataclasses import dataclass
from typing import List

from .frameworks import (
    HelmerAnalysis,
    BlueOceanAnalysis,
    ChristensenAnalysis,
    MooreAnalysis,
    IPClaim,
)

MIN_SCORE_FOR_HIGH = 4
MIN_SCORE_FOR_MEDIUM = 3


@dataclass
class ClaimCandidate:
    name: str
    description: str
    raw_evidence: str


def score_claim_confidence(
    helmer_score: int,
    blue_ocean_score: int,
    christensen_score: int,
    moore_score: int,
) -> str:
    avg = (helmer_score + blue_ocean_score + christensen_score + moore_score) / 4.0
    if avg >= MIN_SCORE_FOR_HIGH:
        return "high"
    elif avg >= MIN_SCORE_FOR_MEDIUM:
        return "medium"
    return "low"


def deduplicate_claims(claims: List[IPClaim]) -> List[IPClaim]:
    seen = set()
    result = []
    for claim in claims:
        if claim.name not in seen:
            seen.add(claim.name)
            result.append(claim)
    return result


def extract_ip_claims(
    candidates: List[ClaimCandidate],
    helmer: HelmerAnalysis,
    blue_ocean: BlueOceanAnalysis,
    christensen: ChristensenAnalysis,
    moore: MooreAnalysis,
    min_score_threshold: int = 3,
) -> List[IPClaim]:
    extractor = IPExtractor(min_score_threshold=min_score_threshold)
    return extractor.extract(candidates, helmer=helmer, blue_ocean=blue_ocean,
                             christensen=christensen, moore=moore)


class IPExtractor:
    def __init__(self, min_score_threshold: int = 3, require_all_frameworks: bool = True):
        self.min_score_threshold = min_score_threshold
        self.require_all_frameworks = require_all_frameworks

    def extract(
        self,
        candidates: List[ClaimCandidate],
        helmer: HelmerAnalysis,
        blue_ocean: BlueOceanAnalysis,
        christensen: ChristensenAnalysis,
        moore: MooreAnalysis,
    ) -> List[IPClaim]:
        if self.require_all_frameworks:
            scores = [helmer.score, blue_ocean.score, christensen.score, moore.score]
            if any(s < self.min_score_threshold for s in scores):
                return []

        claims = []
        for candidate in candidates:
            confidence = score_claim_confidence(
                helmer.score, blue_ocean.score, christensen.score, moore.score
            )
            # Note: records only the first (highest-priority) Helmer power.
            # Helmer agent must list powers in priority order.
            helmer_power = (
                helmer.powers_found[0].power.value if helmer.powers_found else "none"
            )
            claim = IPClaim(
                name=candidate.name,
                description=candidate.description,
                helmer_power=helmer_power.upper(),
                # Note: records only the first (highest-priority) Blue Ocean Create element.
                # Blue Ocean agent must list Create elements in priority order.
                blue_ocean_value=(blue_ocean.create[0] if blue_ocean.create else ""),
                disruption_type=christensen.disruption_type.value,
                core_or_context="CORE" if moore.core_percentage > 60 else "CONTEXT",
                confidence=confidence,
            )
            claims.append(claim)

        return deduplicate_claims(claims)
