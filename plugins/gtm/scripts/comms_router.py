"""Auto-comms router: maps p15-trigger-event events -> comms template set.

Schema-coupled federation — gtm reads the p15-trigger-event.json artifact and
maps trigger_kind to templates. Severity is INFORMATIONAL ONLY (surfaced inside
the rendered draft, never gates which templates are produced). NO cross-plugin
import. See ADR-003.
"""
from __future__ import annotations

_KIND_TO_TEMPLATES = {
    "quality_floor_breach": {"05-customer-announcement.md", "06-internal-faq.md"},
    "cost_rate_breach": {"02-cfo.md", "01-board.md"},
}


def select_templates(events: list[dict]) -> set[str]:
    """Return the deduplicated union of template files for the given events.

    Empty events -> empty set (no-op). Severity is ignored for selection.
    """
    selected: set[str] = set()
    for ev in events:
        selected |= _KIND_TO_TEMPLATES.get(ev.get("trigger_kind"), set())
    return selected
