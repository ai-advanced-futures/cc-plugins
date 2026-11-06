# ADR-003 — Phase 1 Insight Workflow (new agentic-pricing-strategist agent)

| | |
|---|---|
| Status | Accepted |
| Date | 2026-05-19 |
| Deciders | pricing-core sub-spec 1 |
| Context source | JustKeenAI Agentic Pricing Framework v2.1 — Chapter 6 (5-phase engagement structure) |

## Context

Pricing v1.3.0 ships two agents: `new-offering-pricer` (single-feature, future-feature pricing) and `pricing-auditor` (legacy portfolio audit). The JustKeenAI framework introduces a third workflow shape — "Phase 1 Insight" — that diagnoses an entire portco's agentic offering portfolio rather than pricing a single feature or auditing existing prices.

The Phase 1 Insight diagnostic orchestrates 4 distinct skills (cost-amplifier-diagnostic, value-metric-tree-walk, pattern-selection-agentic, sensitivity-stress) producing 3 Charter handoff schemas + a composed strategy report. This is a heavier, multi-skill workflow that doesn't fit either existing agent's shape.

Naming collision: all three agents could write one shared result file. A reader needs a way to tell which agent wrote it, so each agent writes its own file name.

## Decision

**Introduce a third agent: `agentic-pricing-strategist`** at `plugins/pricing/agents/agentic-pricing-strategist.md`. The agent:

1. Orchestrates the 4 Phase 1 skills in canonical order.
2. Composes the final `agentic-pricing-strategy.md` report.
3. Writes its own files in `.pricing/`, so no other agent writes the same file.

**One file name for each agent** is the rule that replaces a shared file. A reader knows which pricing agent wrote a file from its name.

**Flat skills/ layout** (one skill per directory, peer to existing pricing skills) is preserved. No nesting beneath `skills/phase-1/` — keeps grep-ability and aligns with the rest of the plugin's structure.

**audience: mixed** for the agent and the customer-facing-output skills (T12, T13); **audience: internal** for diagnostic-only skills (T11 cost-amplifier-diagnostic, T14 sensitivity-stress). The vocabulary linter enforces the boundary.

## Consequences

- Three agents coexist in `plugins/pricing/agents/`. Cross-discrimination is solved by the `agent` field, not by file-path conventions.
- The Phase 1 Insight workflow is dispatch-addressable as `agentic-pricing-strategist`.
- The orchestration logic stays in the agent prose, not in Python. The 4 skills are independently dispatchable — a user can run `Skill(cost-amplifier-diagnostic)` standalone without invoking the strategist.
- Future Phase 2-5 framework phases (Pricing Strategy, Customer Activation, Realization, Multiple Compression Defense) may add additional agents following the same `agent`-discriminator pattern.

## Cross-references

- Implementation: `plugins/pricing/agents/agentic-pricing-strategist.md` (T15)
- Unit structure test: `plugins/pricing/tests/unit/test_agentic_pricing_strategist_structure.py` (T15)
- Integration contract test: `plugins/pricing/tests/integration/test_agentic_pricing_strategist.py` (T16)
- Skills: `plugins/pricing/skills/{cost-amplifier-diagnostic,value-metric-tree-walk,pattern-selection-agentic,sensitivity-stress}/` (T11-T14)
