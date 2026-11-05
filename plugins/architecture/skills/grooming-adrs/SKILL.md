---
name: grooming-adrs
description: Grooms the ADR corpus -- merges overlapping records, retires ADRs reality has outgrown, compresses bloated prose in place, and archives the dead. Use for "/architecture:groom", "the ADR corpus is rotting", "merge these ADRs", "these two ADRs say the same thing", "archive the dead ADRs", "clean up the ADR corpus". Invoked by a human. Always proposes a plan and shows a diff first; never rewrites silently.
argument-hint: "[job]"
allowed-tools: Bash, Read, Grep, Glob, Write, Edit, AskUserQuestion
---

# grooming-adrs

Grooming is invoked by a human -- it rewrites a corpus, so it does not fire on its own the way
capture and recall do. Each job proposes a plan and shows a diff first, and it never rewrites
before the person confirms, because the corpus holds decisions that other people wrote.
`$ARGUMENTS` selects a job by name (`merge`, `retire`, `compress`, `archive`); with no argument,
ask which job to run.

## Job 1 -- merge overlapping ADRs

Several records circling one decision collapse into one. Read the corpus, find ADRs that make the
same decision or two halves of one decision, and propose which one survives. Show the merged
text as a diff before you write it. The originals become `status: superseded` and set
`superseded_by` to point at the survivor; the survivor sets `supersedes` to list them -- so old
links still resolve and no supersede is one-sided.

## Job 2 -- retire what reality outgrew

This job reads code, not just the corpus. Flag ADRs the code no longer reflects, and `accepted`
ADRs that contradict each other. Propose `status: deprecated` (nothing replaces the decision) or
`status: superseded` (something does, and a new ADR names it) for each one. Show the diff before
you write it.

## Job 3 -- compress prose in place

Rewrite bloated ADRs to the distillation standard. Read
`${CLAUDE_PLUGIN_ROOT}/skills/learn/distillation.md` and apply it: drop the design-journal
voice, fold appended `## Update:` blocks into the decision, and lose no meaning. Show the diff
before you write it.

## Job 4 -- archive the dead

Move `superseded` and `deprecated` records into `{{DIR}}/archive/` (the corpus's own `archive/`
subdirectory) and set `archive_dir` in `.claude/adr.json` the first time this job archives
anything. **On-disk layout is flat by default and nothing moves unless this job is invoked.**

Before moving a record, resolve every inbound target and preserve any `#fragment`:

| Author location | Before | After |
|---|---|---|
| live ADR | `target.md` | `archive/target.md` |
| live ADR | `./target.md#decision` | `archive/target.md#decision` |
| archived ADR | `../target.md` | `target.md` |
| register summary Markdown | `(./target.md#decision)` | `(./archive/target.md#decision)` |

Apply the path-aware replacement to every inbound link: `supersedes`, `superseded_by`, `amends`,
`amended_by`, `refines`, `deviates_from`, `related`, and hand-written Markdown links. For
frontmatter lists, use `adr_lib.rename_list_item`, because a global replace of a basename also
changes text that only mentions the name. Resolve each
path relative to the authored ADR, retain its `#fragment` and inline comment, then move the target to
`{{DIR}}/archive/<filename>`.

Before regenerating the live register, copy the moved row's hand summary into
`archive/README.md` under a filename-keyed bullet. Keep an existing `archive/README.md` and its
prose. The index writer in the close step removes the live row.

## Close every groom job

Show the plan and the diff, get confirmation, then write. After any move or rewrite, run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_index.py" --write
python3 "${CLAUDE_PLUGIN_ROOT}/templates/verbatim/scripts/adr_lint.py"
```

The job is done only when the lint exits 0. When it exits non-zero, report the job as failed
and name each error.
