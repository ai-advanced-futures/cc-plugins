# ADR-002: Charter Cost-Coverage Re-implementation

**Date:** 2026-05-21
**Status:** Accepted
**Attribution:** JustKeenAI Agentic Pricing Framework v2.1 (2026-05-13)
**Charter:** the agentic pricing Charter v1.0.0

## Context

Charter sub-spec 3 requires product-finance to produce a `cost-coverage-readout` artifact (audience: internal) that combines pricing's diagnosis + cost-amplifier-readout with the company's own financial metrics (GM%, NRR delta, forecast variance) to deliver S1-S5 sensitivity matrix, Y1/Y2/Y3 GM trajectory, and PE multiple compression signals.

The math (S1-S5, GM trajectory, compression signals) already exists in `pricing/lib/{sensitivity_matrix,gm_trajectory,multiple_compression}.py`. The question was: import the pricing modules, or re-implement?

## Decision

Product-finance re-implements the S1-S5, GM trajectory, and compression signal math as plain Python in `scripts/cost_coverage_readout.py`, citing Charter §6.3 and pricing-core as the reference implementation. No imports from `pricing/lib`.

The `cost-coverage-agent` is dispatched by its runner, `cost-coverage-runner`, or by the `cost-coverage` command.

## Rationale

Charter §6.1 mandates no cross-plugin Python imports at runtime: "`pricing/lib/` owns the canonical Python implementation. Every other in-scope plugin reimplements only the slice it needs."

`pricing` is explicitly excluded from the uv workspace (the root `pyproject.toml` comment "pricing is NOT a uv workspace member. Including it broke the workspace" reflects a prior failed attempt at workspace coupling). Even if pricing were a workspace member, the Charter still forbids the import.

The Charter is the source of truth for the algorithms; pricing-core happens to implement the same math for its own purposes. Product-finance's implementation additionally uses the company's own financial metrics (GM%, NRR delta, forecast variance) as inputs that pricing does not have access to.

For the vertical-archetype GM trajectory, this sub-spec intentionally diverges from pricing-core's `gm_trajectory.py` (which uses step +5 for both standard and vertical paths and caps Y3 at 75): the spec uses step +7 and caps Y3 at 80 for the vertical archetype. This makes `requires_vertical_anchor_for_70plus` reachable. A follow-up pricing PR should align pricing-core's `gm_trajectory.py` to match — tracked in spec §15 non-goals. ✅ RESOLVED by pricing v1.8.0 (ADR-009) — pricing-core's `gm_trajectory.py` now uses the same §5.3 C4 caps (60/70/80, step +7).

## Consequences

- **Math sync obligation:** If pricing-core's algorithms change, both implementations must be updated to stay Charter-conformant.
- **Cross-plugin enforcement:** The Charter cross-plugin test `pricing/tests/unit/test_charter_cross_plugin.py::test_conforming_plugins_only_claim_schemas_they_participate_in` verifies that product-finance's `.charter-conforms` claims align with `CHARTER_MATRIX`.
- **Test failure modes:** The cross-plugin test would fail if (a) the schema name in `.charter-conforms` diverges from the canonical name in `CHARTER_MATRIX`, or (b) product-finance is removed from the producer set for `cost-coverage-readout` in pricing's matrix.
- **Format-level changes:** Adding new fields per line in `.charter-conforms` beyond `<schema>: <role>` would require a corresponding update to `_discover_conforming_plugins()` in pricing — the parser was updated in PR #105 to handle the role-annotated format.
- **Vertical GM divergence:** The vertical-archetype `+7` step in `compute_gm_trajectory` diverges from pricing-core's `+5`. A follow-up pricing PR should align pricing-core's `gm_trajectory.py` to match (tracked in spec §15 non-goals). ✅ RESOLVED by pricing v1.8.0 (ADR-009).

## Amendment (v0.11.0): no handoff file

Version 0.4.0 wrote a handoff file to two paths for one outside tool. Version 0.11.0 removed that tool and the file. The agent writes `cost-coverage-readout.json` in `.product-finance/{engagement_id}/` and the result file of ADR-006. It has no handoff option.

## Decision: Charter Schema Enum Tightening — `multiple_pressure_estimate`

The Charter `cost-coverage-readout.schema.json` originally declared `multiple_pressure_estimate` as `{"type": "string"}` — any string allowed. Semantic review T1-2 surfaced this as a contract gap.

**Decision:** This PR tightens the schema to `{"type": "string", "enum": ["0", "0.5-1x", "1-2x", ">2x"]}` matching the Pydantic `Literal` in `cost_coverage_readout.py`.

**Rationale:** The Pydantic model is the source of truth for valid values; aligning the JSON Schema closes the back-door where a non-Pydantic consumer could accept malformed data.

**Consequence:** Any future schema amendment must keep these two declarations synchronized — enforced by `tests/unit/test_cost_coverage_schema.py::TestSchemaSha256Pin::test_pinned_sha256_matches_live_schema` (catches drift via hash) and `test_invalid_pressure_estimate_rejected` (catches enum-allowed values that fall outside).

The Charter schema sha256 pin was rebootstrapped after this change. See `scripts/bootstrap_cost_coverage_schema_hash.py`.
