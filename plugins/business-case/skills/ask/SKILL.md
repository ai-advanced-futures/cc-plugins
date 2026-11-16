---
description: Answers a question about a business case from the business-case graph - what a part of a case says, which evidence a part rests on, what the latest review found, and what the funder decided - and follows links into the jtbd and competitive-intelligence graphs. Use for "/business-case:ask" and "what does the case say about X".
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, Skill(knowledge:ask), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/bc_graph.py --root * select *), Bash(git rev-parse *)
---

# Ask the business cases

The question is: **$ARGUMENTS**

Never write a page, because the pages of a case come from its case folder through
`/business-case:build`, and the person confirms them through `business-case:learn`.
Answer from the graphs only.

## Normal questions

Load `knowledge:ask` with the question unchanged before reading Case pages or probing
plugins. Requires knowledge 2.0.0 or later. This is the normal evidence reader.
It searches local registered graphs and accepts no caller-selected nodes or filters.
A case name or graph name in the question does not enforce selection. Validate case
and part evidence below before using it; do not copy a different case's answer.
When the graph is unregistered or remote, read its local source files when available
and report the coverage gap.

## Case and part checks

When the question names a case, offering, or part, validate that scope with the local
query. For a complete list, latest review, open items, or funding decision, use the
matching exact check instead of ranked search. Otherwise run only the check needed
to validate the shared reader's evidence.

Run `git rev-parse --show-toplevel` on its own. Its output is `<git root>`. When it
fails, stop with: "This is not a git repository." Use the literal root path in commands.
Run each command on its own: one command per Bash call, with no pipe (`|`), no `;` and no `&&`.
Quote paths and values with single quotes, escaping each `'` as `'\''`.
`uv run ${CLAUDE_PLUGIN_ROOT}/scripts/bc_graph.py --root '<git root>' select --case '<slug, offering, or CASE ID>'` returns one exact Case and its parts.
If the case is ambiguous, ask for a unique slug or CASE ID, because rank cannot resolve case identity.
For a part question, add `--part <part>`. The value is the part of the question: `job`,
`market`, `competition`, `price`, `gtm`, `finance`, `baseline`, or `strategy`. The query
keeps only type Part pages whose `case` edge targets that Case and whose `part` matches.
Read only those parts as the answer's case evidence. No matching part is a gap.

| Question | Exact check |
|---|---|
| What does a part of a case say? | `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/bc_graph.py --root '<git root>' select --case '<case>' --part <part>`. Use the returned source body and status. |
| Which sources does a part rest on? | Follow the selected Part's `evidence` links, then each Evidence page's `source_results` links into the `jtbd` and `competitive-intelligence` graphs. Verify each Evidence page belongs to the same case. |
| What did the latest review find? | Read the Case's `latest_review` link. Verify the Review has the same `case` and the highest `report` among that case's Review pages. Read its ItemVerdict and Finding pages. |
| Which items are still open? | Read all OpenItem pages linked to that Case and their `state`, because ranked search can omit open items. |
| What did the funder decide? | Read the Case's `funding_decision` link and check the target's case and recorded decision. |

The bundle path is the `business-case` entry in `.claude/knowledge.json`. Use source
frontmatter for validation, not a generic neighbour hint. For an unnamed case-specific
question, use the evidence to identify a unique Case, then validate it with `select`;
ask which case when more than one fits.

## Answer

Cite each page with its graph and path, for example
`(business-case:/parts/PART-07.md)`. Write `(draft)` after each draft source.
Keep case facts separate from linked market evidence. State missing parts, sources,
or reviews instead of filling gaps with evidence from another case.
