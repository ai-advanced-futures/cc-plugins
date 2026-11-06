# ADR-006 — Bounded-Product Safety Check (Pre-Pattern Routing)

**Status:** Accepted (2026-05-27). Rewritten for the marketplace port (2026-11-06).
**Charter:** v1.1.0 (no Charter change)

## Context

The Charter schema `agentic-pricing-diagnosis.schema.json` has the field `bounded_vs_unbounded` (`bounded` or `unbounded`). The plugin had no way to fill it in a safe way. A description of the product is easy to game. A fixed table that tests the cost ratio is not.

An earlier design called a safety check the most important guard against a failure of the multiplicative pricing-power formula. That formula was rejected in review. One of its four reasons: it did not survive the scrutiny of the bounded-product exception classes. Without a safety check, only the product description chose the pattern, and a person can game a description.

This ADR adds the check. ADR-008 closes the other reasons with the publication gate.

## Decision

1. **This change is in the pricing plugin only** — no Charter change. The publication gate is a separate change (ADR-008). Smallest viable scope.

2. **No new schema field** — `bounded_vs_unbounded` enum field already exists in Charter v1.0.0 `agentic-pricing-diagnosis.schema.json`. 4d populates it correctly via new logic. Provenance lives in the existing `value_metric_rationale` prose field (overwrite, not append, to fit the 500-char cap).

3. **Hybrid agent+lib split** — agent (`agentic-pricing-strategist`) owns classification (judgment, LLM-natured): natural-language product description → one of 4 exception class slugs. Lib (`bounded_product_safety_check.py`) owns matrix application (deterministic): apply 5-row override to (class, ratio) tuple. Matches pricing ADR-001/ADR-003 math-vs-judgment split convention.

4. **Canonical class slugs frozen** — 4 string identifiers (`perplexity-class`, `notion-ai-core`, `harvey-hebbia-evenup`, `replit-narrow-vertical`) frozen as `BOUNDED_CLASSES` tuple. Any future expansion (e.g., framework v2.2 adding a 5th class) requires a framework version bump + ADR-006-extension ADR.

5. **Edge-case extrapolations codified** — The source design gives 5 explicit rows with gaps. This ADR fills the gaps: `ratio < 3.0` → row 1 (`bounded` confirmed; class match holds); `5.0 < ratio < 20.0` → row 2 (`ambiguous`); `ratio > 50.0` → row 5 (`unbounded`). Negative ratio raises `ValueError` (P95 ≥ P75 invariant). Tests pin the boundary endpoints.

6. **`'ambiguous'` is internal-only** — the lib's `apply_matrix()` returns `Literal['bounded', 'unbounded', 'ambiguous']`, but the diagnosis schema enum doesn't include `'ambiguous'`. The agent handles `'ambiguous'` by reconciling via AskUserQuestion, and the final `bounded_vs_unbounded` field is always `'bounded'` or `'unbounded'`.

7. **Light enforcement** — doc-contract tests on agent prose (3 assertions) + parametrized matrix unit tests (~25 cases). No AST anti-regression test enforcing "all `bounded_vs_unbounded` values came from `apply_matrix`". Trust the agent prose and the review of the pull request to catch drift.

8. **Automated mode dispatch keys + fallback** — dispatch context carries `bounded_class_match: str | null` + `cost_ratio_observed: float | null`. Safety-check step reads them directly without AskUserQuestion when `automated: true`. Fallback for missing keys (legacy DPO from before sub-spec 4d shipped): `bounded_class_match` absent → treat as `None` (row 4 → unbounded); `cost_ratio_observed` absent AND `bounded_class_match` present → row 3 → unbounded (instrumentation gap); both absent → row 4 → unbounded. Agent never falls back to AskUserQuestion in automated mode (would block dispatch); unbounded is the safe-by-default choice when telemetry is unavailable.

## Consequences

**Positive:**

- Closes the gap in the correctness of prices — without this check, the strategist's pattern recommendations remain gameable via product description alone.
- 4 framework-defined exception classes (Perplexity / Notion AI core / Harvey-Hebbia-EvenUp / Replit Agent) get programmatic handling: bounded variants of patterns instead of full P4 retrofit / P9-P15 universal-rider stack.
- The cost-ratio disconfirmation step is the empirical anchor — product description is gameable, but median-to-P95 cost ratio is observable ground truth. The matrix's row 5 override ensures ratio data takes precedence when description and ratio disagree.
- Pure-function lib module is unit-testable across all 5 canonical rows + extrapolations + boundary endpoints + ValueError guards.

**Negative:**

- 4 canonical class slugs are frozen; framework v2.2+ expansion requires an ADR-006-extension. Mitigation: tests assert `len(BOUNDED_CLASSES) == 4` and exact slug set, so any change is intentional.
- Light enforcement means a later change could fill `bounded_vs_unbounded` by hand without `apply_matrix()`. Review of the pull request is the check.
- Cost-ratio response interpretation has judgment overhead: user says "around 8x" — strategist routes via row 2 (ambiguous) when row 5 (unbounded) might be more honest. Future calibration could come from real-world telemetry (the archetype-baseline-telemetry schema).

**Future:**

- ADR-008 adds the publication gate for the Charter.
- A case study file can record two anchors from 2026: the credit-model change of Notion Custom Agents and the change of EvenUp from a price per demand to a price per case.

## References

- `pricing/lib/bounded_product_safety_check.py`
- `scripts/bounded_safety_check.py`
- ADR-001 and ADR-003: the split of work between math (code) and judgment (the agent) that this ADR follows
