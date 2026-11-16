---
description: Answers a question about the system design from the system-design graph - which component realizes a capability, which interface two components use, which scenarios constrain a component, and why the design is this way - and follows links into the PRD, ADR, and domain graphs. Use for "/system-design:ask", "which component does X", and before a change to a component boundary.
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, Skill, Bash(uv run *), Bash(git rev-parse *), Bash(bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh *)
---

# Ask the system design

The question is: **$ARGUMENTS**

Never write a page, because the person makes each design change through the
`system-design:learn` skill. Answer from the graphs only.

## Normal questions

Load `knowledge:ask` with the question unchanged before any design page read or plugin
probe. Requires knowledge 2.0.0 or later. This is the normal evidence reader, not a
fallback. It searches local registered graphs only and accepts no caller-selected nodes
or filters. A graph name in a question does not restrict search. Use design evidence;
use linked sources only when they state a fact or condition that the question asks for. For an unregistered or remote graph, read local source
files when available and report the coverage gap.

## Exact checks

For complete sets, typed relations, deployment, or decision status, use the matching
query below instead of ranked search. Otherwise run a check only when the returned
evidence needs it. Resolve the plugin and root only when a query needs them.

`K` is `uv run <knowledge plugin>/scripts/knowledge.py --root "$(git rev-parse --show-toplevel)"`.
Find the knowledge plugin with
`bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh knowledge scripts/knowledge.py`.
When the probe exits 1, stop with: "system-design:ask needs the knowledge
plugin. Install it: claude plugin install knowledge@cc-plugins."

Use only the check that fits the question. Read each selected source page to verify its fields.

| Question | Shortcut |
|---|---|
| Which component realizes capability X? | `$K pages system-design --type Component`. Keep each page whose `realizes` holds `prd:/capabilities/<X>.md`. |
| Which interface do A and B use? | Read the `uses` entries of A. The `via` of the entry to B is the interface. |
| Which scenarios constrain component A? | `$K neighbors system-design:/components/<A>.md`. Keep the `in` rows of type QualityScenario. |
| Why is the design this way? | Read the DECISION-INDEX block of `system.md` and the `decisions` of the area. |
| Is this decision still in force? | `$K show adr:/<file>`. Read `lifecycle`. The design never copies it. |
| Where does component A run? | Read `deployed_to` of A, then the DeploymentNode pages. |

For each ADR used in an answer, check its source `lifecycle` and amendment or
supersession links. Use `architecture:ask` when the decision history needs explanation;
a ranked hit alone does not show which decision is in force.

## Answer

Cite each page with its graph and path, for example
`(system-design:/components/COMPONENT-03.md)`. Write `(draft)` after each
draft page. Give the lifecycle of each ADR that the answer uses.
