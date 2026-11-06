# ADR-005 — Inferred Archetype Cost Data (data_source provenance enum)

| | |
|---|---|
| Status | Accepted |
| Date | 2026-05-19 |
| Deciders | pricing-core sub-spec 1 |
| Context source | JustKeenAI Agentic Pricing Framework v2.1 — Table §3.1 (per-archetype cost-per-interaction baselines) |

## Context

The framework's Table §3.1 provides per-archetype cost-per-interaction baselines for **three** of the six in-scope archetypes:

- `support_agent` — ~$0.20 base inference per resolution
- `developer_tool` — ~$0.10 per task base
- `vertical_pro_services_agent` — ~$5.00 per deliverable base

The framework is silent on baselines for the other three archetypes (`sales_marketing_agent`, `knowledge_horizontal_copilot`, `autonomous_workflow_agent`). The framework's broader prose discusses these archetypes without committing to specific baseline numbers.

Pricing-core needs baselines for **all six** archetypes so `cost_taxonomy.effective_cost()` works uniformly. Three options were considered:

1. Refuse to ship until the framework publishes baselines for the missing three — blocks v1.4.0 indefinitely.
2. Pick inferred baselines without disclosure — silently introduces unverified data.
3. Pick inferred baselines and surface the provenance via a first-class enum — chosen.

## Decision

**Introduce `DataSource = Literal["framework_table", "inferred_v1_4_0"]`** as a runtime-typed provenance enum on every `EffectiveCostResult`.

**Encode per-archetype baselines in `cost_taxonomy._BASELINE_COST`**:

| Archetype | Baseline ($/interaction) | data_source |
|---|---|---|
| support_agent | 0.20 | framework_table |
| developer_tool | 0.10 | framework_table |
| vertical_pro_services_agent | 5.00 | framework_table |
| sales_marketing_agent | 0.50 | inferred_v1_4_0 |
| knowledge_horizontal_copilot | 0.30 | inferred_v1_4_0 |
| autonomous_workflow_agent | 2.00 | inferred_v1_4_0 |

**Inferred baseline rationale** (derived from the framework's prose context, not its Table §3.1):

- `sales_marketing_agent` (e.g., Clay) — mid-cost workflow; per-contact enrichment cost ≈ 5x support's per-resolution given multi-API fan-out + LLM-classification chains. Anchor: $0.50.
- `knowledge_horizontal_copilot` (e.g., Perplexity Pro) — bounded surface with RAG depth + multi-model routing; cost between support and autonomous-workflow. Anchor: $0.30.
- `autonomous_workflow_agent` (e.g., Sierra) — heavy planner-loop + multi-tool fan-out; ~10x support cost reflects framework §3.2 amplifier #1 + #2 typical co-presence. Anchor: $2.00.

**Refinement deferred to v1.4.1** — the aiml sub-spec (Charter sub-spec 4) ships amplifier telemetry that will replace these inferred values with telemetry-enriched data. The data_source enum will flip from `inferred_v1_4_0` to `telemetry_v1_4_1` for those three archetypes at that time.

## Consequences

- Downstream consumers (`agentic-pricing-strategist`, sensitivity-stress skill, product-finance cost-coverage-readout) can read `data_source` to decide whether to flag the recommendation as "validated" vs "directional".
- The Charter §11.3 "honesty over precision" principle is structurally enforced — the type system makes the provenance distinction unavoidable.
- The inferred baselines are visible to code reviewers (in `_BASELINE_COST`) and to ADR readers (here). No silent assumption.
- Future framework releases that fill in the missing baselines will update the enum to `framework_table_v2_2_2026` (or whichever version), preserving the audit trail.

## Cross-references

- Implementation: `plugins/pricing/pricing/lib/cost_taxonomy.py` (T6)
- Tests: `plugins/pricing/tests/unit/test_cost_taxonomy.py` (8 tests including per-archetype provenance assertions)
- Framework reference: JustKeenAI Agentic Pricing Framework v2.1 Table §3.1 (where present)
- Follow-up: Charter sub-spec 4 (aiml) will refine inferred values via telemetry

## Amendment (sub-spec 4c, 2026-05-31) — the promised flip is realized

The v1.4.1 refinement promised above is delivered by Charter sub-spec 4c (aiml v0.4.0 + pricing v1.7.0):

- `DataSource` gains a third value `telemetry_v1_4_1`.
- `cost_taxonomy.effective_cost()` gains an optional `telemetry_baselines` param. When an `archetype-baseline-telemetry` artifact (§7.13, aiml-produced) is present AND the archetype is in the strict `_TELEMETRY_OVERRIDABLE` allowlist (`sales_marketing_agent`, `knowledge_horizontal_copilot`, `autonomous_workflow_agent`), the telemetry-derived baseline replaces the inferred value and `data_source` flips to `telemetry_v1_4_1`.
- **Strict allowlist:** framework_table archetypes are NEVER telemetry-overridden — a telemetry entry for them is ignored (not an error). The framework table stays authoritative.
- **Graceful fallback:** absent/None telemetry → existing `inferred_v1_4_0` lookup, unchanged.
- pricing reads the artifact via `archetype_baseline_loader.py` (its own jsonschema reader; no aiml import — schema-coupled federation per Charter §6).
