"""Value-metric decision tree — 6 archetype → 8 terminal nodes.

Per spec §5 + ADR-004 (terminal-node → pattern-bundle mapping).
Charter §4.1-§4.6 source.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pricing.lib.charter_exports import canonical_terminal_node

SuccessMode = Literal["volume", "outcome", "productivity", "net_new", "dev_output"]
ArrBand = Literal["<50M", "50-100M", "100-200M", "200-500M", ">500M"]
Bounded = Literal["bounded", "unbounded"]
Confidence = Literal["low", "medium", "high"]


@dataclass
class TreeAnswers:
    success_mode: SuccessMode
    branch_diagnostic: bool  # YES/NO answer for the success_mode's branch
    bounded_vs_unbounded: Bounded
    portco_arr_band: ArrBand


@dataclass
class TerminalNodeResult:
    terminal_node: str  # canonical 8-set
    archetype: str
    layer_classification: str
    recommended_pattern_ids: list[str]
    confidence: Confidence


# Branch routing table per Charter §4.2.
# Each (success_mode, branch_diagnostic) → raw terminal label (may be D.2 alias).
_BRANCH_ROUTES: dict[tuple[SuccessMode, bool], str] = {
    ("volume", True): "A.2",
    ("volume", False): "A.3",
    ("outcome", True): "B.2",
    ("outcome", False): "B.3",
    ("productivity", True): "C.2",
    ("productivity", False): "C.3",
    ("net_new", True): "D.2",  # alias for B.2 — canonical_terminal_node resolves
    ("net_new", False): "D.2",  # framework collapses D.2/B.2; conservative routing
    ("dev_output", True): "E.2",
    ("dev_output", False): "E.3",
}


# Archetype mapping per Charter §4 + framework Table §1.4 (Five Vendor Pattern Archetypes).
_TERMINAL_TO_ARCHETYPE: dict[str, str] = {
    "A.2": "support_agent",
    "A.3": "support_agent",
    "B.2": "autonomous_workflow_agent",
    "B.3": "sales_marketing_agent",
    "C.2": "vertical_pro_services_agent",
    "C.3": "knowledge_horizontal_copilot",
    "E.2": "developer_tool",
    "E.3": "developer_tool",
}


# Terminal-node → pattern-bundle mapping per ADR-004.
# Each terminal pinned to a default bundle. Engineer may override via spec §5.1.
_TERMINAL_TO_PATTERNS: dict[str, tuple[str, ...]] = {
    "A.2": ("P4", "P9", "P15"),         # Hybrid seat+meter + budget + pass-through
    "A.3": ("P3", "P9", "P15"),         # Per-resolution + budget + pass-through
    "B.2": ("P12-Light", "P9", "P15"),  # Outcome+Quality + budget + pass-through
    "B.3": ("P4", "P9", "P15"),         # Hybrid + budget + pass-through (attribution dispute)
    "C.2": ("P1", "P9", "P15"),         # Per-seat unlimited (vertical anchor) + budget + pass-through
    "C.3": ("P4", "P9", "P15"),         # Hybrid + budget + pass-through
    "E.2": ("P4", "P9", "P15"),         # Tiered hybrid + cap + pass-through
    "E.3": ("P2", "P9", "P15"),         # Per-task/ACU + cap + pass-through
}


# Archetype-expected bounded/unbounded shape per framework §3.2.
# Confidence falls to "medium" when the portco's bounded_vs_unbounded answer
# diverges from the archetype's structural expectation.
_ARCHETYPE_BOUNDED_EXPECTED: dict[str, Bounded] = {
    "support_agent": "unbounded",
    "autonomous_workflow_agent": "unbounded",
    "vertical_pro_services_agent": "bounded",
    "knowledge_horizontal_copilot": "bounded",
    "developer_tool": "unbounded",
    "sales_marketing_agent": "unbounded",
}


def walk_tree(answers: TreeAnswers) -> TerminalNodeResult:
    """Walk the decision tree from answers to terminal node + recommendations."""
    key = (answers.success_mode, answers.branch_diagnostic)
    if key not in _BRANCH_ROUTES:
        raise ValueError(f"unknown success_mode: {answers.success_mode!r}")

    raw_terminal = _BRANCH_ROUTES[key]
    canonical = canonical_terminal_node(raw_terminal)
    archetype = _TERMINAL_TO_ARCHETYPE[canonical]
    patterns = list(_TERMINAL_TO_PATTERNS[canonical])

    # Layer classification: bounded → can stay application-layer; unbounded → application with full PA
    layer = "application"  # All in-scope JustKeenAI archetypes are app-layer
    if archetype == "vertical_pro_services_agent":
        layer = "vertical_labor_anchor"

    confidence: Confidence = (
        "high"
        if _ARCHETYPE_BOUNDED_EXPECTED.get(archetype) == answers.bounded_vs_unbounded
        else "medium"
    )

    return TerminalNodeResult(
        terminal_node=canonical,
        archetype=archetype,
        layer_classification=layer,
        recommended_pattern_ids=patterns,
        confidence=confidence,
    )
