# ADR-002: Delegation to the Anthropic knowledge-worker plugins

**Status:** Accepted
**Date:** 2026-03-05
**Updated:** 2026-11-05 (port to this marketplace: optional tools, the `Skill` tool)

---

## Context

Anthropic published a set of knowledge-worker plugins for Claude Code. They include `sales`, `marketing`, `data`, `customer-support`, and `enterprise-search`. Several of their skills do work that the gtm agents also did:

- `marketing:draft-content` drafts content. The marketing agent also drafted it.
- `marketing:performance-report` writes a performance report. The funnel agent also wrote one.
- `sales:call-prep` prepares a call. The sales agent also researched the account.
- `sales:battlecard` writes a battlecard. The sales agent also wrote one.
- `sales:prospect-research` searches for prospects. The sales agent also searched with Apollo.
- `data:write-query` and `data:data-exploration` run SQL and data analysis. The funnel agent only estimated in words.

This ADR says how gtm responds.

The reference analysis of the source plugin is not in this repository.

---

## Decision 1: Delegate commodity work, keep the integrity gate

gtm does not compete with these plugins on generic work. It uses this pattern:

- **Delegate.** An agent calls a skill of the other plugin for content drafts, call prep, SQL, and report text.
- **Gate.** The integrity agent scores all output, also the output of the other plugin, before delivery.
- **Own.** gtm keeps the strategy, the evidence, and the integrity layers.

```
value-ip, competitive-intelligence, jtbd-market-discovery, pricing   (optional evidence)
    -> plugin_integrator.py reads the graphs of jtbd-market-discovery and competitive-intelligence, and finds the files of the others
gtm   (strategy, wave order, integrity engine)
    -> calls a skill of an Anthropic plugin for commodity work, when the plugin is in the session
Anthropic plugins: sales, marketing, data, enterprise-search, customer-support   (optional)
    -> the integrity agent scores all output before delivery
```

### Reasons

- The defensible part of gtm is the integrity engine, not content production.
- The same drafting steps in two plugins cost maintenance and give no advantage.
- The Anthropic plugins have more CRM connectors than gtm.

### How a delegation works in this marketplace

The four agents `knowledge-agent`, `marketing-agent`, `sales-agent`, and `funnel-agent` have the `Skill` tool. An agent checks if the skill of the other plugin is in the session. If it is, the agent calls the skill. If it is not, the agent uses its own short path, and its output names the plugin as an option. The agent never asks the person to install a plugin, because a subagent cannot ask. No agent has `AskUserQuestion`.

An optional plugin reads the data that the agent gives it. For example, the sales agent gives account and deal data.

---

## Decision 2: Thin the steps that another plugin does better

| Agent | Thinned step | Delegate to | Fallback |
|---|---|---|---|
| `marketing-agent` | Content drafts | `marketing:draft-content` | A short draft by the agent |
| `marketing-agent` | Performance report text | `marketing:performance-report` | A short summary step |
| `sales-agent` | Call prep | `sales:call-prep` | A short research step |
| `sales-agent` | Battlecard | `sales:battlecard` | `competitive-intelligence:respond` |
| `sales-agent` | Prospect search | `sales:prospect-research` | A direct Apollo call, or the ICP criteria for a manual search |
| `funnel-agent` | SQL cohort analysis | `data:write-query` and `data:data-exploration` | An estimate in words |

One step is removed with no fallback: CRM activity logging. The Anthropic `sales` plugin has CRM write connectors. gtm reads HubSpot only.

### Consequences

- The sales agent starts at MEDDPICC qualification, after call prep and prospect search.
- The marketing agent owns the strategy and the briefs. The Anthropic plugin owns the copy.
- The funnel agent owns the bottleneck diagnosis and the revenue math. The `data` plugin owns the raw analysis.

---

## Decision 3: Four integration hooks

**Hook 1: `enterprise-search` in `knowledge-agent`.** Before the agent asks for a file, it checks for the plugin. It uses the plugin to find playbooks, call transcripts, win and loss notes, and case studies. When the plugin is missing or finds nothing, the agent reads only the files that the dispatch fields name.

**Hook 2: `customer-support` in `knowledge-agent`.** When the plugin is in the session, the agent reads churn-tagged ticket summaries as field input. A claim from a support ticket gets a floor of Tier 3, because no verified call is on record.

**Hook 3: `data` in `funnel-agent`.** For cohort analysis, trend data, or SQL funnel reports, the agent calls `data:write-query` and `data:data-exploration`. It reads the result for the diagnosis and the revenue math.

**Hook 4: `/gtm:audit` as an integrity wrapper.** The audit works on any marketing or sales file, also a file that another plugin wrote. The README describes the pattern.

`plugin_integrator.py` keeps the detection patterns for the files of `customer-support` and `data`.

---

## Rejected: Rebuild gtm as a layer that needs the Anthropic plugins

Rejected for these reasons:

- A person without those plugins would lose capability with no way forward.
- It makes a hard dependency on plugins that gtm does not control.
- The brand, MEDDPICC, and SPIN work of gtm is not in those plugins.

Chosen instead: soft delegation with a fallback. The other plugins are optional.

## Rejected: Ignore the Anthropic plugins

Rejected for these reasons:

- Two plugins would do the same work, and a person would not know which to use.
- It spends maintenance on generic work that Anthropic improves faster.

---

## Summary

| Layer | gtm owns | Delegated |
|---|---|---|
| Intelligence | Plugin evidence, field intelligence, codebase scan | Enterprise search, churn signal summaries |
| Strategy | Brand identity, PMF gate, MQL seed, wave order, SAL design, MEDDPICC | None |
| Execution | SPIN sequences, Challenger pitch outline, the integrity gate on all output | Content drafts, call prep, battlecards, prospect search, SQL analysis, report text |
| Integrity | Truth Tier on all output | None |
