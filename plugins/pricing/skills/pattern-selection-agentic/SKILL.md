---
name: pattern-selection-agentic
description: Take a value-metric-tree-walk diagnosis, filter pattern_catalogue by ACV band, and recommend a pattern bundle — produces pattern-selection.json with customer_facing_name for each selected pattern.
model: sonnet
allowed-tools: Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/pattern_selection.py" *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/pattern_selection.py *), Edit(/.pricing/**)
audience: mixed
---

# Pattern Selection (Agentic) — Phase 1 Insight

> Based on JustKeenAI Agentic Pricing Framework v2.1 (2026-05-13). See ${CLAUDE_PLUGIN_ROOT}/ATTRIBUTION.md.

Run only the script of this skill, as `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/pattern_selection.py" ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because the Bash grant covers only that script. Do not read a file of the plugin, because this page holds each rule and the script holds the library and the schema.

## Mode Detection

Check dispatch context for `automated: true` before proceeding.
- **Automated** (`automated: true`): Skip all `AskUserQuestion` calls. Use values from the dispatch context. Proceed through all steps without pausing for user input.
- **Interactive** (default): Engage Socratic dialogue at checkpoints as described in the workflow below.

## Purpose

Take the value-metric-tree-walk output (terminal node + recommended_pattern_ids) and produce a final pattern-selection.json with customer-facing names, filtered by the portco's ACV band per pattern_catalogue.acv_band field.

## Workflow

1. **Load inputs** — read `.pricing/agentic-pricing-diagnosis.json` (the value-metric-tree-walk output, skill T12) for `recommended_pattern_ids`, and get the portco's ACV band (ask the user, or read the dispatch context in automated mode). If the diagnosis file is absent, stop and say that the `value-metric-tree-walk` skill must run first.

2. **Filter pattern_catalogue** — print the catalogue rows of the recommended patterns. Give each `pattern_id` of the bundle as one argument:

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/pattern_selection.py" --catalogue P4 P9 P15
   ```

   The script reads `PATTERNS[pattern_id]` from `pricing.lib.pattern_catalogue` and prints one line `<pattern_id>|<acv_band>|<audience_default>|<name>` for each pattern. With no pattern id, it prints each pattern of the catalogue. Reject each pattern whose `acv_band` is incompatible with the portco's ACV (`any` is compatible with each ACV).

3. **Customer-facing rename** — the `name` field of each line is the framework's customer-facing pattern name (e.g., "Outcome + Quality (no gainshare)" for P12-Light). Present each selected pattern with that name.

4. **Confirm with user** (interactive mode) — present the bundle in customer-facing terms and confirm before persisting.

5. **Write the input file** — write `.pricing/pattern-selection-input.json` with the Write tool. It holds one entry for each selected pattern. `rationale` is at most 500 characters. `customer_facing_name` (the name of the bundle) and `dependencies` are optional; each dependency names 2 selected patterns.

   ```json
   {
     "patterns": [
       {"pattern_id": "P4", "rationale": "The ACV of $120k is in the band $50k+, and success is a volume of resolved tickets."},
       {"pattern_id": "P9", "rationale": "A budget hard stop gives a predictable AI cost."},
       {"pattern_id": "P15", "rationale": "A pass-through trigger protects the margin when the provider cost goes up."}
     ],
     "customer_facing_name": "Hybrid seat + meter with spending caps",
     "dependencies": [
       {"pattern_id": "P15", "depends_on_pattern_id": "P9", "reason": "The trigger uses the budget of the hard stop."}
     ]
   }
   ```

6. **Emit JSON** — run this command one time:

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/pattern_selection.py" --input .pricing/pattern-selection-input.json --out .pricing/pattern-selection.json
   ```

   The script takes `acv_band` of each pattern from the catalogue. It checks the result against the Charter schema `pattern-selection.schema.json` and writes `.pricing/pattern-selection.json` with `selected_patterns: [{pattern_id, acv_band, rationale}]`, `customer_facing_name` and `dependencies`. It prints `selected=<ids> name=<customer_facing_name>`, then the `engagement_id`, then `wrote <file>`. On exit code 1, it prints one line that names the error and writes no file: correct the input file and run the command again. Do not write the selection file yourself, because only the script checks it against the schema.

## Customer-facing pattern presentation

The recommended bundle delivers predictable AI cost via spending caps and value floors, plus quality assurance via the contracted outcome floors. Pass-through triggers and model-version hedges preserve renewal-rate protection across the contract term.

<!-- audience:internal -->
## Internal selection rationale

The default bundle for each terminal node is from ADR-004's terminal-node → pattern-bundle map. Internal diagnostic notes: vendor margin retention via P9 caps + P15 pass-through is the cost-coverage equilibrium anchor.

ACV band filtering: P12 is scoped to >$1M ACV per framework §3.6; sub-$1M ACV deals fall back to P12-Light. P11 (ELA) is enterprise-only.
<!-- /audience -->

## Cross-References

- **Script:** `scripts/pattern_selection.py`
- **Python library:** `pricing.lib.pattern_catalogue` (T2)
- **Upstream:** value-metric-tree-walk skill (T12)
- **Downstream:** sensitivity-stress skill (T14), agentic-pricing-strategist agent (T15)
- **Schema:** `schemas/agentic-pricing/pattern-selection.schema.json`
