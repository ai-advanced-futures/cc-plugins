"""S1-S5 sensitivity-matrix stress test per spec §6.

Implements framework Table §3.3's 5-scenario sensitivity matrix.

- S1 base: cost_baseline × composite.p75
- S2 inference +50%: (cost_baseline × 1.5) × composite.p75
- S3 volume +200%: cost_baseline × (composite.p75 × 1.2)  # modest amp uplift proxy
- S4 loop 3x: cost_baseline × (composite.p75 × 3)
- S5 combined: (cost_baseline × 1.5) × (composite.p75 × 1.2 × 3)

S4 narrative differs when amp #1 (loop overhead) is absent from the
composite vs present: present → canonical "loop-overhead-3x stress";
absent → "fallback: tripling composite P75 since amp #1 not flagged".
Both branches use the same arithmetic (composite.p75 × 3) because the
public API receives the composite only — not the per-amp readings. A
future v1.4.1 may extend the API to accept readings and implement the
true canonical path that recomposes with amp #1's multiplier tripled.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pricing.lib.amplifier_composer import AmplifierCompositeResult

PricingUnit = Literal[
    "per_seat", "per_outcome", "per_task", "per_resolution",
    "per_deliverable", "per_run", "per_acu",
]


@dataclass
class PricingModelInput:
    archetype: str
    headline_price: float
    pricing_unit: PricingUnit
    cost_per_interaction_baseline: float  # from cost_taxonomy / framework Table


@dataclass
class S1S5Result:
    s1_base_margin_pct: float
    s2_inference_50_margin_pct: float
    s3_volume_200_margin_pct: float
    s4_loop_3x_margin_pct: float
    s5_combined_margin_pct: float
    narrative_md_per_scenario: dict[str, str] = field(default_factory=dict)


_KNOWN_ARCHETYPES = frozenset({
    "support_agent",
    "developer_tool",
    "vertical_pro_services_agent",
    "sales_marketing_agent",
    "knowledge_horizontal_copilot",
    "autonomous_workflow_agent",
})

_S2_INFERENCE_COST_FACTOR = 1.5
_S3_VOLUME_AMP_UPLIFT = 1.2
_S4_LOOP_OVERHEAD_MULTIPLIER = 3.0


def _margin_pct(price: float, cost: float, amp: float) -> float:
    """Return effective margin % for given (price, baseline_cost, amp_multiplier)."""
    if price <= 0:
        return 0.0
    effective_cost = cost * amp
    return (price - effective_cost) / price * 100.0


def compute_sensitivity(
    archetype: str,
    pricing_model: PricingModelInput,
    composite_amplifier: AmplifierCompositeResult,
) -> S1S5Result:
    """Compute the S1-S5 stress matrix for a given pricing model + amplifier composite."""
    if archetype not in _KNOWN_ARCHETYPES:
        raise ValueError(f"unknown archetype: {archetype!r}")

    price = pricing_model.headline_price
    cost = pricing_model.cost_per_interaction_baseline
    base_amp = composite_amplifier.p75

    s1 = _margin_pct(price, cost, base_amp)
    s2 = _margin_pct(price, cost * _S2_INFERENCE_COST_FACTOR, base_amp)
    s3 = _margin_pct(price, cost, base_amp * _S3_VOLUME_AMP_UPLIFT)
    s4 = _margin_pct(price, cost, base_amp * _S4_LOOP_OVERHEAD_MULTIPLIER)
    s5 = _margin_pct(
        price,
        cost * _S2_INFERENCE_COST_FACTOR,
        base_amp * _S3_VOLUME_AMP_UPLIFT * _S4_LOOP_OVERHEAD_MULTIPLIER,
    )

    amp1_present = 1 in composite_amplifier.present_amplifiers
    if amp1_present:
        s4_narrative = (
            f"S4 (loop overhead 3x): canonical path — amplifier #1 (planner re-run / "
            f"loop overhead) is present in the composite. Stress proxy multiplies the "
            f"composite P75 by 3 (effective_amp = {base_amp * _S4_LOOP_OVERHEAD_MULTIPLIER:.2f}x). "
            f"Effective margin = {s4:.1f}%."
        )
    else:
        s4_narrative = (
            f"S4 (loop overhead 3x): fallback path — amplifier #1 is absent from the "
            f"composite. Stress is applied directly to the composite P75 instead of "
            f"amplifier #1's multiplier_p75 (effective_amp = "
            f"{base_amp * _S4_LOOP_OVERHEAD_MULTIPLIER:.2f}x). Effective margin = {s4:.1f}%."
        )

    narrative = {
        "s1": (
            f"S1 (base case): composite P75 amplifier = {base_amp:.2f}x applied to "
            f"baseline cost ${cost:.4f}. Effective cost-per-interaction = "
            f"${cost * base_amp:.4f}. Effective margin = {s1:.1f}%."
        ),
        "s2": (
            f"S2 (inference +50%): baseline cost lifted to ${cost * _S2_INFERENCE_COST_FACTOR:.4f}. "
            f"Composite amplifier unchanged at {base_amp:.2f}x. Effective margin = {s2:.1f}%."
        ),
        "s3": (
            f"S3 (volume +200%): amplifier uplift to {base_amp * _S3_VOLUME_AMP_UPLIFT:.2f}x "
            f"as a +20% loop-pressure proxy from volume growth. Baseline cost unchanged. "
            f"Effective margin = {s3:.1f}%."
        ),
        "s4": s4_narrative,
        "s5": (
            f"S5 (combined S2+S3+S4): inference +50%, volume amp uplift +20%, loop 3x "
            f"stress. Effective amplifier = {base_amp * _S3_VOLUME_AMP_UPLIFT * _S4_LOOP_OVERHEAD_MULTIPLIER:.2f}x "
            f"on cost ${cost * _S2_INFERENCE_COST_FACTOR:.4f}. Effective margin = {s5:.1f}%."
        ),
    }

    return S1S5Result(
        s1_base_margin_pct=s1,
        s2_inference_50_margin_pct=s2,
        s3_volume_200_margin_pct=s3,
        s4_loop_3x_margin_pct=s4,
        s5_combined_margin_pct=s5,
        narrative_md_per_scenario=narrative,
    )
