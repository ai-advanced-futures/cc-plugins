# ADR-003: Trigger/Mode Taxonomy Reconciliation (F67)

**Status:** Accepted
**Date:** 2026-06-12
**Plugin:** competitive-intelligence v1.5.0 (F67)

---

## Context

Before F67 the plugin carried two divergent trigger taxonomies. The live prose
contract (the dispatch fields, `context-analyst.md` Q1 mapping,
`lens-executor.md` priority rows) used `feature_decision` /
`competitor_response` / `strategic_planning` / `monitoring` — plus a stray
`sales_enablement` value that appeared in trigger positions even though the
Python reference model treats it as an analysis *mode*, not a trigger. The
never-invoked Python reference model (`scripts/phase_01_context_discovery.py`)
used `feature_validation` / `competitive_response` / `strategic_planning` /
`continuous_monitoring` for its `AnalysisTrigger` enum, with a separate
2-value `AnalysisMode` enum (`strategic_planning`, `sales_enablement`). ADR-001
Decision 6 recorded a hybrid of the two. Separately, the key `mode` was
overloaded: it carried the analysis mode in internal artifacts and in the
published ci-swot-v1 SWOT artifact, while the same key name carried the
dispatch mode (`interactive|automated`) in session state.

F67 reconciles the taxonomy. The user confirmed all five decisions below in
the design spec of F67.

---

## Decision

### Canonical model (post-F67)

- **Trigger** — 4 values: `feature_decision`, `competitor_response`,
  `strategic_planning`, `monitoring`. Sole input to lens-priority routing and
  depth classification.
- **Analysis mode** — 2 values: `strategic_planning`, `sales_enablement`.
  Affects framing only (objective vs positioning) in synthesizer and
  deliverable-generator. Never affects lens routing.
- Carried as `trigger` + `analysis_mode` in `context-config.json` — the sole
  live carrier; `analysis_mode` is optional in the dispatch fields
  (default `strategic_planning`). The internal session-metadata.json /
  metadata.json artifacts (and `schemas/metadata.json`) carry the same
  canonical pair.

### 1. Prose values are canonical (decision a)

The canonical trigger value set is the prose contract:
`feature_decision` / `competitor_response` / `strategic_planning` /
`monitoring`. These are the live, externally visible contract; the Python
enum is internal-only (the reference models are never invoked at runtime), so
renaming it is contained and zero-risk. The old→new value mapping:

| Old (Python reference model) | New (canonical) |
|------------------------------|-----------------|
| `feature_validation` | `feature_decision` |
| `competitive_response` | `competitor_response` |
| `strategic_planning` | `strategic_planning` (unchanged) |
| `continuous_monitoring` | `monitoring` |

### 2. Trigger-only lens routing (decision b1)

Analysis mode does **not** affect lens routing — routing is trigger-only
(matching the Python model). Mode affects only synthesis/deliverable framing.
`sales_enablement` exits the trigger enum entirely: it is an `AnalysisMode`,
never a trigger, and has no row in lens-executor's priority table.

### 3. The "Sales enablement" answer maps to a trigger + mode pair (decision b2)

The Q1 answer "Sales enablement / preparing positioning" (and the matching
"sales team needs..." row in context-analyst's Context Detection Heuristics)
maps to **`trigger: feature_decision` + auto-set
`analysis_mode: sales_enablement`**. The auto-set only flips Q3's
recommended/default option to Sales Enablement; Q3 is still asked, and the
user's explicit Q3 answer always wins over the auto-set. This preserves
today's exact lens routing (JTBD+Value primary) and the user persona path.

### 4. Optional `analysis_mode` dispatch field (decision c)

The dispatch fields gain an optional `analysis_mode` field
(`strategic_planning|sales_enablement`, default `strategic_planning`).
Additive and backward compatible; lets a run that asks nothing produce
positioning-framed deliverables. An unrecognized `analysis_mode` value falls
back to the default with a context-summary `warnings` entry — it never aborts
the run.

### 5. `mode` → `analysis_mode` rename, scoped to internal carriers (decision d)

The analysis-mode carrier key renames `mode` → `analysis_mode` in **internal
carriers only**:

- `context-config.json` (context-analyst writer + all agent readers) — the
  sole live carrier
- the context/synthesis summary templates' `{mode}` placeholders
- the metadata chain: `schemas/metadata.json` and the deliverable-generator's
  session-metadata.json / metadata.json templates
- the Python reference models (`phase_01_context_discovery.py`,
  `workflow_engine.py`)
- the old state.json reference example of the full-run workflow
  (doc-consistency only — session.json is not a live carrier of the
  analysis mode)

**Exemptions — `mode` keys that do NOT rename:**

1. **The published ci-swot-v1 `mode` key.** Renaming would break a published
   schema. The key lives in synthesizer.md's swot-analysis.json output
   template (the test anchor); `schemas/swot-analysis.json` has no `mode`
   property to pin. No dispatch-mode key coexists in that artifact.
2. **Run `mode`** (`interactive|automated`) — session.json
   top-level `mode`, and the deliverable-generator
   session-metadata `mode` from the dispatch fields. Untouched everywhere.

**Internal-vs-published classification:** `schemas/metadata.json` is
**internal** — it is absent from the output table of the README, and
unlike ci-swot-v1 there is no downstream consumer evidence, so its
`analysis_context.mode` key renames to `analysis_context.analysis_mode`.
The **ci-swot-v1** SWOT artifact is **published** (declared for downstream
consumers), so its `mode` key is left unchanged.

---

## Consequences

### Becomes easier

- **One taxonomy** — agents, SKILL.md, schemas, and the Python reference
  models all carry the same 4 trigger values and 2 analysis-mode values;
  doc-contract tests (`tests/unit/test_trigger_contract.py`) pin the set
  cross-file.
- **No `mode` overload in internal carriers** — `analysis_mode` is
  unambiguous next to dispatch-mode `mode`, so readers of
  context-config.json and the metadata chain cannot confuse the two.
- **Positioning-framed runs that ask nothing** — a run that a coach starts can
  set `analysis_mode: sales_enablement` without changing lens routing.

### Becomes harder

- **Two named exemptions must be remembered** — the published ci-swot-v1
  `mode` key and the run `mode` key keep their names; any future
  sweep renaming `mode` keys must honor both (enforced by
  `test_swot_template_keeps_published_mode_key` for ci-swot-v1).
- **Old value strings are invalid** — a dispatch that still sends
  `feature_validation` / `competitive_response` / `continuous_monitoring`
  does not match the canonical enum; the trigger enum was already canonical in
  the prose before F67, so no published contract changed.

---

## Status History

| Date | Status | Notes |
|------|--------|-------|
| 2026-06-12 | Accepted | F67 taxonomy reconciliation recorded (v1.5.0); ADR-001 Decision 6 trigger taxonomy line aligned in lockstep |
| 2026-11-05 | Accepted | 1.7.0 port: the skills ask the questions and give the answers to the agents as dispatch fields; the taxonomy does not change |
