---
description: Writes one architecture decision record (ADR) the moment a decision that would be expensive to undo has just been made -- a datastore, a service or trust boundary, a wire or event contract, a deployment topology, a public interface others consume. Writes the ADR with lifecycle accepted and keeps working; it never stops to ask. Use for "/architecture:learn", "write an ADR", "record this decision", "document this architecture decision", and fires on its own during a session the moment a decision that is expensive to undo is made.
argument-hint: "[decision]"
allowed-tools: Read, Grep, Glob, Write, Edit, Skill, Bash(uv run *), Bash(git *), Bash(gh issue create *), Bash(test *)
---

# Learn

Write one ADR. Capture the decision now, then keep working on whatever the session was already
doing.

## Input and callers

Keep the existing free-text input: one decision sentence plus facts for Context, Decision,
Why, Alternatives considered, and Consequences. Existing callers, including
`architecture-assess`, need no flags or additional positional arguments. The input is
**$ARGUMENTS**.

Accept optional labeled facts `map_area: AREA`, `Parent spec: PATH`, and
`Source: PATH_OR_URL`. These facts add to the decision; they do not replace it. A map area
must be one of `quality`, `context`, `strategy`, `building-blocks`, `data`, `contracts`,
`conventions`, or `deployment`. Omit the field when no area was supplied; do not guess one
from `area`, `parent_spec`, or a source. Keep the existing free-text `area` unchanged.

Explorer supplies only confirmed firm choices. Preserve that confirmation when saving;
do not ask its interview again. Rejected and deferred findings from Explorer are not
inputs for a new accepted or proposed ADR. This rule does not change independent capture
or the existing explicit request for a proposed ADR below.

For an existing accepted decision that must change, use `architecture:amending-adrs`
instead of silently writing a replacement. When Explorer requests the change, require its
explicit replacement confirmation before proceeding. Independent capture still writes a
new decision when the decision is made and keeps working without an extra approval step.

## The bar

Record a decision when undoing it later would be expensive. Cheap to change your mind, no ADR.

| Earns an ADR | Does not |
|---|---|
| Chose Postgres over DynamoDB | Picked a retry count of 3 |
| Put auth at the gateway, not per service | Named a helper function |
| An event shape other services now consume | Chose a lodash utility |

Two rejected bars, recorded so they are not re-litigated:

- **"Escapes its module."** This bar misses expensive local choices, such as a storage engine
  inside one service. A decision does not have to cross a module boundary to be expensive to undo.
- **"Alternatives were weighed."** This bar fires constantly, because sessions weigh options all
  the time. Weighing options is not the test. The cost of reversing the choice is the test.

## When this fires on its own

The moment you make a decision that is expensive to undo -- a datastore, a service or trust
boundary, a wire or event contract, a deployment topology, a public interface others consume --
write the ADR and keep working. Do not stop to ask, because asking breaks flow. In a long or
unattended session, nobody is there to answer, and the decision gets lost.

The ADR gets `lifecycle: accepted`. The review of the pull request is the acceptance: the person
who merges the pull request accepts each ADR in it, or deletes or changes the ADR before the merge.
Write `--lifecycle proposed` only when
the person tells you that the decision is still open.

## Write it

Run `git rev-parse --show-toplevel` separately to find the repository root. Replace `ROOT`
in each command with that literal absolute path and use the expanded plugin path, because
the permission checks cannot verify shell variables or command substitutions.

Read `.claude/adr.json` first. If `rules` names a file, read that repository-root-relative
Markdown file and apply it as additional instructions after this shipped procedure. Stop with the
missing path when the configured file cannot be read.

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/adr.py --root ROOT new --title "<title>" --area "<area>"
```

Add `--parent-spec <path>` only when a parent spec exists, and `--description "<line>"` when the
active schema has a `description` property. `adr.py new` prints the path of the new file.

When the input supplies `map_area: AREA`, add `--map-area AREA` to that same `new` call.
For an accepted choice, retain `lifecycle: accepted` and a valid OKF status (`stable` by
default). A schema that lacks `map_area` or rejects its value must stop the save. Report
`/architecture:setup --refresh` or a custom schema update as the next step. Do not silently
refresh a custom schema, remove the supplied map area, or retry without it.

When the input supplies `Source: PATH_OR_URL`, record that source in the ADR body, with
its external-ADR identity when present. Preserve the source's relevant context and explain
why the choice applies here. Keep URLs in body attribution rather than `related`,
`parent_spec`, or another ADR-only relationship field, because those fields expect record
paths. An external source is not a parent spec merely because it was supplied.

When model facts are known, add `--model-status VALUE` to the same `new` call. Choose
`modeled`, `out-of-scope`, or `black-box`. Add `--model-element VALUE` and
`--model-reason VALUE` only when they explain the choice; both require `--model-status`.
Supply these facts before creation so the full schema check can validate them with the
map area. If required model facts are missing, report them and keep the record unsaved.

When durable, dated evidence exists, add `--evidence VALUE` to the same `new` call.
Repeat `--evidence` for each measurement so the full schema check receives all entries
before creation. Omit evidence when none exists; if the schema requires it, report the
missing evidence and keep the record unsaved.

When the active schema has a `description` property, write one `description` line of 30 words or
fewer in the words of the task, and pass it with `--description`. The line tells a reader when to
open the ADR, so it adds to the title and does not repeat it. The script stops with exit 2 when the
schema does not have the property.

This allocates the next identity, writes frontmatter with `lifecycle: accepted`, `status: stable`, `area`, and `model`,
and prints the new file's path. Open that file and fill in the five sections: Context, Decision,
Why, Alternatives considered, Consequences.

The filename is the identity. Never write an `id` field into the frontmatter, because a number
there can drift from the filename and nothing detects the drift. Cross-references (`supersedes`,
`superseded_by`, `related`) hold filenames, never numbers, because of the same drift.

## Style

Read `${CLAUDE_PLUGIN_ROOT}/skills/learn/distillation.md` and apply it.

## Both checks and the report

1. Call the `knowledge:checking` skill with the graph `adr`. Never report success
   while it returns `CHECKS: FAILED`, because a failed check means the graph is broken.
2. When `adr.py` cannot make a change that its interface does not support, edit the ADR
   directly, then write one Report entry:
   `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/adr.py log Report "<operation> failed: <error>. I edited <file>: <edit>. Reason: <reason>."`
   This fallback never bypasses invalid input, a rejected map area, or a schema refusal.
   A failed save remains unsaved; report its cause and any partial file rather than a
   successful accepted record. Do not count it as coverage.
3. Return the saved ADR path and list each ERROR, WARN, and SKIP line of the checks. When a
   Report entry exists, offer to open a GitHub issue in
   `ai-advanced-futures/cc-plugins`. After a yes, show the person the full
   issue body, in a fenced block, as the issue will hold it. Then ask a second
   question: "Open the issue with this body? `ai-advanced-futures/cc-plugins`
   is public, so remove each path and each value of the project that must stay
   private." When the person changes the body, show it again and ask again.
   Open it only after a yes to the second question, because the first yes is
   to the offer and not to the text.
