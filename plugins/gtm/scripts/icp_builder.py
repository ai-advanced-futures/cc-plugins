from __future__ import annotations

# Role psychographic profiles — canonical source for ICP builder.
# Agent docs that reference these: agents/orchestrator.md Step 4 (profiling),
# agents/marketing-agent.md Step 2 (Kotler STP).
# Extend this list when adding new buyer roles; do NOT duplicate in agent markdown.
ROLE_PSYCHOGRAPHICS: dict[str, dict[str, str]] = {
    "cto": {
        "buyer_mindset": "build-vs-buy evaluator",
        "risk_tolerance": "low",
        "decision_style": "technical proof required",
    },
    "cio": {
        "buyer_mindset": "compliance-first",
        "risk_tolerance": "very low",
        "decision_style": "vendor risk assessment",
    },
    "cmo": {
        "buyer_mindset": "growth-focused",
        "risk_tolerance": "medium-high",
        "decision_style": "channel and attribution driven",
    },
    "vp marketing": {
        "buyer_mindset": "growth-focused",
        "risk_tolerance": "medium",
        "decision_style": "ROI and attribution driven",
    },
    "head of marketing": {
        "buyer_mindset": "growth-focused",
        "risk_tolerance": "medium",
        "decision_style": "ROI and attribution driven",
    },
    "vp sales": {
        "buyer_mindset": "quota-focused",
        "risk_tolerance": "medium",
        "decision_style": "pipeline impact driven",
    },
    "cfo": {
        "buyer_mindset": "cost-control",
        "risk_tolerance": "low",
        "decision_style": "payback period and TCO",
    },
}

_DEFAULT_PSYCHOGRAPHIC: dict[str, str] = {
    "buyer_mindset": "value-driven",
    "risk_tolerance": "medium",
    "decision_style": "data-informed",
}


class ICPBuilder:
    def build(
        self,
        industry: str,
        company_size: str,
        role: str,
        pain_points: list[str],
        success_metrics: list[str],
        geographies: list[str] | None = None,
    ) -> dict:
        return {
            "industry": industry,
            "role": role,
            "pain_points": pain_points,
            "success_metrics": success_metrics,
            "firmographic": {
                "company_size": company_size,
                "industries": [industry],
                "geographies": geographies or ["global"],
            },
            "psychographic": ROLE_PSYCHOGRAPHICS.get(role.lower().strip(), _DEFAULT_PSYCHOGRAPHIC),
            "trigger_events": [],
            "disqualifiers": [],
        }


class PersonaGenerator:
    def generate(self, icp: dict, name: str) -> dict:
        return {
            "name": name,
            "role": icp.get("role", ""),
            "industry": icp.get("industry", ""),
            "company_size": icp.get("firmographic", {}).get("company_size", ""),
            "pain_points": icp.get("pain_points", []),
            "success_metrics": icp.get("success_metrics", []) if "success_metrics" in icp else [],
            "goals": [],
            "objections": [],
            "preferred_channels": [],
            "buyer_journey": {
                "awareness": "learns via peer networks and content",
                "consideration": "evaluates via trials and demos",
                "decision": "requires ROI proof and exec alignment",
            },
        }
