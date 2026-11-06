---
name: pattern-selection-agentic
description: Take a value-metric-tree-walk diagnosis, filter pattern_catalogue by ACV band, and recommend a pattern bundle — produces pattern-selection.json with customer_facing_name for each selected pattern.
model: sonnet
tools: Read, Write, Bash, Skill, AskUserQuestion
audience: mixed
---

# Pattern Selection (Agentic) — Phase 1 Insight

> Based on JustKeenAI Agentic Pricing Framework v2.1 (2026-05-13). See ${CLAUDE_PLUGIN_ROOT}/ATTRIBUTION.md.

## Mode Detection

Check dispatch context for `automated: true` before proceeding.
- **Automated** (`automated: true`): Skip all `AskUserQuestion` calls. Use values from the dispatch context. Proceed through all steps without pausing for user input.
- **Interactive** (default): Engage Socratic dialogue at checkpoints as described in the workflow below.

## Purpose

Take the value-metric-tree-walk output (terminal node + recommended_pattern_ids) and produce a final pattern-selection.json with customer-facing names, filtered by the portco's ACV band per pattern_catalogue.acv_band field.

## Workflow

1. **Load inputs** — read the value-metric-tree-walk JSON output (skill T12) and the portco's ACV band.

2. **Filter pattern_catalogue** — for each `pattern_id` in the recommended bundle, look up `PATTERNS[pattern_id]` from `pricing.lib.pattern_catalogue`. Reject any whose `acv_band` is incompatible with the portco's ACV.

3. **Customer-facing rename** — for each selected pattern, fetch the `name` field from the catalogue (the framework's customer-facing pattern name, e.g., "Outcome + Quality (no gainshare)" for P12-Light).

4. **Emit JSON** — write `pattern-selection.json` matching Charter schema with `selected_patterns: [{pattern_id, customer_facing_name, acv_band, audience_default}]`.

5. **Confirm with user** (interactive mode) — present the bundle in customer-facing terms and confirm before persisting.

## Customer-facing pattern presentation

The recommended bundle delivers predictable AI cost via spending caps and value floors, plus quality assurance via the contracted outcome floors. Pass-through triggers and model-version hedges preserve renewal-rate protection across the contract term.

<!-- audience:internal -->
## Internal selection rationale

The default bundle for each terminal node is from ADR-004's terminal-node → pattern-bundle map. Internal diagnostic notes: vendor margin retention via P9 caps + P15 pass-through is the cost-coverage equilibrium anchor.

ACV band filtering: P12 is scoped to >$1M ACV per framework §3.6; sub-$1M ACV deals fall back to P12-Light. P11 (ELA) is enterprise-only.
<!-- /audience -->

## Cross-References

- **Python library:** `pricing.lib.pattern_catalogue` (T2)
- **Upstream:** value-metric-tree-walk skill (T12)
- **Downstream:** sensitivity-stress skill (T14), agentic-pricing-strategist agent (T15)
- **Schema:** `${CLAUDE_PLUGIN_ROOT}/schemas/agentic-pricing/pattern-selection.schema.json`
