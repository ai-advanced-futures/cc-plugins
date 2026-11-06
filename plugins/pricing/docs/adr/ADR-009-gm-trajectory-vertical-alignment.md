# ADR-009: Align gm_trajectory vertical caps to product-finance §5.3

**Status:** Accepted

**Date:** 2026-06-04

## Context

`pricing/lib/gm_trajectory.py::project_gm_trajectory` projects a Year-1/2/3 gross-margin trajectory under the Predictability Architecture. For the vertical-labor-anchor archetype (`vertical_pro_services_agent`) it previously used pre-C4 caps — Y1 55, Y2 65, Y3 75, annual step +5. Under those caps the vertical Y3 is mathematically bounded at 65 (Y1≤55 → Y2≤60 → Y3=min(75,65)=65), so `requires_vertical_anchor_for_70plus = (Y3 >= 70)` was **always False** — dead code.

product-finance re-implemented the same math in `scripts/cost_coverage_readout.py::compute_gm_trajectory` and intentionally diverged on the vertical branch (product-finance ADR-002 §Decision + §Consequences): caps 60/70/80, annual step +7, to make the anchor flag reachable. ADR-002 flagged that "a follow-up pricing PR should align pricing-core's `gm_trajectory.py` to match." This is that follow-up (FOLLOWUPS.md F5).

## Decision

Adopt the §5.3 C4 vertical caps (60/70/80, annual step +7; starting step +10 unchanged) in pricing-core. Extract named module constants for both the standard and vertical paths; the standard branch is behaviorally unchanged (its literals are merely named). The vertical-anchor flag becomes reachable (vertical @ starting_gm=55 → Y3=74 → True).

A pricing-side re-divergence guard test (`tests/unit/test_gm_trajectory.py::TestVerticalCapsMatchSpec53`) pins the vertical constants to the §5.3 values. Per Charter §6.1 (re-implement, don't import), pricing and product-finance keep independent implementations; the guard asserts pricing's own constants rather than importing product-finance.

## Consequences

- **Behavior change (vertical only):** the vertical-archetype Y1/Y2/Y3 output band shifts (e.g. @ starting_gm=55: 55/60/65 → 60/67/74). Warrants the minor version bump 1.7.2 → 1.8.0.
- **Reachable flag:** `requires_vertical_anchor_for_70plus` is now live for the vertical archetype at realistic starting margins (e.g. `starting_gm=46` → Y3=70, the inclusive `>=70` threshold).
- **Nominal ceilings:** the `_VERTICAL_Y2_CAP=70` / `_VERTICAL_Y3_CAP=80` caps are §5.3 nominal ceilings the `+7` step never actually reaches — given `_VERTICAL_Y1_CAP=60`, the path saturates at max Y2=67 / max Y3=74. They are retained as the spec's declared upper bounds (and would bind if the Y1 cap or the step were raised), but the maximum reachable Y3 today is **74%**, not 80%. The anchor flag's reachability comes from the Y3=74 step value, not from the caps binding.
- **Standard branch unaffected:** identical outputs for all inputs.
- **No API change:** `project_gm_trajectory` signature and `GmTrajectory` shape unchanged; no production caller exists (the `pa` param is a never-wired stub).
- **Closes product-finance ADR-002:** the §Decision and §Consequences "follow-up should align" notes are annotated RESOLVED, and the stale follow-up pointer in `cost_coverage_readout.py`'s module docstring is corrected.
