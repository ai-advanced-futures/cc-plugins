---
name: amending-adrs
description: Changes a recorded decision when it changes -- rewrites the ADR in place, deprecates it, or supersedes it with correct back-links on both sides. Use for "the decision changed", "deprecate this ADR", "supersede ADR N", "we no longer do X", and fires on its own when a session changes a decision an existing ADR records.
allowed-tools: Bash, Read, Grep, Glob, Write, Edit
---

# amending-adrs

A recorded decision just changed. Update the corpus to match. There is no command for this skill
-- it is reached by the model on its own, or from `architecture:learn` when writing a new ADR requires
retiring an old one.

Rewrite in place and never append an `## Update` block, because git holds the history. Apply
`${CLAUDE_PLUGIN_ROOT}/skills/learn/distillation.md` to every rewrite.

Read `.claude/adr.json`. If `rules` names a file, read that repository-root-relative Markdown
file and apply it as additional instructions after this shipped procedure. Stop with the missing
path when the configured file cannot be read.

When the active schema has a `description` property, write one `description` line of 30 words or
fewer in the words of the task, and pass it with `--description`. On a rewrite in place, edit the
line in the front matter. The line tells a reader when to open the ADR, so it adds to the title
and does not repeat it.

## Eight forms

| Form | Textual frontmatter changes |
|---|---|
| Rewrite in place | Rewrite the body; set `amended: <today>`; keep status. |
| Deprecate | Set `status: deprecated`; set `amended: <today>`. |
| Full supersede | Old: `status: superseded`, append new filename to `superseded_by`; new: append old filename to `supersedes`. |
| Partial supersede | Keep both statuses; append the reciprocal items with `# partial — <scope>` on both sides. |
| Amend by sibling | New: append old filename to `amends`; old: append new filename to `amended_by`; statuses stay. |
| Refine | Append the target filename to `refines`; no reciprocal field. |
| Deviate | Append the target filename to `deviates_from`; no reciprocal field. |
| Archive | Move only deprecated or superseded ADRs to `archive/` through the grooming procedure. |

For a full or partial supersede, write the new ADR first with `architecture:learn`. Set both sides;
one-sided supersession is a lint error. Cross-references hold filenames, never a number, because
the filename is the identity.

Change only the frontmatter lines for the named keys. Keep every other key, the key order, the
scalar spelling, and each inline comment, because a full re-serialization of the block loses them.

## Close every amend

Run both gates and report their output:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_index.py --write
python3 ${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_lint.py
```

The amend is done only when the lint exits 0. When it exits non-zero, report the amend as
failed and name each error.
