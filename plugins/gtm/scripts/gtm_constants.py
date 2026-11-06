from __future__ import annotations

# Single source of truth for all GTM agent name lists.
# Import from here — never redefine these lists in other modules.

# Agents that produce working artifacts (have .gtm/working/{agent}/ directories)
CONTENT_AGENTS: list[str] = ["brand", "marketing", "sales", "funnel"]

# All agents that receive completion flags (superset of CONTENT_AGENTS)
ALL_AGENTS: list[str] = ["knowledge", "codebase_scanner", "brand", "marketing", "sales", "funnel"]

# Agents that receive integrity audit passes
INTEGRITY_AGENTS: list[str] = ["brand", "marketing", "sales", "funnel"]

# All flag names (content + integrity passes)
ALL_FLAGS: list[str] = ALL_AGENTS + [f"{a}_integrity" for a in INTEGRITY_AGENTS]

# Integrity score thresholds (authoritative — matches definitions/integrity-score.md)
INTEGRITY_FLOOR: float = 0.60    # Below this: floor_breached = true, do NOT write to gtm-output/
INTEGRITY_TARGET: float = 0.85   # Target for acceptable artifact quality
