"""GM trajectory under Predictability Architecture (PA) per framework §3.17.

Standard archetypes hold 45-55% (Y1) / 50-60% (Y2) / 55-65% (Y3) GM under PA.
The vertical-labor-anchor archetype (`vertical_pro_services_agent`) follows the
product-finance spec §5.3 C4 trajectory — caps 60/70/80 with annual step +7 —
reaching up to 74% GM by Y3 (the 70/80 caps are nominal ceilings the +7 step
never reaches: max Y2=67, max Y3=74), which makes the 70%+ vertical-anchor
requirement reachable. See ADR-009; this closes the divergence recorded in product-finance
ADR-002 §3 (pricing-core previously used pre-C4 caps 55/65/75 with step +5,
leaving `requires_vertical_anchor_for_70plus` unreachable).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Charter §3.17 + product-finance spec §5.3 GM-trajectory constants.
# Vertical caps use the §5.3 C4 values (60/70/80, step +7) so that
# `requires_vertical_anchor_for_70plus` is reachable. See ADR-009.
# ---------------------------------------------------------------------------
_VERTICAL_Y1_CAP: float = 60.0
# Y2/Y3 caps are §5.3 nominal ceilings; given Y1_CAP=60 + step 7 the path
# saturates at max Y2=67, max Y3=74 — these caps never actually bind.
_VERTICAL_Y2_CAP: float = 70.0
_VERTICAL_Y3_CAP: float = 80.0
_VERTICAL_STARTING_STEP: float = 10.0   # Y1 = min(cap, starting_gm + STARTING_STEP)
_VERTICAL_ANNUAL_STEP: float = 7.0      # +7 per year (was +5, pre-C4)

_STANDARD_Y1_FLOOR: float = 45.0
_STANDARD_Y1_CAP: float = 55.0
_STANDARD_Y2_CAP: float = 60.0
_STANDARD_Y3_CAP: float = 65.0
_STANDARD_STARTING_STEP: float = 7.0
_STANDARD_ANNUAL_STEP: float = 5.0

_VERTICAL_ANCHOR_THRESHOLD_PCT: float = 70.0


@dataclass
class GmTrajectory:
    y1_pct: float
    y2_pct: float
    y3_pct: float
    requires_vertical_anchor_for_70plus: bool
    rationale_md: str


def project_gm_trajectory(archetype: str, pa: Any, starting_gm_pct: float) -> GmTrajectory:
    """Project Y1/Y2/Y3 GM trajectory under PA per framework §3.17.

    The vertical-labor-anchor archetype uses §5.3 C4 caps (60/70/80, step +7);
    all other archetypes use the standard 45-55 / 50-60 / 55-65 trajectory.
    """

    is_vertical = archetype == "vertical_pro_services_agent"

    if is_vertical:
        y1 = min(_VERTICAL_Y1_CAP, starting_gm_pct + _VERTICAL_STARTING_STEP)
        y2 = min(_VERTICAL_Y2_CAP, y1 + _VERTICAL_ANNUAL_STEP)
        y3 = min(_VERTICAL_Y3_CAP, y2 + _VERTICAL_ANNUAL_STEP)
    else:
        y1 = min(_STANDARD_Y1_CAP, max(_STANDARD_Y1_FLOOR, starting_gm_pct + _STANDARD_STARTING_STEP))
        y2 = min(_STANDARD_Y2_CAP, y1 + _STANDARD_ANNUAL_STEP)
        y3 = min(_STANDARD_Y3_CAP, y2 + _STANDARD_ANNUAL_STEP)

    requires_anchor = y3 >= _VERTICAL_ANCHOR_THRESHOLD_PCT

    rationale = (
        f"Y1 ({y1:.1f}%): Caps + value floors land; basic Predictability Architecture in place. "
        f"Y2 ({y2:.1f}%): Provider-cost stress-test season passes; pass-through triggers operationalized. "
        f"Y3 ({y3:.1f}%): Model-version hedges operational; full PA. "
        f"{'Requires vertical labor anchor for 70%+ trajectory.' if requires_anchor else 'No vertical anchor required at this GM level.'}"
    )

    return GmTrajectory(
        y1_pct=y1, y2_pct=y2, y3_pct=y3,
        requires_vertical_anchor_for_70plus=requires_anchor,
        rationale_md=rationale,
    )
