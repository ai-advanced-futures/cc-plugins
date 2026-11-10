---
description: Writes one architecture decision record (ADR) the moment a decision that would be expensive to undo has just been made -- a datastore, a service or trust boundary, a wire or event contract, a deployment topology, a public interface others consume. Writes the ADR with lifecycle accepted and keeps working; it never stops to ask. Use for "/architecture:learn", "write an ADR", "record this decision", "document this architecture decision", and fires on its own during a session the moment a decision that is expensive to undo is made.
argument-hint: "[decision]"
allowed-tools: Read, Grep, Glob, Write, Edit, Skill, Bash(uv run *), Bash(git *), Bash(gh issue create *), Bash(test *)
---

# Learn

Write one ADR. Capture the decision now, then keep working on whatever the session was already
doing.

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

`ROOT` is `$(git rev-parse --show-toplevel)`.
`A` is `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/adr.py --root "$ROOT"`.

Read `.claude/adr.json` first. If `rules` names a file, read that repository-root-relative
Markdown file and apply it as additional instructions after this shipped procedure. Stop with the
missing path when the configured file cannot be read.

```bash
$A new --title "<title>" --area "<area>"
```

Add `--parent-spec <path>` only when a parent spec exists, and `--description "<line>"` when the
active schema has a `description` property. `adr.py new` prints the path of the new file.

`adr.py new` has no `model` flag. When the choice has a model status, element, or reason, set it
right after:

```bash
$A set <id> model='{status: <value>, element: <value>, reason: <value>}'
```

Choose a valid model status: `modeled`, `out-of-scope`, or `black-box`. Give `element` and
`reason` only when they explain the choice.

`adr.py new` also has no `evidence` flag. When durable, dated evidence exists, set it the same way:

```bash
$A set <id> evidence='[<dated measurement>, ...]'
```

`evidence` is dated evidence: a measurement that must persist. Omit it when none exists.

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
2. When `adr.py` cannot make a change, edit the ADR directly, then write one
   Report entry: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/adr.py log Report "<operation> failed: <error>. I edited <file>: <edit>. Reason: <reason>."`
3. In the report, list each ERROR, WARN, and SKIP line of the checks. When a
   Report entry exists, offer to open a GitHub issue in
   `ai-advanced-futures/cc-plugins`. After a yes, show the person the full
   issue body, in a fenced block, as the issue will hold it. Then ask a second
   question: "Open the issue with this body? `ai-advanced-futures/cc-plugins`
   is public, so remove each path and each value of the project that must stay
   private." When the person changes the body, show it again and ask again.
   Open it only after a yes to the second question, because the first yes is
   to the offer and not to the text.
