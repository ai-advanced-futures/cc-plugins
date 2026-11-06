"""Bounded-product safety check — ADR-006 (pricing-side); absorbs PR #107 ADR-004 upstream logic.

Pure function module. No agent state. Spec §4.1, §4.2, §4.2.1, §4.2.2.

The matrix populates the `bounded_vs_unbounded` field on
`agentic-pricing-diagnosis.schema.json` (Charter v1.0.0 field — no schema change).
Caller (agentic-pricing-strategist agent) classifies natural-language product
description into one of 4 exception classes (judgment, LLM-natured), then calls
apply_matrix() with the (class, ratio) tuple for deterministic determination.

See ADR-006 (plugins/pricing/docs/adr/ADR-006-bounded-product-safety-check.md) for
the architectural rationale for this module's design choices (frozen SafetyCheckResult,
separate BOUNDED_CLASSES tuple, named threshold constants).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BoundedClass = Literal[
    "perplexity-class",
    "notion-ai-core",
    "harvey-hebbia-evenup",
    "replit-narrow-vertical",
]

Determination = Literal["bounded", "unbounded", "ambiguous"]


# frozen: SafetyCheckResult is an immutable value object — apply_matrix is a pure
# function and callers must not mutate the result (the agent reconciles via the
# diagnosis artifact, not by mutating this). Divergence from pricing's other
# result dataclasses (bare @dataclass) is deliberate. See ADR-006 §3.
@dataclass(frozen=True)
class SafetyCheckResult:
    determination: Determination
    reason: str               # for value_metric_rationale; static templates kept ≤500 chars (verified by test_reason_non_empty_and_under_500_chars)
    matched_row: int          # 1-5, which matrix row triggered (observable for tests)
    class_match: BoundedClass | None
    cost_ratio_observed: float | None


# Runtime membership set for the apply_matrix guard. MUST stay in sync with the
# BoundedClass Literal above — test_bounded_classes_matches_literal_args enforces this.
BOUNDED_CLASSES: tuple[BoundedClass, ...] = (
    "perplexity-class",
    "notion-ai-core",
    "harvey-hebbia-evenup",
    "replit-narrow-vertical",
)

# Matrix thresholds (spec §4.2). Recalibration requires updating these + ADR-006.
_ROW1_UPPER_BOUND = 5.0    # ratio ≤ this with class match → bounded (row 1)
_ROW5_LOWER_BOUND = 20.0   # ratio ≥ this with class match → unbounded ratio-override (row 5)


def apply_matrix(
    class_match: BoundedClass | None,
    cost_ratio_observed: float | None,
) -> SafetyCheckResult:
    """ADR-006 / PR #107 ADR-004 5-row override matrix. Pure function, no agent state.

    Thresholds: _ROW1_UPPER_BOUND (≤5.0 → bounded), _ROW5_LOWER_BOUND (≥20.0 → unbounded
    ratio-override). See spec §4.2 and ADR-006 for recalibration protocol.

    Raises:
        ValueError: if class_match is not in BOUNDED_CLASSES and is not None
                    (runtime guard — Literal hints don't enforce at runtime).
        ValueError: if cost_ratio_observed is not None and < 0.0
                    (P95 ≥ P75 invariant; negative ratio is a programming error).
    """
    # Runtime guards (spec §4.1 Raises)
    if class_match is not None and class_match not in BOUNDED_CLASSES:
        raise ValueError(
            f"class_match={class_match!r} not in BOUNDED_CLASSES={BOUNDED_CLASSES}; "
            "must be one of the 4 framework-defined slugs or None"
        )
    if cost_ratio_observed is not None and cost_ratio_observed < 0.0:
        raise ValueError(
            f"cost_ratio_observed={cost_ratio_observed} must be ≥ 0 "
            "(P95 ≥ P75 invariant; negative ratio is a programming error)"
        )

    # Coerce to float for consistent template rendering (spec §4.2.1 contract)
    cost_ratio_observed = (
        float(cost_ratio_observed) if cost_ratio_observed is not None else None
    )

    # Row 4 early-return guard: class_match is None → unbounded (no ratio descriptor in reason)
    # Precedence: row 4 fires before row 5 when class_match is None (spec §4.2 precedence note)
    if class_match is None:
        return SafetyCheckResult(
            determination="unbounded",
            reason="Unbounded: no bounded-class match for product description — matrix row 4 match",
            matched_row=4,
            class_match=None,
            cost_ratio_observed=cost_ratio_observed,
        )

    # Row 3 early-return guard: class match present + ratio is None → unbounded (instrumentation gap)
    if cost_ratio_observed is None:
        return SafetyCheckResult(
            determination="unbounded",
            reason=(
                f"Unbounded: class={class_match} matched but cost ratio is unmeasured — "
                "instrumentation gap is itself a finding (PR #107 ADR-004 row 3); matrix row 3 match"
            ),
            matched_row=3,
            class_match=class_match,
            cost_ratio_observed=None,
        )

    # Row 5: class match + ratio ≥ _ROW5_LOWER_BOUND → unbounded (ratio override; "ratio is source of truth")
    if cost_ratio_observed >= _ROW5_LOWER_BOUND:
        return SafetyCheckResult(
            determination="unbounded",
            reason=(
                f"Unbounded: cost_ratio={cost_ratio_observed}x ≥ 20.0 overrides "
                f"class={class_match} match — matrix row 5 "
                "(PR #107 ADR-004 'ratio is source of truth' rule)"
            ),
            matched_row=5,
            class_match=class_match,
            cost_ratio_observed=cost_ratio_observed,
        )

    # Row 1: class match + ratio ≤ _ROW1_UPPER_BOUND → bounded confirmed
    if cost_ratio_observed <= _ROW1_UPPER_BOUND:
        return SafetyCheckResult(
            determination="bounded",
            reason=(
                f"Bounded confirmed: class={class_match}, "
                f"cost_ratio={cost_ratio_observed}x ≤ 5.0 — "
                "matrix row 1 match (PR #107 ADR-004 §A.1)"
            ),
            matched_row=1,
            class_match=class_match,
            cost_ratio_observed=cost_ratio_observed,
        )

    # Row 2: class match + 5.0 < ratio < 20.0 → ambiguous (likely product creep)
    return SafetyCheckResult(
        determination="ambiguous",
        reason=(
            f"Ambiguous: class={class_match} matched but cost_ratio={cost_ratio_observed}x "
            "suggests product creep beyond original bounded surface — "
            "matrix row 2; agent must reconcile via AskUserQuestion"
        ),
        matched_row=2,
        class_match=class_match,
        cost_ratio_observed=cost_ratio_observed,
    )
