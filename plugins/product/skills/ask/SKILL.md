---
description: Answers a question about the product from the PRD and roadmap bundles - what the product is, which capability serves a need, what is in scope, what work traces a capability, and what is ready or blocked - and follows links into the other graphs. Use for "/product:ask", "what does the PRD say about X", and "which stories trace capability X".
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, Skill, Bash
---

# Ask the product

The question is: **$ARGUMENTS**

Answer from the bundles only. Never write a page, because the other product skills own each write to the bundles.

## Guard

When `docs/product/prd/index.md` does not exist, stop with: "This repository
has no PRD bundle. Run `/product:setup` first." When a v3 PRD file is present in
`docs/product/` instead, say: "Run `/product:migrate` first."

## Normal questions

Load `knowledge:ask` with the question unchanged before reading `product.md`,
the capability index, or roadmap pages. This is the normal evidence reader.
Requires knowledge 2.0.0 or later. The reader searches local registered graphs only.
It takes a question, not caller-selected nodes or filters. A graph name in the question
is a search term, not an enforced filter. Use product bundle evidence; use linked sources
only when they state a fact or condition that the question asks for. If a required bundle is unregistered or remote, read its local source
files directly when available and report the limit; a search miss is not proof of absence.

## Exact questions

For complete lists, work state, or trace coverage, use the matching local query instead
of ranked search. For other questions, use these checks only when the returned evidence
leaves that part unanswered. Run only the matching query.

`P` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py --root "$(git rev-parse --show-toplevel)"`.

| Question | Exact check |
|---|---|
| A capability by name when the search is unresolved | Search `docs/product/prd/capabilities/index.md` with `grep -i`, then the `aliases` of the capability pages. |
| The PRD reason of a roadmap item | Read the `traces` of the item: each entry names `prd:/<path>`. |
| The work state: ready, blocked, in progress | `prd.py list`: `$P list <Type> --where state=<state> --fields title,state`. |
| What traces a capability | Read the LINKS block of the capability: "traced by" lines. Check all matching trace edges, not only search hits. |
| What the product is, for whom, and why, when evidence is incomplete | Read the section of `docs/product/prd/product.md` that states the product, audience, or need. |

Put a search term in single quotes, and write each `'` in the term as `'\''`
(or use a term with no `'`), because the shell reads the rest of the term as part
of the command.

## Answer

Cite each page with its graph and path, for example
`(prd:/capabilities/CAPABILITY-03.md)`. Write `(draft)` after each draft page.
State gaps instead of treating a ranked result as a complete list.
