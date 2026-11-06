from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

AGENT_ORDER = ["brand", "marketing", "sales", "funnel"]


def consolidate_audits(audit_dir: str) -> dict:
    base = Path(audit_dir)
    agent_audits: list[dict] = []

    for agent in AGENT_ORDER:
        audit_file = base / f"{agent}-integrity.json"
        if not audit_file.exists():
            raise FileNotFoundError(
                f"Missing audit file for '{agent}': {audit_file}"
            )
        agent_audits.append(json.loads(audit_file.read_text()))

    scores = {a["agent"]: a["integrity_score"] for a in agent_audits}
    overall = round(sum(scores.values()) / len(scores), 3)
    total_claims = sum(a["total_claims"] for a in agent_audits)
    total_blocked = sum(a["tier5_blocked"] for a in agent_audits)

    all_issues = []
    for audit in agent_audits:
        for issue in audit.get("issues", []):
            all_issues.append({**issue, "source_agent": audit["agent"]})

    return {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "agents_audited": AGENT_ORDER,
        "integrity_scores": scores,
        "overall_score": overall,
        "total_claims_across_all_agents": total_claims,
        "total_tier5_blocked": total_blocked,
        "issues": all_issues,
    }
