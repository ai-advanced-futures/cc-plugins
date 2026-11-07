---
description: Answers a question about the product from the PRD and roadmap bundles - what the product is, which capability serves a need, what is in scope, what work traces a capability, and what is ready or blocked - and follows links into the other graphs. Use for "/product:ask", "what does the PRD say about X", and "which stories trace capability X".
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, Agent, Skill, Bash
---

# Ask the product

The question is: **$ARGUMENTS**

Answer from the bundles only. Never write a page, because the other product skills own each write to the bundles.

`P` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py --root "$(git rev-parse --show-toplevel)"`.

## Step 0: the guard

When `docs/product/prd/index.md` does not exist, stop with: "This repository
has no PRD bundle. Run `/product:setup` first." When a v3 PRD file is present in
`docs/product/` instead, say: "Run `/product:migrate` first."

## Step 1: the shortcuts

Use the first shortcut that fits. Each one gives start nodes.

| Question | Shortcut |
|---|---|
| A broad question: what the product is, for whom, and why | Start at `docs/product/prd/product.md` (`prd:/product.md`). |
| A capability by name | Search `docs/product/prd/capabilities/index.md` with `grep -i`, then the `aliases` of the capability pages. |
| The PRD reason of a roadmap item | Read the `traces` of the item: each entry names `prd:/<path>`. |
| The work state: ready, blocked, in progress | `prd.py list`: `$P list <Type> --where state=<state> --fields title,state`. |
| What traces a capability | Read the LINKS block of the capability: "traced by" lines. |

Put a search term in single quotes, and write each `'` in the term as `'\''` (or use a term with no `'`), because the shell reads the rest of the term as part of the command.

## Step 2: the generic procedure

Load the `knowledge:ask` skill. Give it the question and the start nodes of
Step 1 (`prd:/index.md` or `roadmap:/index.md` when no shortcut fits). It
walks the graphs one step at a time, also into the system design and the
ADRs.

## Step 3: answer

Cite each page with its graph and path, for example
`(prd:/capabilities/CAPABILITY-03.md)`. Write `(draft)` after each draft page.
