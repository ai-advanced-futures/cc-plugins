from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class TruthTier(Enum):
    SHIPPED = 1
    IN_FLIGHT = 2
    COMMITTED = 3
    STRATEGIC_INTENT = 4
    SPECULATION = 5


_SUPERLATIVES_PATH = Path(__file__).parent.parent / "definitions" / "superlatives.txt"
SUPERLATIVES: set[str] = {
    line.strip()
    for line in _SUPERLATIVES_PATH.read_text().splitlines()
    if line.strip() and not line.startswith("#")
}

# Word-boundary-aware pattern. Sorted longest-first so multi-word phrases take precedence.
# Uses (?<!\w) / (?!\w) instead of \b to handle non-word-char tokens like "#1".
_SUPERLATIVE_PATTERN = re.compile(
    '|'.join(
        r'(?<!\w)' + re.escape(s) + r'(?!\w)'
        for s in sorted(SUPERLATIVES, key=len, reverse=True)
    ),
    re.IGNORECASE,
)

QUANTIFIED_CLAIM_PATTERN = re.compile(r'\d+\s*%|\d+x|\d+\s+times', re.IGNORECASE)
FUTURE_TENSE_PATTERN = re.compile(r'\b(will|shall|going to|soon|upcoming)\b', re.IGNORECASE)
SOURCE_PATTERN = re.compile(r'\(source:|source:|per |according to', re.IGNORECASE)


@dataclass
class TierResult:
    tier: TruthTier
    blocked: bool = False
    reason: str = ""


@dataclass
class AuditReport:
    claims: list[dict]
    tier_results: list[TierResult]
    language_issues: list[str]
    integrity_score: float
    blocked_count: int


class TruthTierValidator:
    def classify(self, claim: dict[str, Any]) -> TierResult:
        evidence = claim.get("evidence")

        if evidence is None:
            return TierResult(tier=TruthTier.SPECULATION, blocked=True, reason="No evidence provided")

        etype = evidence.get("type", "")

        if etype in ("code", "released", "ga", "tested"):
            return TierResult(tier=TruthTier.SHIPPED)

        if etype in ("beta", "early_access", "in_progress", "changelog"):
            return TierResult(tier=TruthTier.IN_FLIGHT)

        if etype == "roadmap":
            if evidence.get("budget") and evidence.get("exec_sponsor"):
                return TierResult(tier=TruthTier.COMMITTED)
            missing = [f for f in ("budget", "exec_sponsor") if not evidence.get(f)]
            reason = f"Roadmap missing: {', '.join(missing)}" if missing else ""
            return TierResult(tier=TruthTier.STRATEGIC_INTENT, reason=reason)

        if etype == "vision":
            return TierResult(tier=TruthTier.STRATEGIC_INTENT)

        return TierResult(tier=TruthTier.SPECULATION, blocked=True, reason=f"Unknown evidence type: {etype}")

    def check_language(self, text: str) -> list[str]:
        issues = []
        if self._is_superlative(text):
            issues.append("Superlative claim requires benchmark data or must be demoted")
        if QUANTIFIED_CLAIM_PATTERN.search(text) and not SOURCE_PATTERN.search(text):
            issues.append("Quantified claim requires data source in parentheses")
        if FUTURE_TENSE_PATTERN.search(text):
            issues.append("Future tense used — verify this is a Tier 3+ claim with proper evidence")
        return issues

    def _is_superlative(self, text: str) -> bool:
        return bool(_SUPERLATIVE_PATTERN.search(text))

    def audit(self, claims: list[dict[str, Any]]) -> AuditReport:
        tier_results = [self.classify(c) for c in claims]
        all_issues: list[str] = []
        for c in claims:
            all_issues.extend(self.check_language(c.get("text", "")))

        blocked = sum(1 for r in tier_results if r.blocked)
        total = len(claims)
        # Canonical formula (definitions/integrity-score.md):
        #   integrity_score = (total_claims - Tier_5_blocked) / total_claims
        # The denominator is total_claims (INCLUDING Tier 5) — Tier 5 (blocked) claims
        # reduce the score. When all claims are Tier 5: blocked == total → score = 0.0.
        # Empty claim set (total == 0) → score = 1.0 (no claims reviewed = no violations).
        # Language issues are advisory only — they appear in language_issues but do NOT reduce the score.
        eligible = total - blocked
        if total == 0:
            score = 1.0  # no claims reviewed = no violations
        else:
            score = eligible / total

        return AuditReport(
            claims=claims,
            tier_results=tier_results,
            language_issues=all_issues,
            integrity_score=round(score, 2),
            blocked_count=blocked,
        )
