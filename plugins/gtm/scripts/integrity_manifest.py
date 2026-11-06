from __future__ import annotations

from pathlib import Path

AGENT_MANIFESTS: dict[str, list[str]] = {
    "brand": [
        ".gtm/working/brand/brand-identity.draft.json",
        ".gtm/working/brand/messaging-architecture.draft.json",
        ".gtm/working/brand/voice-guide.draft.md",
        ".gtm/working/brand/purpose-statement.draft.md",
        ".gtm/working/brand/storybrand-script.draft.md",
    ],
    "marketing": [
        ".gtm/working/marketing/campaign-plan.draft.json",
        ".gtm/working/marketing/launch-plan.draft.json",
        ".gtm/working/marketing/content-calendar.draft.md",
    ],
    "sales": [
        ".gtm/working/sales/pitch-deck.draft.json",
        ".gtm/working/sales/pitch-narrative.draft.md",
        ".gtm/working/sales/prospecting-plan.draft.json",
        ".gtm/working/sales/pipeline-playbook.draft.json",
        ".gtm/working/sales/discovery-questions.draft.md",
        ".gtm/working/sales/meddpicc-scorecard.draft.md",
    ],
    "funnel": [
        ".gtm/working/funnel/funnel-metrics.draft.json",
        ".gtm/working/funnel/funnel-health.draft.md",
        ".gtm/working/funnel/handoff-sla.draft.md",
        ".gtm/working/funnel/revenue-math.draft.md",
    ],
}


def get_draft_paths(target_agent: str) -> list[str]:
    if target_agent not in AGENT_MANIFESTS:
        raise ValueError(
            f"Unknown target_agent: '{target_agent}'. Must be one of: {list(AGENT_MANIFESTS.keys())}"
        )
    return list(AGENT_MANIFESTS[target_agent])


def get_output_path(draft_path: str) -> str:
    filename = Path(draft_path).name          # e.g. brand-identity.draft.json
    clean_name = filename.replace(".draft.", ".")  # brand-identity.json
    return f"gtm-output/{clean_name}"
