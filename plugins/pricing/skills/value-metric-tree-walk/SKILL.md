---
name: value-metric-tree-walk
description: Walk the 6-archetype → 8-terminal value-metric decision tree from the Agentic Pricing Framework — produces value-metric-tree-walk JSON with terminal_node, archetype, layer classification, and recommended pattern_ids.
model: sonnet
allowed-tools: Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/tree_walk.py" *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/tree_walk.py *), Edit(/.pricing/**)
audience: mixed
---

# Value-Metric Tree Walk — Phase 1 Insight

> Based on JustKeenAI Agentic Pricing Framework v2.1 (2026-05-13). See ${CLAUDE_PLUGIN_ROOT}/ATTRIBUTION.md.

Run only the script of this skill, as `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/tree_walk.py" ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because the Bash grant covers only that script. Do not read a file of the plugin, because this page holds each rule and the script holds the library and the schema.

## Mode Detection

Check dispatch context for `automated: true` before proceeding.
- **Automated** (`automated: true`): Skip all `AskUserQuestion` calls. Use values from the dispatch context. Proceed through all steps without pausing for user input.
- **Interactive** (default): Engage Socratic dialogue at checkpoints as described in the workflow below.

## Purpose

Walk the 6-archetype → 8-terminal value-metric decision tree to identify the recommended pricing pattern bundle for a portco offering. Customer-facing pattern recommendations stay outside fences below; internal diagnostic prose is fenced.

## Workflow

1. **Gather portco answers** — ask user (or read from dispatch context in automated mode):
   - `success_mode` — what does success look like? (volume / outcome / productivity / net_new / dev_output)
   - `branch_diagnostic` — YES/NO for the success_mode's branch question (per framework §4.2)
   - `bounded_vs_unbounded` — is the agentic surface bounded or unbounded?
   - `portco_arr_band` — what ARR band? (<50M / 50-100M / 100-200M / 200-500M / >500M)

2. **Write the input file** — write `.pricing/tree-walk-input.json` with the Write tool. `branch_diagnostic` is `true` for YES and `false` for NO. `value_metric_rationale` is optional: 1 or 2 sentences that say why the answers give this value metric.

   ```json
   {
     "success_mode": "volume",
     "branch_diagnostic": true,
     "bounded_vs_unbounded": "unbounded",
     "portco_arr_band": "50-100M",
     "value_metric_rationale": "Success is the number of resolved tickets, and each resolution has a clear count."
   }
   ```

3. **Walk the tree and emit JSON** — run this command one time:

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/tree_walk.py" --input .pricing/tree-walk-input.json --out .pricing/agentic-pricing-diagnosis.json
   ```

   The script calls `pricing.lib.value_metric_tree.walk_tree(TreeAnswers(...))`. It checks the result against the Charter schema `agentic-pricing-diagnosis.schema.json` and writes `.pricing/agentic-pricing-diagnosis.json`. (Filename matches the canonical Charter schema name; this is the same artifact consumed by the agentic-pricing-strategist agent at step 3.) It prints `terminal_node=<t> archetype=<a> layer=<l> confidence=<c> patterns=<ids>`, then the `engagement_id`, then `wrote <file>`. On exit code 1, it prints one line that names the field with the error and writes no file: correct the input file and run the command again. Do not write the diagnosis file yourself, because only the script checks it against the schema.

4. **Return** — the terminal node, the archetype, the confidence and the recommended pattern ids from the line that the script printed.

## Customer-facing pattern recommendation

The walk returns a recommended pattern bundle. Common bundles include quality assurance with value floors, predictable AI cost via spending caps and pass-through triggers, and model-version hedges to preserve renewal-rate protection.

The exact bundle depends on the terminal node:

- Volume-driven (terminal A.2 / A.3): hybrid seat-plus-meter with budget caps and pass-through cost trigger
- Outcome-driven (terminal B.2 / B.3): outcome + quality assurance + budget caps
- Productivity-driven (terminal C.2 / C.3): per-seat or hybrid with budget caps
- Developer-tooling (terminal E.2 / E.3): tiered hybrid or per-task with budget caps

<!-- audience:internal -->
## Internal diagnostic notes

The terminal-node mapping enforces ADR-004's canonical 8-terminal set via `canonical_terminal_node()`. The D.2 branch (net_new) is collapsed to B.2 per framework §4.2. The pattern-bundle assignment per terminal is the ADR-004 default; the agentic-pricing-strategist agent may override based on cost-coverage equilibrium diagnostic findings or amplifier multiplier composition.

For deep-dive context: the framework Chapter 2 decision tree separates archetypes by `bounded_vs_unbounded` × `success_mode`; the bounded/unbounded mismatch with archetype lowers `confidence` from "high" to "medium".
<!-- /audience -->

## Cross-References

- **Script:** `scripts/tree_walk.py`
- **Python library:** `pricing.lib.value_metric_tree` (T5)
- **ADR:** `plugins/pricing/docs/adr/ADR-004-terminal-node-to-pattern-bundle.md`
- **Schema:** `schemas/agentic-pricing/agentic-pricing-diagnosis.schema.json`
- **Downstream:** pattern-selection-agentic skill (T13), agentic-pricing-strategist agent (T15)
