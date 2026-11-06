"""Predictability Architecture (PA) composition per spec §8.

Composes the customer-facing Predictability Architecture from a list of
selected pattern_ids. Quality floors derive from P12 / P12-Light, spending
caps from P9, pass-through triggers and model-version hedges from P15.

`customer_facing_summary_md` MUST pass the vocabulary linter at
`audience: customer-facing` (Charter §5.3) — the test
`test_pa_customer_summary_passes_vocabulary_linter` runs the linter
against the runtime output.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from pricing.lib.pattern_catalogue import PATTERNS


@dataclass
class QualityThresholds:
    floor_pct: float        # e.g. 0.90 — quality floor anchor (framework Chapter 4)
    escalation_pct: float   # e.g. 0.10 — escalation rate ceiling
    csat_min: float         # e.g. 4.0 — CSAT floor


@dataclass
class QualityFloor:
    pattern_id: str
    name: str
    floor_pct: float
    escalation_pct: float
    csat_min: float
    remedy: str
    has_gainshare: bool


@dataclass
class Cap:
    pattern_id: str
    name: str
    description: str


@dataclass
class Trigger:
    pattern_id: str
    name: str
    description: str


@dataclass
class Hedge:
    pattern_id: str
    name: str
    description: str


@dataclass
class PredictabilityArchitecture:
    quality_floors: list[QualityFloor] = field(default_factory=list)
    spending_caps: list[Cap] = field(default_factory=list)
    pass_through_triggers: list[Trigger] = field(default_factory=list)
    model_version_hedges: list[Hedge] = field(default_factory=list)
    customer_facing_summary_md: str = ""


_QUALITY_FLOOR_PATTERNS = {"P12", "P12-Light"}
_CAP_PATTERNS = {"P9"}
_TRIGGER_PATTERNS = {"P15"}
_HEDGE_PATTERNS = {"P15"}


def compose_pa(
    selected_patterns: list[str],
    arr_band: str,
    quality_thresholds: QualityThresholds,
) -> PredictabilityArchitecture:
    """Compose the customer-facing PA from selected pattern_ids."""
    # Validate patterns exist in the catalogue first.
    for pid in selected_patterns:
        if pid not in PATTERNS:
            raise ValueError(f"unknown pattern: {pid!r}")

    quality_floors: list[QualityFloor] = []
    spending_caps: list[Cap] = []
    pass_through_triggers: list[Trigger] = []
    model_version_hedges: list[Hedge] = []

    for pid in selected_patterns:
        pdef = PATTERNS[pid]
        if pid in _QUALITY_FLOOR_PATTERNS:
            has_gainshare = pid == "P12"
            quality_floors.append(QualityFloor(
                pattern_id=pid,
                name=pdef.name,
                floor_pct=quality_thresholds.floor_pct,
                escalation_pct=quality_thresholds.escalation_pct,
                csat_min=quality_thresholds.csat_min,
                remedy="service credits + fee reduction" + (" + outcome gainshare" if has_gainshare else ""),
                has_gainshare=has_gainshare,
            ))
        if pid in _CAP_PATTERNS:
            spending_caps.append(Cap(
                pattern_id=pid,
                name=pdef.name,
                description=(
                    f"Monthly hard ceiling — protects buyer from runaway usage cost. "
                    f"Triggered when monthly spending caps are reached; further usage requires "
                    f"explicit buyer approval. ARR band: {arr_band}."
                ),
            ))
        if pid in _TRIGGER_PATTERNS:
            pass_through_triggers.append(Trigger(
                pattern_id=pid,
                name=pdef.name,
                description=(
                    f"Cost pass-through trigger — preserves predictable AI cost when underlying "
                    f"provider unit prices change. Renewal-rate protection preserved. ARR band: {arr_band}."
                ),
            ))
        if pid in _HEDGE_PATTERNS:
            model_version_hedges.append(Hedge(
                pattern_id=pid,
                name="Model-version hedges",
                description=(
                    f"Model-version hedges — customer commitment to maintain service continuity "
                    f"across underlying model upgrades. Quality assurance maintained at the "
                    f"value floors above. ARR band: {arr_band}."
                ),
            ))

    summary = _render_customer_facing_summary(
        quality_floors, spending_caps, pass_through_triggers, model_version_hedges,
    )

    return PredictabilityArchitecture(
        quality_floors=quality_floors,
        spending_caps=spending_caps,
        pass_through_triggers=pass_through_triggers,
        model_version_hedges=model_version_hedges,
        customer_facing_summary_md=summary,
    )


def _render_customer_facing_summary(
    floors: list[QualityFloor],
    caps: list[Cap],
    triggers: list[Trigger],
    hedges: list[Hedge],
) -> str:
    """Render the customer-facing prose. MUST use customer-facing vocabulary only.

    Allowed terms (vocabulary.yaml customer_facing): predictable AI cost, hard
    ceilings, spending caps, value floors, quality floors, quality assurance,
    forecastable cost, renewal-rate protection, model-version hedges.

    Forbidden terms (vocabulary.yaml internal_only): cost-coverage equilibrium,
    vendor margin, GM compression, margin collapse, amplifier multiplier,
    shared risk, cost-coverage trap, effective cost per outcome.
    """
    lines = ["## Predictability Architecture", ""]
    lines.append(
        "This portion of the agreement commits the partnership to a predictable AI cost "
        "envelope and durable quality assurance. The four protections below define how "
        "the partnership preserves forecastable cost and renewal-rate protection across "
        "the contract term."
    )
    lines.append("")

    if floors:
        lines.append("### Quality floors")
        for qf in floors:
            gainshare = " plus outcome gainshare" if qf.has_gainshare else ""
            lines.append(
                f"- **{qf.name}** — value floors maintained at {qf.floor_pct:.0f}% successful "
                f"outcomes with escalation ceiling at {qf.escalation_pct:.0f}% and CSAT floor "
                f"at {qf.csat_min:.1f}. Remedy: {qf.remedy}{gainshare}."
            )
        lines.append("")

    if caps:
        lines.append("### Spending caps (hard ceilings)")
        for c in caps:
            lines.append(f"- **{c.name}** — {c.description}")
        lines.append("")

    if triggers:
        lines.append("### Pass-through triggers")
        for t in triggers:
            lines.append(f"- **{t.name}** — {t.description}")
        lines.append("")

    if hedges:
        lines.append("### Model-version hedges")
        for h in hedges:
            lines.append(f"- **{h.name}** — {h.description}")
        lines.append("")

    if not (floors or caps or triggers or hedges):
        lines.append(
            "_No protections selected for this contract. Default PA composition is "
            "recommended for portcos with unbounded agentic surfaces._"
        )

    return "\n".join(lines)
