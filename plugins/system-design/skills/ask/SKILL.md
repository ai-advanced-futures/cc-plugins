---
description: Answers a question about the system design from the system-design graph - which component realizes a capability, which interface two components use, which scenarios constrain a component, and why the design is this way - and follows links into the PRD, ADR, and domain graphs. Use for "/system-design:ask", "which component does X", and before a change to a component boundary.
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, Agent, Skill, Bash(uv run *), Bash(git rev-parse *)
---

# Ask the system design

The question is: **$ARGUMENTS**

Never write a page, because the person makes each design change through the
`system-design:learn` skill. Answer from the graphs only.

`K` is `uv run <knowledge plugin>/scripts/knowledge.py --root "$(git rev-parse --show-toplevel)"`.
Find the knowledge plugin with
`bash ${CLAUDE_PLUGIN_ROOT}/scripts/probe-plugin.sh knowledge scripts/knowledge.py`.
When the probe exits 1, stop with: "system-design:ask needs the knowledge
plugin. Install it: claude plugin install knowledge@cc-plugins."

## Step 1: the shortcuts

Use the first shortcut that fits the question. Each one gives start nodes.

| Question | Shortcut |
|---|---|
| Which component realizes capability X? | `$K pages system-design --type Component`. Keep each page whose `realizes` holds `prd:/capabilities/<X>.md`. |
| Which interface do A and B use? | Read the `uses` entries of A. The `via` of the entry to B is the interface. |
| Which scenarios constrain component A? | `$K neighbors system-design:/components/<A>.md`. Keep the `in` rows of type QualityScenario. |
| Why is the design this way? | Read the DECISION-INDEX block of `system.md` and the `decisions` of the area. |
| Is this decision still in force? | `$K show adr:/<file>`. Read `lifecycle`. The design never copies it. |
| Where does component A run? | Read `deployed_to` of A, then the DeploymentNode pages. |

## Step 2: the generic procedure

Load the `knowledge:ask` skill. Give it the question and the start nodes of
Step 1 (or `system-design:/index.md` when no shortcut fits). It walks the
graphs one step at a time, also into the PRD, ADR, and domain graphs.

## Step 3: answer

Cite each page with its graph and path, for example
`(system-design:/components/COMPONENT-03.md)`. Write `(draft)` after each
draft page. Give the lifecycle of each ADR that the answer uses.
