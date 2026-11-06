"""Pure deterministic cost-class band classifier.

No I/O, no pricing.lib import. Thresholds are ADR-010-pinned named constants.
The cost-class band is a pure function of the consumed cost-amplifier-readout
composite multipliers; the 4-layer classification is the agent's judgment.
"""
from __future__ import annotations

# ADR-010-pinned thresholds (prose↔code doc-contract — see spec §2.1).
_BOUNDED_UPPER = 3.0
_MODERATE_UPPER = 8.0
_HIGH_UPPER = 20.0
_P95_TAIL_ESCALATOR = 50.0


def classify_cost_class(composite_p75: float, composite_p95: float) -> str:
    """Return the cost-class band for a (p75, p95) composite pair.

    Tail escalator: composite_p95 >= 50.0 forces class_4_critical regardless
    of p75. Otherwise band on p75 with upper-inclusive lower-band boundaries.
    """
    if composite_p95 >= _P95_TAIL_ESCALATOR:
        return "class_4_critical"
    if composite_p75 <= _BOUNDED_UPPER:
        return "class_1_bounded"
    if composite_p75 <= _MODERATE_UPPER:
        return "class_2_moderate"
    if composite_p75 <= _HIGH_UPPER:
        return "class_3_high"
    return "class_4_critical"
