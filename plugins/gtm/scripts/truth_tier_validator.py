# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Score the claims of one integrity audit.

Run it by its path. It puts its own plugin folder on sys.path, never the cwd:
    uv run "${CLAUDE_PLUGIN_ROOT}/scripts/truth_tier_validator.py" --root <project> --agent <agent>

It reads .gtm/audit/<agent>-integrity.json, which holds a list `claims`. It adds
`integrity_score`, `total_claims`, `tier5_blocked`, `by_tier`, `floor_breached`,
`band` and `scored_by`, and writes the file back. The band is "floor" below
INTEGRITY_FLOOR, "choice" below INTEGRITY_TARGET, and "pass" above. It prints one
line and exits 0. Exit 2: the file cannot be read or does not hold valid claims.
Exit 3: the list `claims` is empty, and the script writes nothing. An audit with 0 claims
has no integrity score: `truth_tier_validator.py` exits 3 with the gap `no_claims`, and the
run stops with no file in `gtm-output/`.

A floor holds. Phase audit of the integrity agent takes the Tier 5 claims out of the drafts, so
a second audit of the same drafts counts only the claims that stayed, and its score is too high.
On band "floor" the script keeps the scored audit and the sha256 of each draft in
.gtm/audit/<agent>-floor-hold.json, and it sets `completion_flags.<agent>` of gtm-context.json
to false: the content agent must write new drafts. On a later call, while that flag is not true
or no draft has changed, the script writes the kept audit back, gives no new score, prints one
line with the gap `floor_holds`, and exits 4. When the flag is true and a draft has changed, the
script scores the new audit. A new band "choice" or "pass" removes the kept file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from scripts.gtm_constants import INTEGRITY_AGENTS, INTEGRITY_FLOOR, INTEGRITY_TARGET  # noqa: E402
from scripts.integrity_manifest import AGENT_MANIFESTS  # noqa: E402

FLOOR_HOLDS = 4  # the exit code of a call while an earlier floor holds


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


class NoClaims(Exception):
    """The audit holds 0 claims, so it has no integrity score (STORY-187)."""


@dataclass
class AuditReport:
    claims: list[dict]
    tier_results: list[TierResult]
    language_issues: list[str]
    integrity_score: float
    blocked_count: int


# The 3 source forms of a stated claim (STORY-204): a line of brief.md, a question to the person, a learned_knowledge key.
STATED_SOURCE = re.compile(r"^(brief\.md:\d+(-\d+)?|person:\S.*|learned_knowledge\.\S+)$")


class TruthTierValidator:
    def classify(self, claim: dict[str, Any]) -> TierResult:
        evidence = claim.get("evidence")

        if evidence is None:
            return TierResult(tier=TruthTier.SPECULATION, blocked=True, reason="No evidence provided")

        etype = evidence.get("type", "")

        if etype == "stated":  # the brief, an answer of the person, or learned_knowledge states it (STORY-204)
            if not STATED_SOURCE.match(str(evidence.get("source") or "").strip()):
                return TierResult(tier=TruthTier.SPECULATION, blocked=True, reason="Stated with no source")
            return TierResult(tier=TruthTier.SHIPPED, reason="stated")

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
        if not claims:
            raise NoClaims("no_claims: the audit holds 0 claims, so there is no integrity score")
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
        # An empty claim set has no score: audit() raises NoClaims above (STORY-187).
        # Language issues are advisory only — they appear in language_issues but do NOT reduce the score.
        score = (total - blocked) / total

        return AuditReport(
            claims=claims,
            tier_results=tier_results,
            language_issues=all_issues,
            integrity_score=round(score, 2),
            blocked_count=blocked,
        )


def band(score: float) -> str:
    """The band of an integrity score: "floor", "choice" or "pass"."""
    if score < INTEGRITY_FLOOR:
        return "floor"
    if score < INTEGRITY_TARGET:
        return "choice"
    return "pass"


def score_audit(data: Any) -> dict[str, Any]:
    """Add the 7 score keys to an audit document. Raise ValueError when the claims are not valid."""
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        raise ValueError("the audit must be an object with a list `claims`")
    for number, claim in enumerate(data["claims"]):
        if not isinstance(claim, dict) or not isinstance(claim.get("text"), str):
            raise ValueError(f"claims[{number}] must be an object with a string `text`")
        evidence = claim.get("evidence")
        if evidence is not None and not isinstance(evidence, dict):
            raise ValueError(f"claims[{number}].evidence must be an object or null")
    report = TruthTierValidator().audit(data["claims"])
    by_tier = {f"tier_{tier.value}": 0 for tier in TruthTier if tier is not TruthTier.SPECULATION}
    by_tier["tier_5_blocked"] = 0
    for result in report.tier_results:
        key = "tier_5_blocked" if result.blocked else f"tier_{result.tier.value}"
        by_tier[key] += 1
    name = band(report.integrity_score)
    data.update(
        integrity_score=report.integrity_score,
        total_claims=len(report.claims),
        tier5_blocked=report.blocked_count,
        by_tier=by_tier,
        floor_breached=name == "floor",
        band=name,
        scored_by="truth_tier_validator.py",
    )
    return data


def hold_path(root: Path, agent: str) -> Path:
    return root / ".gtm" / "audit" / f"{agent}-floor-hold.json"


def draft_hashes(root: Path, agent: str) -> dict[str, str | None]:
    """The sha256 of each draft of the agent, or None for a draft that is not a file."""
    out: dict[str, str | None] = {}
    for rel in AGENT_MANIFESTS[agent]:
        try:
            out[rel] = hashlib.sha256((root / rel).read_bytes()).hexdigest()
        except OSError:
            out[rel] = None
    return out


def content_flag(root: Path, agent: str) -> Any:
    """`completion_flags.<agent>` of gtm-context.json, or None when the file does not give it."""
    try:
        flags = json.loads((root / "gtm-context.json").read_text(encoding="utf-8"))["completion_flags"]
        return flags.get(agent)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def clear_content_flag(root: Path, agent: str) -> str:
    """Set `completion_flags.<agent>` to false. Returns what was done, for the kept file."""
    path = root / "gtm-context.json"
    try:
        context = json.loads(path.read_text(encoding="utf-8"))
        flags = context["completion_flags"]
        if agent not in flags:
            return f"not set: gtm-context.json has no completion_flags.{agent}"
        flags[agent] = False
        path.write_text(json.dumps(context, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError) as error:
        return f"not set: gtm-context.json: {error}"
    return "set to false"


def floor_reason(root: Path, agent: str) -> str | None:
    """Why the floor of an earlier audit still holds, or None when it does not (or there is none)."""
    path = hold_path(root, agent)
    if not path.is_file():
        return None
    try:
        kept = json.loads(path.read_text(encoding="utf-8"))
        audit, drafts = kept["audit"], kept["drafts"]
        score = audit["integrity_score"]
    except (OSError, ValueError, KeyError, TypeError):
        return f"{path} cannot be read, so the floor that it records holds"
    if content_flag(root, agent) is not True:
        why = f"{agent}-agent did not finish a new run after it (completion_flags.{agent} is not true)"
    elif draft_hashes(root, agent) == drafts:
        why = f"no draft of {agent} has changed after it"
    else:
        return None
    audit_path = root / ".gtm" / "audit" / f"{agent}-integrity.json"
    audit_path.write_text(json.dumps(dict(audit, floor_holds=why), indent=2) + "\n", encoding="utf-8")
    return f"the earlier audit gave integrity_score {score:.2f}, band floor, and {why}"


def keep_floor(root: Path, agent: str, data: dict[str, Any]) -> None:
    """Keep the scored floor audit and the draft hashes, and set the flag of the content agent to false."""
    kept = {"agent": agent, "audit": data, "drafts": draft_hashes(root, agent),
            "completion_flag": clear_content_flag(root, agent)}
    hold_path(root, agent).write_text(json.dumps(kept, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="truth_tier_validator.py", description="Score one integrity audit file.")
    parser.add_argument("--root", required=True, help="the project root")
    parser.add_argument("--agent", required=True, choices=INTEGRITY_AGENTS)
    args = parser.parse_args(argv)
    root = Path(args.root)
    path = root / ".gtm" / "audit" / f"{args.agent}-integrity.json"
    try:
        held = floor_reason(root, args.agent)
        if held is not None:
            print(f"{args.agent}: floor_holds: {held}. No new score.")
            return FLOOR_HOLDS
        data = score_audit(json.loads(path.read_text(encoding="utf-8")))
        if data["band"] == "floor":
            keep_floor(root, args.agent, data)
        else:
            hold_path(root, args.agent).unlink(missing_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except NoClaims as gap:
        print(f"truth_tier_validator.py: {path}: {gap}")
        return 3
    except (OSError, ValueError) as error:
        print(f"truth_tier_validator.py: {path}: {error}")
        return 2
    print(f"{args.agent}: integrity_score {data['integrity_score']:.2f}, band {data['band']} "
          f"({data['tier5_blocked']} of {data['total_claims']} claims blocked)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
