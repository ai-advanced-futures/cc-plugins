---
description: Answer a question about the domain model from the ddd bundle only. Uses the shared local evidence reader, checks aliases and status, and cites each page. Use for "what does X mean in context Y", "which contexts use X", "what emits OrderPlaced", and before a change to a domain boundary.
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, Skill(knowledge:ask), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py regen --check), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py regen --check)
---

# Ask: answer from the domain bundle

The question is: **$ARGUMENTS**

This skill writes no page or generated file. Answer from the domain bundle only.

## Find the bundle and check drift

Read `.claude/ddd.json`. If the file does not exist, tell the user: "This repository has no
domain bundle. Run `/business-domain:setup` first." Then stop. Its `dir` is `<dir>`.

Before a page read or shared search, run the read-only drift check:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py regen --check

If `uv` is not installed, run `python3` with the same path.

- Exit 0: continue to the normal reader or exact query.
- Exit 1: show each `STALE:` line. Stop this lookup because generated edges can give a wrong
  answer. Repair is a separate action that writes files, not part of this read-only ask.
  Offer the existing repair commands below for explicit approval, then rerun the ask.
- Exit 2 or another error: stop and show the output.

Separate repair commands, only after approval outside this lookup:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py regen
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py check

Use `python3` if `uv` is absent. Report the files that repair rewrites and each `ERROR:`
line. A failed repair is not a successful lookup. Version 2.0 stops on drift instead
of silently regenerating the graph; repair remains available as an explicit write.

## Normal questions

Load `knowledge:ask` with the question unchanged before reading the root index,
context, or term page. Requires knowledge 2.0.0 or later. The shared reader searches
local registered graphs; it accepts no caller-selected nodes or filters. A graph word
in the question is a search term, not an enforced filter. Keep only evidence inside
`<dir>` and check the selected source pages for context, aliases, and status before
answering, because the answer must represent the recorded domain model.

If `ddd` is unregistered or remote, or its local evidence does not resolve the name,
use the local read order below. Report the coverage gap instead of treating a search
miss as proof that the domain model is silent.

## Exact queries and unresolved names

For a complete list or typed relation, use the type index and `<dir>/links.tsv` instead
of ranked search. Resolve the ID first and match the relation key and direction in
that edge file, because it holds the full relation set in one place. For names, search `<dir>/*/index.md` and `aliases` in the source pages,
including multiline alias lists.

Put a search term in single quotes, and write each `'` in the term as `'\''`
(or use a term with no `'`), because the shell reads the rest of the term as part
of the command.

When direct reading is necessary, follow the read order of
`${CLAUDE_PLUGIN_ROOT}/skills/shared/bundle-schema.md`:

1. Read `<dir>/index.md` to select a context.
2. Read `<dir>/contexts/<ID>.md` for its terms, aggregates, events, and relationships.
3. Read only the matching page. Its frontmatter holds stored edges; its LINKS block
   holds reverse edges.
4. For full-graph relations, search `<dir>/links.tsv` with the resolved ID.

The limit is 8 reads of bundle pages in this lookup. After 8 reads, state what remains
unanswered and which pages you read.

## Answer

- Cite each page by its path, for example `<dir>/terms/TERM-01.md`.
- Put "(draft)" after each cited page with `status: draft`.
- A page with `status: deprecated` is not an answer. Find the replacement with the old
  ID in `aliases`, check its context, and use that page. Report a missing replacement.
- If the bundle does not hold the answer, say so. Do not answer from outside the bundle,
  because the reader needs the recorded domain model. To add knowledge, suggest
  `/business-domain:learn` as a separate approved write.
