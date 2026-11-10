---
name: cost-amplifier-diagnostic
description: Run the 8-amplifier rule-of-thumb diagnostic — produce cost-amplifier-readout JSON for the portco engagement. Internal-only diagnostic; output feeds product-finance and architecture sub-specs.
model: sonnet
allowed-tools: Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/amplifier_readout.py" *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/amplifier_readout.py *), Edit(/.pricing/**)
audience: internal
---

# Cost-Amplifier Diagnostic — Phase 1 Insight

> Based on JustKeenAI Agentic Pricing Framework v2.1 (2026-05-13). See ${CLAUDE_PLUGIN_ROOT}/ATTRIBUTION.md.

Run only the script of this skill, as `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/amplifier_readout.py" ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because the Bash grant covers only that script. Do not read a file of the plugin, because this page holds each rule and the script holds the library and the schema.

## Mode Detection

Check dispatch context for `automated: true` before proceeding.
- **Automated** (`automated: true`): Skip all `AskUserQuestion` calls. Use values from the dispatch context. Proceed through all steps without pausing for user input.
- **Interactive** (default): Engage Socratic dialogue at checkpoints as described in the workflow below.

## Purpose

Diagnose which of the 8 framework cost amplifiers are present in the portco's agentic offering and compute the composite LogNormal cost multiplier. Produces `.pricing/cost-amplifier-readout.json` matching Charter schema.

## Workflow

1. **Gather amplifier readings** — for each of the 8 amplifiers (1 planner loop, 2 tool fan-out, 3 multi-model, 4 evaluator, 5 reasoning explosion, 6 observability, 7 RAG depth, 8 cache miss):
   - Present rule-of-thumb threshold (from framework Table §3.2)
   - Ask user with `AskUserQuestion`: present? Y/N (skip if automated mode — use dispatch context)
   - If present, capture multiplier_p75 + multiplier_p95

2. **Write the input file** — write `.pricing/cost-amplifier-input.json` with the Write tool. It holds one entry for each of the 8 amplifiers. An amplifier that is not present needs only `"present": false`.

   ```json
   {
     "amplifiers": {
       "1": {"present": true, "multiplier_p75": 2.5, "multiplier_p95": 6.0, "detection_signal": "planner loop count >3"},
       "2": {"present": false},
       "3": {"present": true, "multiplier_p75": 1.5, "multiplier_p95": 3.0, "detection_signal": "RAG depth"},
       "4": {"present": false},
       "5": {"present": true, "multiplier_p75": 1.3, "multiplier_p95": 2.5, "detection_signal": "verifier passes"},
       "6": {"present": false},
       "7": {"present": false},
       "8": {"present": false}
     },
     "notes": "Diagnostic readout for an unbounded support agent."
   }
   ```

3. **Compose and emit JSON** — run this command one time:

   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/amplifier_readout.py" --input .pricing/cost-amplifier-input.json --out .pricing/cost-amplifier-readout.json
   ```

   The script calls `pricing.lib.amplifier_composer.compose_amplifiers()` with the readings (the closed-form LogNormal composition resolves Charter §14.1 deferred decision per ADR-002). It checks the result against the Charter schema `cost-amplifier-readout.schema.json` and writes `.pricing/cost-amplifier-readout.json` (audience: internal const). It prints `composite mean=<m> p50=<m> p75=<m> p95=<m> present=<ids>`, then the `engagement_id`, then `wrote <file>`. On exit code 1, it prints one line that names the field with the error and writes no file: correct the input file and run the command again. Do not write the readout file yourself, because only the script checks it against the schema.

4. **Return** — composite mean / P50 / P75 / P95 from the line that the script printed, to caller (the agentic-pricing-strategist agent or direct user invocation). Downstream consumers: sensitivity-stress skill (T14), product-finance cost-coverage-readout (sub-spec 3).

## Output schema (Charter §8)

The script writes a file that matches `cost-amplifier-readout.schema.json`. The `amplifiers` field is a keyed object (keys 1–8 for the framework's 8 amplifiers), and `composite_p75` / `composite_p95` are flat top-level numbers (not nested under a `composite` object). Example:

```json
{
  "engagement_id": "11111111-2222-3333-4444-555555555555",
  "produced_at": "2026-05-19T12:00:00Z",
  "schema_version": "1.0.0",
  "mode": "rule_of_thumb",
  "amplifiers": {
    "1": {"multiplier_p75": 2.5, "multiplier_p95": 6.0, "detection_signal": "planner loop count >3", "present": true},
    "2": {"multiplier_p75": 1.2, "multiplier_p95": 2.0, "detection_signal": "model fan-out", "present": false},
    "3": {"multiplier_p75": 1.5, "multiplier_p95": 3.0, "detection_signal": "RAG depth", "present": true},
    "4": {"multiplier_p75": 1.0, "multiplier_p95": 1.0, "detection_signal": "n/a", "present": false},
    "5": {"multiplier_p75": 1.3, "multiplier_p95": 2.5, "detection_signal": "verifier passes", "present": true},
    "6": {"multiplier_p75": 1.0, "multiplier_p95": 1.0, "detection_signal": "n/a", "present": false},
    "7": {"multiplier_p75": 1.0, "multiplier_p95": 1.0, "detection_signal": "n/a", "present": false},
    "8": {"multiplier_p75": 1.0, "multiplier_p95": 1.0, "detection_signal": "n/a", "present": false}
  },
  "composite_p75": 2.5567,
  "composite_p95": 9.3255,
  "notes": "Diagnostic readout for an unbounded support agent.",
  "audience": "internal"
}
```

## Cross-References

- **Script:** `scripts/amplifier_readout.py`
- **Python library:** `pricing.lib.amplifier_composer` (T4)
- **Schema:** `schemas/agentic-pricing/cost-amplifier-readout.schema.json`
- **Downstream:** `sensitivity-stress` skill (T14), product-finance sub-spec 3, aiml sub-spec 4
