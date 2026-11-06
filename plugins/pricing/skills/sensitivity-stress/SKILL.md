---
name: sensitivity-stress
description: Apply the S1-S5 sensitivity matrix stress test to a portco's pricing model + composite cost amplifier — produces sensitivity-stress.json feeding product-finance cost-coverage-readout. Internal-only diagnostic.
model: sonnet
tools: Read, Write, Bash, Skill, AskUserQuestion
audience: internal
---

# Sensitivity Stress — Phase 1 Insight (internal-only)

> Based on JustKeenAI Agentic Pricing Framework v2.1 (2026-05-13). See ${CLAUDE_PLUGIN_ROOT}/ATTRIBUTION.md.

## Mode Detection

Check dispatch context for `automated: true` before proceeding.
- **Automated** (`automated: true`): Skip all `AskUserQuestion` calls. Use values from the dispatch context. Proceed through all steps without pausing for user input.
- **Interactive** (default): Engage Socratic dialogue at checkpoints as described in the workflow below.

## Purpose

Apply framework Table §3.3's 5-scenario stress matrix (S1 base, S2 inference +50%, S3 volume +200%, S4 loop 3x, S5 combined) to a portco's pricing model + composite cost amplifier. Output feeds the cost-coverage equilibrium and amplifier multiplier discussion in product-finance sub-spec 3.

## Workflow

1. **Load inputs** — read the cost-amplifier-readout (T11 output) for the composite AmplifierCompositeResult, and gather the PricingModelInput (archetype, headline_price, pricing_unit, cost_per_interaction_baseline) from the portco diagnosis. When a §7.13 `archetype-baseline-telemetry` artifact is present, `cost_per_interaction_baseline` must be the raw telemetry-overridden baseline the strategist resolved in its step 3c (`tb[archetype].baseline_cost_per_interaction`, `data_source = telemetry_v1_4_1`) — explicitly not `effective_cost`'s `median_effective_per_interaction` output, which is already amplified (`baseline × p50`). `compute_sensitivity` applies the composite amplifier internally (× composite p75 for S1, etc.), so forwarding the already-amplified value would double-count the amplifier and overstate the S1–S5 margins. Fall back to the raw inferred baseline (`_BASELINE_COST[archetype][0]`) when no telemetry artifact exists.

2. **Stress** — invoke `pricing.lib.sensitivity_matrix.compute_sensitivity(archetype, pricing_model, composite_amplifier)`.

3. **Inspect S1-S5 margins** — review effective margin % per scenario:
   - S1 base case
   - S2 inference +50% — provider cost shock
   - S3 volume +200% — loop pressure proxy
   - S4 loop 3x — canonical or fallback path depending on whether amp #1 (planner re-run) is in the composite's present_amplifiers
   - S5 combined — worst-case stack

4. **Emit JSON** — write `sensitivity-stress.json` with full S1S5Result + per-scenario narrative_md.

5. **Flag margin collapse risks** — any scenario where effective margin drops below the portco's vendor margin floor is a margin collapse / cost-coverage trap signal. Recommend additional patterns (typically P9 cap + P15 trigger) to mitigate.

## Cross-References

- **Python library:** `pricing.lib.sensitivity_matrix` (T9) + `pricing.lib.amplifier_composer` (T4)
- **Upstream:** cost-amplifier-diagnostic skill (T11), pattern-selection-agentic skill (T13)
- **Downstream:** product-finance sub-spec 3 (cost-coverage-readout), agentic-pricing-strategist agent (T15)
- **Schema:** `${CLAUDE_PLUGIN_ROOT}/schemas/agentic-pricing/sensitivity-stress.schema.json`
