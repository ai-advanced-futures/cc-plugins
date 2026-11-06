"""Per-archetype P50/P95 effective cost per interaction.

Per spec §11 + ADR-005 (inferred archetype cost data). Framework Table §3.1
provides data for 3 archetypes (support, developer-tool, vertical pro-services).
The other 3 archetypes (sales-marketing, knowledge-horizontal-copilot,
autonomous-workflow) use inferred defaults — refinement deferred to v1.4.1
when aiml sub-spec ships telemetry-enriched data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pricing.lib.amplifier_composer import AmplifierCompositeResult

DataSource = Literal["framework_table", "inferred_v1_4_0", "telemetry_v1_4_1"]


@dataclass
class EffectiveCostResult:
    median_effective_per_interaction: float
    p95_effective_per_interaction: float
    margin_at_headline_p95_pct: float
    data_source: DataSource  # provenance per ADR-005


# Baseline cost-per-interaction by archetype (in USD).
# Framework Table §3.1 sourced; inferred values flagged.
_BASELINE_COST: dict[str, tuple[float, DataSource]] = {
    "support_agent": (0.20, "framework_table"),               # ~$0.20 base inference per resolution
    "developer_tool": (0.10, "framework_table"),              # ~$0.10 per task base
    "vertical_pro_services_agent": (5.00, "framework_table"), # ~$5.00 per deliverable base
    "sales_marketing_agent": (0.50, "inferred_v1_4_0"),       # Inferred mid-cost workflow
    "knowledge_horizontal_copilot": (0.30, "inferred_v1_4_0"),# Inferred bounded surface
    "autonomous_workflow_agent": (2.00, "inferred_v1_4_0"),   # Inferred high-cost workflow
}


# Strict telemetry-override allowlist: exactly the archetypes whose baseline is
# currently `inferred_v1_4_0` may be overridden by an archetype-baseline-telemetry
# artifact (§7.13). framework_table archetypes stay framework-authoritative.
# DERIVED from _BASELINE_COST (single source of truth) so the set cannot drift from
# the provenance tags — "telemetry may override exactly the inferred baselines".
# (pricing ADR-005 amendment, sub-spec 4c; /simplify-derived per the lockstep test.)
_TELEMETRY_OVERRIDABLE = frozenset(
    archetype for archetype, (_baseline, data_source) in _BASELINE_COST.items()
    if data_source == "inferred_v1_4_0"
)


def effective_cost(
    archetype: str,
    headline_price: float,
    amplifier_composite: AmplifierCompositeResult,
    telemetry_baselines: "dict[str, object] | None" = None,
) -> EffectiveCostResult:
    """Compute effective cost per interaction at P50 and P95 amplification.

    When `telemetry_baselines` carries the archetype AND the archetype is in the
    strict `_TELEMETRY_OVERRIDABLE` set, the telemetry-derived baseline replaces
    the table baseline and data_source flips to `telemetry_v1_4_1`. A telemetry
    entry for a framework_table archetype is IGNORED (not an error). Absent
    telemetry → existing _BASELINE_COST lookup (graceful fallback).
    """
    if archetype not in _BASELINE_COST:
        raise ValueError(f"unknown archetype: {archetype!r}")

    baseline, data_source = _BASELINE_COST[archetype]
    if telemetry_baselines and archetype in _TELEMETRY_OVERRIDABLE and archetype in telemetry_baselines:
        baseline = telemetry_baselines[archetype].baseline_cost_per_interaction
        data_source = "telemetry_v1_4_1"

    median_effective = baseline * amplifier_composite.p50
    p95_effective = baseline * amplifier_composite.p95
    margin_at_p95 = (headline_price - p95_effective) / headline_price * 100.0 if headline_price > 0 else 0.0

    return EffectiveCostResult(
        median_effective_per_interaction=median_effective,
        p95_effective_per_interaction=p95_effective,
        margin_at_headline_p95_pct=margin_at_p95,
        data_source=data_source,
    )
