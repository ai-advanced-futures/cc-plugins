---
name: cost-amplifier-diagnostic
description: Run the 8-amplifier rule-of-thumb diagnostic — produce cost-amplifier-readout JSON for the portco engagement. Internal-only diagnostic; output feeds product-finance and architecture sub-specs.
model: sonnet
tools: Read, Write, Bash, Skill, AskUserQuestion
audience: internal
---

# Cost-Amplifier Diagnostic — Phase 1 Insight

> Based on JustKeenAI Agentic Pricing Framework v2.1 (2026-05-13). See ${CLAUDE_PLUGIN_ROOT}/ATTRIBUTION.md.

## Mode Detection

Check dispatch context for `automated: true` before proceeding.
- **Automated** (`automated: true`): Skip all `AskUserQuestion` calls. Use values from the dispatch context. Proceed through all steps without pausing for user input.
- **Interactive** (default): Engage Socratic dialogue at checkpoints as described in the workflow below.

## Purpose

Diagnose which of the 8 framework cost amplifiers are present in the portco's agentic offering and compute the composite LogNormal cost multiplier. Produces `cost-amplifier-readout.json` matching Charter schema.

## Workflow

1. **Gather amplifier readings** — for each of the 8 amplifiers (planner loop, tool fan-out, multi-model, evaluator, reasoning explosion, observability, RAG depth, cache miss):
   - Present rule-of-thumb threshold (from framework Table §3.2)
   - Ask user: present? Y/N (skip if automated mode — use dispatch context)
   - If present, capture multiplier_p75 + multiplier_p95

2. **Compose** — invoke `pricing.lib.amplifier_composer.compose_amplifiers()` with the list of readings. The closed-form LogNormal composition resolves Charter §14.1 deferred decision per ADR-002.

3. **Emit JSON** — write `cost-amplifier-readout.json` matching Charter schema (audience: internal const). Schema location: `${CLAUDE_PLUGIN_ROOT}/schemas/agentic-pricing/cost-amplifier-readout.schema.json`.

4. **Return** — composite mean / P50 / P75 / P95 to caller (the agentic-pricing-strategist agent or direct user invocation). Downstream consumers: sensitivity-stress skill (T14), product-finance cost-coverage-readout (sub-spec 3).

## Output schema (Charter §8)

Output matches `${CLAUDE_PLUGIN_ROOT}/schemas/agentic-pricing/cost-amplifier-readout.schema.json`. The `amplifiers` field is a keyed object (keys 1–8 for the framework's 8 amplifiers), and `composite_p75` / `composite_p95` are flat top-level numbers (not nested under a `composite` object). Example:

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

- **Python library:** `pricing.lib.amplifier_composer` (T4)
- **Schema:** `${CLAUDE_PLUGIN_ROOT}/schemas/agentic-pricing/cost-amplifier-readout.schema.json`
- **Downstream:** `sensitivity-stress` skill (T14), product-finance sub-spec 3, aiml sub-spec 4
