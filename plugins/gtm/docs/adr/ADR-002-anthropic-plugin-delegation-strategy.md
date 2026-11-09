# ADR-002: Delegation to the Anthropic knowledge-worker plugins

**Status:** Accepted
**Date:** 2026-03-05
**Updated:** 2026-11-05 (port to this marketplace: optional tools, the `Skill` tool)
**Updated:** 2026-11-07 (STORY-146: no agent has the `Skill` tool; `/gtm:run` calls 2 skills, and the agents name the other plugins as options)

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

- **Delegate.** The command `/gtm:run` calls a skill of the other plugin for the knowledge search and the churn signals. For content drafts, call prep, SQL, and report text, the agent uses its own short path and names the other plugin as an option.
- **Gate.** The integrity agent scores all output, also the output of the other plugin, before delivery.
- **Own.** gtm keeps the strategy, the evidence, and the integrity layers.

```
value-ip, competitive-intelligence, jtbd-market-discovery, pricing   (optional evidence)
    -> plugin_integrator.py reads the graphs of jtbd-market-discovery and competitive-intelligence, and finds the files of the others
gtm   (strategy, wave order, integrity engine)
    -> /gtm:run calls 2 skills of an Anthropic plugin, when the plugin is in the session; the agents name the others as options
Anthropic plugins: sales, marketing, data, enterprise-search, customer-support   (optional)
    -> the integrity agent scores all output before delivery
```

### Reasons

- The defensible part of gtm is the integrity engine, not content production.
- The same drafting steps in two plugins cost maintenance and give no advantage.
- The Anthropic plugins have more CRM connectors than gtm.

### How a delegation works in this marketplace

No agent has the `Skill` tool, because no documented form limits `Skill` to named skills in a subagent. The command `/gtm:run` checks if the skills `enterprise-search` and `customer-support` are in the session. For each one that is, the command calls the skill before it starts `knowledge-agent`, writes the answer to `.gtm/working/knowledge/enterprise-search.md` or `.gtm/working/knowledge/customer-support.md`, and gives the paths to the agent as `skill_outputs`. The agent reads them as data. The 7 other calls (`marketing:draft-content`, `marketing:performance-report`, `sales:call-prep`, `sales:battlecard`, `sales:prospect-research`, `data:write-query` and `data:data-exploration`) are removed. Each agent uses its own short path, and its output names the plugin as an option. The agent never asks the person to install a plugin, because a subagent cannot ask. No agent has `AskUserQuestion`.

An optional plugin reads the request that `/gtm:run` gives it.

---

## Decision 2: Thin the steps that another plugin does better

| Agent | Thinned step | Named as an option | Path of the agent |
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

**Hook 1: `enterprise-search` for `knowledge-agent`.** Before `/gtm:run` starts the agent, it checks for the plugin. It uses the plugin to find playbooks, call transcripts, win and loss notes, and case studies, and gives the answer to the agent as data. When the plugin is missing or finds nothing, the agent reads only the files that the dispatch fields name.

**Hook 2: `customer-support` for `knowledge-agent`.** When the plugin is in the session, `/gtm:run` gets churn-tagged ticket summaries, and the agent reads them as data. A claim from a support ticket gets a floor of Tier 3, because no verified call is on record.

**Hook 3: `data` for `funnel-agent`.** For cohort analysis, trend data, or SQL funnel reports, the agent calls no plugin. It estimates from the data in `gtm-context.json`, and its output names the `data` plugin (`data:write-query` and `data:data-exploration`) as an option.

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
