# ADR-004 — Terminal-node → Pattern-bundle Mapping (default selection rule)

| | |
|---|---|
| Status | Accepted |
| Date | 2026-05-19 |
| Deciders | pricing-core sub-spec 1 |
| Context source | JustKeenAI Agentic Pricing Framework v2.1 §3 + §4 (decision tree + 19-pattern catalogue) |

## Context

The framework's decision tree (Chapter 2 + §4) walks 6 archetypes through 5 success-mode branches to 8 canonical terminal nodes (A.2, A.3, B.2, B.3, C.2, C.3, E.2, E.3 — D.2 aliases to B.2 per §4.2). Each terminal corresponds to a customer archetype + success-mode pairing. The framework's 19-pattern catalogue (Appendix A) provides per-pattern guidance.

The framework does **not** mechanically specify which patterns to recommend for each terminal — that is the strategist's role. Pricing-core must encode a defensible default mapping so the `walk_tree()` function returns recommendation candidates without requiring human judgment for every invocation.

## Decision

**Encode an 8-entry default-pattern-bundle table in `value_metric_tree.py`:**

| Terminal | Archetype | Default bundle | Rationale |
|---|---|---|---|
| A.2 | support_agent (bounded-outcome subset) | P4 + P9 + P15 | Hybrid seat+meter with universal riders |
| A.3 | support_agent (general) | P3 + P9 + P15 | Per-resolution with quality SLA + universal riders |
| B.2 | autonomous_workflow_agent | P12-Light + P9 + P15 | Outcome + Quality (no gainshare) at sub-$1M ACV; framework §3.6 |
| B.3 | sales_marketing_agent | P4 + P9 + P15 | Hybrid (attribution dispute defense per framework §3.4) |
| C.2 | vertical_pro_services_agent | P1 + P9 + P15 | Per-seat unlimited — vertical labor anchor, Harvey/EvenUp-class |
| C.3 | knowledge_horizontal_copilot | P4 + P9 + P15 | Hybrid for bounded surfaces (Perplexity-class) |
| E.2 | developer_tool (bounded subset) | P4 + P9 + P15 | Tiered hybrid + caps (Cursor avoidance) |
| E.3 | developer_tool (unbounded subset) | P2 + P9 + P15 | Per-task / per-ACU (Copilot AI Credits-class) |

**Universal riders P9 (Budget hard stop) and P15 (Pass-through cost trigger)** appear in every bundle because the framework's "Three Levers" (Caps + Floors + Hedges) sit at the universal-rider layer. P9 implements Lever 1 (Caps); P15 implements Lever 3 (Hedges via cost pass-through and version stability).

**Quality floors (P12 / P12-Light)** appear only in B.2 by default because (a) framework §3.6 scopes P12 to >$1M ACV, (b) P12-Light covers sub-$1M ACV outcome contracts, and (c) other archetypes don't structurally need a quality floor at the per-interaction layer.

**Engineer override** — the agentic-pricing-strategist agent (T15) may inspect the cost-amplifier-readout and sensitivity-stress outputs and override the default mapping. The default is a sensible-starting-point, not a forced selection.

## Consequences

- The `walk_tree()` function returns `recommended_pattern_ids` as a stable default for downstream consumers without requiring a separate LLM call.
- New patterns added to `pattern_catalogue.yaml` do NOT automatically join any bundle — a future ADR-006 (or v1.5.0) must explicitly update this 8-entry table.
- The mapping is encoded in Python (not YAML) because changes require ADR discipline. YAML-config edits are insufficient.
- T18's `test_diagnosis_fixture_pattern_ids_in_catalogue` and `test_returns_recommended_pattern_ids` (T5) gate the contract: every recommended pattern must exist in `PATTERN_IDS`.

## Cross-references

- Implementation: `plugins/pricing/pricing/lib/value_metric_tree.py` `_TERMINAL_TO_PATTERNS` dict (T5)
- Tests: `plugins/pricing/tests/unit/test_value_metric_tree.py::test_returns_recommended_pattern_ids` (T5)
- Catalogue: `schemas/agentic-pricing/pattern_catalogue.yaml`
- Framework reference: JustKeenAI Agentic Pricing Framework v2.1 §3.4, §3.5, §3.6 (P12 ACV scoping)
