"""Deterministic vendor-archetype classifier.

Pure, no I/O. Maps a 7-bool VendorPricingSignals vector to one of the framework's
five canonical vendor archetypes (JustKeenAI v2.1 Chapter 1 "Five vendor archetypes
in market today", collapsed to 5 + a seat_anchor discriminator). First-match-wins
precedence; returns an `unclassified` sentinel (never raises) when no rule matches.

Precedence note (ADR-002): a vendor with has_outcome_metric=True AND NOT
has_platform_fee_floor fires Rule 3 (pure_outcome_absorbed) even if it ALSO carries
seat+meter signals — outcome metrics are architecturally dominant in the framework,
so Rules 2-3 intentionally precede Rules 4-5. No wave-1 vendor hits this overlap.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass

# best_in_class_pattern per archetype, anchored to the framework's Chapter-2 terminal
# pattern definitions (NOT the editorial Chapter-1 table prose). See ADR-002: for
# pure_outcome_absorbed, A.3 is cited as the best-in-class UPGRADE TARGET (add a
# platform floor), not a descriptor of the archetype itself.
BEST_IN_CLASS_PATTERN = {
    "pure_outcome_absorbed": "Pure per-resolution at Intercom scale; best-in-class upgrade = add platform floor → A.3",
    "hybrid_platform_outcome": "Per-outcome + quality SLA + tier floor (B.2) with six-figure platform fee",
    "pure_per_seat": "Per-seat unlimited / per-case flat, labor-anchored (C.2) — or bounded-surface flat per-seat",
    "hybrid_seat_meter": "Hybrid seat + meter with Lite/Pro split (C.3/A.2) — Writer-class",
    "pure_passthrough": "Tiered hybrid + mandatory spend cap (E.2/E.3)",
}


@dataclass(frozen=True)
class VendorPricingSignals:
    """The validated 7-bool signal vector the classifier consumes."""
    has_outcome_metric: bool
    has_platform_fee_floor: bool
    has_seat_price: bool
    has_usage_meter: bool
    passthrough_dominant: bool
    labor_anchored: bool
    bounded_agent_surface: bool


@dataclass(frozen=True)
class ClassificationResult:
    archetype: str          # one of the 5, or "unclassified"
    seat_anchor: str | None  # "vertical_anchor" | "bounded_surface" | None
    best_in_class_pattern: str | None
    reason: str
    is_classified: bool


def _result(archetype: str, seat_anchor: str | None = None) -> ClassificationResult:
    return ClassificationResult(
        archetype=archetype,
        seat_anchor=seat_anchor,
        best_in_class_pattern=BEST_IN_CLASS_PATTERN[archetype],
        reason="",
        is_classified=True,
    )


def _unclassified(reason: str) -> ClassificationResult:
    return ClassificationResult(
        archetype="unclassified",
        seat_anchor=None,
        best_in_class_pattern=None,
        reason=reason,
        is_classified=False,
    )


def classify(signals: VendorPricingSignals) -> ClassificationResult:
    """First-match-wins classification. Never raises."""
    if signals.passthrough_dominant:
        return _result("pure_passthrough")
    if signals.has_outcome_metric and signals.has_platform_fee_floor:
        return _result("hybrid_platform_outcome")
    if signals.has_outcome_metric and not signals.has_platform_fee_floor:
        return _result("pure_outcome_absorbed")
    if signals.has_seat_price and signals.has_usage_meter:
        return _result("hybrid_seat_meter")
    if signals.has_seat_price and not signals.has_usage_meter:
        if signals.labor_anchored:
            return _result("pure_per_seat", "vertical_anchor")
        if signals.bounded_agent_surface:
            return _result("pure_per_seat", "bounded_surface")
        return _unclassified("per-seat without anchor signal")
    return _unclassified("no rule matched")


def _signals_from_dict(d: dict) -> VendorPricingSignals:
    """Build VendorPricingSignals from a raw (already schema-validated) signals dict.

    Lives in the classifier (NOT the loader) so classify_registry stays free of any
    loader/I/O dependency and classify() remains pure. Registry data is validated
    against the federation schema before reaching here. Field names are derived from
    VendorPricingSignals itself — no parallel tuple required.
    """
    keys = (f.name for f in dataclasses.fields(VendorPricingSignals))
    return VendorPricingSignals(**{k: bool(d[k]) for k in keys})


def classify_registry(registry: list[dict]) -> list[dict]:
    """Re-classify each registry entry's signals; return drift records.

    Returns a list of {vendor, expected, got} for every vendor whose re-classified
    (archetype, seat_anchor) != its recorded (archetype, seat_anchor). Empty list ==
    zero drift (the registry is internally consistent with the classifier rules).
    """
    drift = []
    for entry in registry:
        recorded = (entry["archetype"], entry.get("seat_anchor"))
        result = classify(_signals_from_dict(entry["signals"]))
        got = (result.archetype, result.seat_anchor)
        if got != recorded:
            drift.append({"vendor": entry["vendor_name"], "expected": recorded, "got": got})
    return drift
