---
description: Answer a question about the domain model from the ddd bundle only. Reads the root index, one context, one page, and links.tsv, in that order, and cites each page it used. Use for "what does X mean in context Y", "which contexts use X", "what emits OrderPlaced", and before a change to a domain boundary.
argument-hint: "<question>"
allowed-tools: Read, Grep, Glob, Bash
---

# Ask: answer from the domain bundle

This skill writes no page. It reads the bundle in the read order of
`${CLAUDE_PLUGIN_ROOT}/skills/shared/bundle-schema.md`, and stops when it has the answer.
Bash is only for the `regen --check`, `regen`, and `check` commands of Step 2.

## Step 1: find the bundle

Read `.claude/ddd.json`. If the file does not exist, tell the user: "This repository has no
domain bundle. Run `/business-domain:setup` first." Then stop. The `dir` value is `<dir>` below.

## Step 2: the drift check

Run this command first, before you read a page:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py regen --check

If `uv` is not installed, run `python3` with the same path.

- Exit 0: the generated parts agree with the frontmatter. Go to Step 3.
- Exit 1: each `STALE:` line names one generated part that does not agree with the
  frontmatter. An edit outside Claude Code caused it. Run these two commands:

      uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py regen
      uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py check

  Tell the user each generated part that `regen` rewrote. If `regen` gives an exit code that
  is not 0, stop and show the output. If `check` gives exit code 1, show each `ERROR:` line,
  and say that the answer can use a page with a broken edge. Then go to Step 3.
- Exit 2: stop. Show the output.

## Step 3: read in order

Each Read of one file counts as one read. The limit is 8 reads. A Grep does not count.

1. Read `<dir>/index.md`. It has one line for each context.
2. Select the context of the question. Read its page, `<dir>/contexts/<ID>.md`. Its `LINKS`
   block lists the terms, aggregates, events, and relationships of the context, each with its
   title.
3. If the answer needs more, Read one page from that `LINKS` block. The frontmatter gives the
   stored edges. The `LINKS` block gives the reverse edges.
4. For a question about the full graph, as in "which contexts consume `OrderPlaced`?", get the
   ID from the type index, then Grep `<dir>/links.tsv` for the ID. Do not read each page,
   because `links.tsv` holds each edge in one file.
5. To find a name, Grep the type indexes, `<dir>/*/index.md`, and ignore letter case. A name
   can also be in `aliases`: Grep `<dir>` for `^aliases:.*<name>` with the glob `*.md`.

After 8 reads, stop reading. Say which pages you read, and that the bundle did not give the
answer in 8 reads.

## Step 4: answer

- Cite each page that you used by its path, as in `<dir>/terms/TERM-01.md`.
- Put "(draft)" after each cited page that has `status: draft`. A person accepted the page,
  but it is not settled.
- A page with `status: deprecated` is not an answer. Find the page that has its ID in
  `aliases`, and use that page.
- If the bundle does not hold the answer, say so. Do not answer from outside the bundle.
  The reason: the user reads the answer as the recorded model of this repository. Tell
  the user how to add the knowledge: run
  `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ddd.py new <Type> --title <title> --description <description>`,
  or edit a page.

## The rest of the question

When the read order above does not answer the question, load the
`knowledge:ask` skill. Give it the question and the start nodes that you
found, as `ddd:/<folder>/<ID>.md` (or `ddd:/index.md`). It walks every graph
one step at a time.
