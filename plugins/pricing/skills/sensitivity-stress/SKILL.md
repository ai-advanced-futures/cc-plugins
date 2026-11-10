---
name: sensitivity-stress
description: Apply the S1-S5 sensitivity matrix stress test to a portco's pricing model + composite cost amplifier — produces sensitivity-stress.json feeding product-finance cost-coverage-readout. Internal-only diagnostic.
model: sonnet
allowed-tools: Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/sensitivity_stress.py" *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/sensitivity_stress.py *), Edit(/.pricing/**)
audience: internal
---

# Sensitivity Stress — Phase 1 Insight (internal-only)

> Based on JustKeenAI Agentic Pricing Framework v2.1 (2026-05-13). See ${CLAUDE_PLUGIN_ROOT}/ATTRIBUTION.md.

Run only the script of this skill, as `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/sensitivity_stress.py" ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because the Bash grant covers only that script. Do not read a file of the plugin, because this page holds each rule and the script holds the library.

## Mode Detection

Check dispatch context for `automated: true` before proceeding.
- **Automated** (`automated: true`): Skip all `AskUserQuestion` calls. Use values from the dispatch context. Proceed through all steps without pausing for user input.
- **Interactive** (default): Engage Socratic dialogue at checkpoints as described in the workflow below.

## Purpose

Apply framework Table §3.3's 5-scenario stress matrix (S1 base, S2 inference +50%, S3 volume +200%, S4 loop 3x, S5 combined) to a portco's pricing model + composite cost amplifier. Output feeds the cost-coverage equilibrium and amplifier multiplier discussion in product-finance sub-spec 3.

## Workflow

1. **Load inputs** — the composite AmplifierCompositeResult comes from `.pricing/cost-amplifier-readout.json` (T11 output): the script reads that file, so you give only its path. If the file is absent, stop and say that the `cost-amplifier-diagnostic` skill must run first. Gather the PricingModelInput (archetype, headline_price, pricing_unit, cost_per_interaction_baseline) from the portco diagnosis (ask the user, or read the dispatch context in automated mode). When a §7.13 `archetype-baseline-telemetry` artifact is present, `cost_per_interaction_baseline` must be the raw telemetry-overridden baseline the strategist resolved in its step 3c (`tb[archetype].baseline_cost_per_interaction`, `data_source = telemetry_v1_4_1`) — explicitly not `effective_cost`'s `median_effective_per_interaction` output, which is already amplified (`baseline × p50`). `compute_sensitivity` applies the composite amplifier internally (× composite p75 for S1, etc.), so forwarding the already-amplified value would double-count the amplifier and overstate the S1–S5 margins. When you have no raw baseline, leave `cost_per_interaction_baseline` out: the script then uses the raw inferred baseline (`_BASELINE_COST[archetype][0]`) and prints its source. Do not estimate a baseline, because the table of the library has the value.

2. **Write the input file** — write `.pricing/sensitivity-stress-input.json` with the Write tool. `archetype` is one of `support_agent`, `developer_tool`, `vertical_pro_services_agent`, `sales_marketing_agent`, `knowledge_horizontal_copilot`, `autonomous_workflow_agent`. `pricing_unit` is one of `per_seat`, `per_outcome`, `per_task`, `per_resolution`, `per_deliverable`, `per_run`, `per_acu`.

   ```json
   {
     "archetype": "support_agent",
     "headline_price": 1.5,
     "pricing_unit": "per_resolution",
     "cost_per_interaction_baseline": 0.2,
     "readout": ".pricing/cost-amplifier-readout.json"
   }
   ```

3. **Stress and emit JSON** — run this command one time:

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/sensitivity_stress.py" --input .pricing/sensitivity-stress-input.json --out .pricing/sensitivity-stress.json
   ```

   The script calls `pricing.lib.sensitivity_matrix.compute_sensitivity(archetype, pricing_model, composite_amplifier)` and writes `.pricing/sensitivity-stress.json` with full S1S5Result + per-scenario narrative_md. It prints `s1=<m> s2=<m> s3=<m> s4=<m> s5=<m> baseline=<b> source=<s>` (effective margin % per scenario), then `wrote <file>`. On exit code 1, it prints one line that names the field with the error and writes no file: correct the input file and run the command again. Do not write the stress file yourself, because only the script calls the library.

4. **Inspect S1-S5 margins** — review effective margin % per scenario, from the line that the script printed:
   - S1 base case
   - S2 inference +50% — provider cost shock
   - S3 volume +200% — loop pressure proxy
   - S4 loop 3x — canonical or fallback path depending on whether amp #1 (planner re-run) is in the composite's present_amplifiers
   - S5 combined — worst-case stack

5. **Flag margin collapse risks** — any scenario where effective margin drops below the portco's vendor margin floor is a margin collapse / cost-coverage trap signal. Recommend additional patterns (typically P9 cap + P15 trigger) to mitigate.

## Cross-References

- **Script:** `scripts/sensitivity_stress.py`
- **Python library:** `pricing.lib.sensitivity_matrix` (T9) + `pricing.lib.amplifier_composer` (T4)
- **Upstream:** cost-amplifier-diagnostic skill (T11), pattern-selection-agentic skill (T13)
- **Downstream:** product-finance sub-spec 3 (cost-coverage-readout), agentic-pricing-strategist agent (T15)
- **Output shape:** the `S1S5Result` keys of `pricing.lib.sensitivity_matrix`: the 5 `*_margin_pct` numbers and `narrative_md_per_scenario`. No Charter schema covers this file (ADR-003: the 4 skills make 3 Charter schemas).
