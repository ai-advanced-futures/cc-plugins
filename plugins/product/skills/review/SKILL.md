---
description: Review each roadmap item whose traced requirement changed, show the change, and accept the drift only when the person says the item is still correct
argument-hint: "[ID...]"
allowed-tools: AskUserQuestion, Bash, Read, Edit, Grep, Glob
---

# PRD review

A roadmap item traces a requirement page with a short hash. When the text of
the requirement changes, the hash does not match, and the trace is drifted.
This skill shows each drifted trace to the person, and asks the person whether
the item is still correct.

This skill needs no GitHub Project and no network. It reads and writes only the
two bundles below `docs/product/`, and it reads the local Git history.
`/product:roadmap-sync` runs this same review as its Part 2.

Read these first:

- `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` — the layout, the page format, and the write rule
- `${CLAUDE_SKILL_DIR}/../shared/roadmap-model.md` — the types, the states, and the `drifted` field
- `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style of each line you write

Run the command as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py <subcommand>` from
the repository root. If `uv` is not available, run `python3` with the same path.

Stop before you start if `docs/product/prd/index.md` does not exist and a v3
PRD file is present in `docs/product/`. Tell the user to run `/product:migrate`.
Leave the v3 file as it is, because the migration reads it and a second copy
becomes a second source of truth.

**The exit code is the verdict.** After each command, read the exit code. A code
that is not 0 stops the skill: show the output and do not report success,
because the command did not do its work. Step 2 is the one exception.

## The accept rule

Only a person accepts a drift. An agent cannot accept a drift.

- Run `prd.py drift --accept` only for a trace that the person accepted in this
  session, in an answer to `AskUserQuestion`.
- Do not accept a trace because it looks like a wording change. The person
  decides that.
- Do not give any step of this skill to an agent or to a subagent, because
  only the person in this session can answer the question.
- Accept a whole group only when the person accepted it as a group.

## Step 1: get the login of the person

```bash
gh api user -q .login
```

If `gh` fails, for example with no network, ask the user for the login. Do not
guess it from the Git configuration, because the Git name is not the GitHub
login. The actor is `human:<login>`, such as
`human:pilo`, and it must match `^human:[A-Za-z0-9._-]+$`.

## Step 2: find and flag each drifted trace

If the user gave IDs of PRD pages, run `prd.py drift --ids <ID>... --write`.
Else run this command:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py drift --all --write
```

The command prints one line for each drifted trace: the item ID, a tab, and the
target. `--write` adds each target to the `drifted` field of its item.

Read the exit code. This step is an exception to **The exit code is the
verdict**, because exit code 1 is the drift that this skill reviews:

- Exit code 0: no trace drifted. Tell the user, and go to Step 7.
- Exit code 1 with no `ERROR:` line on stderr: the command found drift. This is
  the normal result. Go to Step 3.
- Exit code 1 with an `ERROR:` line on stderr: the command failed, for example
  on a page that it cannot read. Stop, and show the output.
- Exit code 2: stop, and show the output.

## Step 3: show what changed

For each line of Step 2, run this command:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py drift --show <ITEM> <TARGET>
```

The command writes nothing. It prints:

- `BASE:` the commit that holds the text of the last accept.
- `CHANGE:` each commit after the base that changed the target, and
  `CHANGE: not committed` for a change that is not in a commit.
- A diff from the text of the last accept to the current text.
- A `NOTE:` line when it cannot give the diff. For example, no commit holds the
  old text, or the target was deleted. Then it prints the current text, if the
  target exists.

## Step 4: group the traces

Put the traces with the same `CHANGE:` lines in one group. One wording change
to many requirements, for example "moved" to "migrated", gives one group. In a
group, put the traces with the same target together.

Review each trace that has a `NOTE:` line alone in Step 5, because it has no
diff to compare with the others.

## Step 5: ask the person

For each group, show the person:

1. The change commits, from the `CHANGE:` lines.
2. For each target, the diff one time, and the IDs and titles of the items that
   trace it. Get a title with `prd.py list <Type> --fields title`, or read the
   item page.
3. In one sentence, what the change does to the meaning. For example, "Each
   change replaces 'moved' with 'migrated'. The meaning does not change."
   Say that this is your reading, and that the person decides.

Then ask with `AskUserQuestion`. Give these options:

- **All items are still correct**: the person accepts each trace of the group.
- **Review each item**: ask again for each item of the group, with the same
  three options for one item.
- **All items need rework**: keep each flag.

For a trace with a `NOTE:` line, show the current text and the note, and ask
for that one item.

If the person gives no clear answer, keep the flag. Do not accept, because
only a clear answer from the person accepts a drift.

## Step 6: act on each answer

For each trace that the person accepted, run this command:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py drift --accept <ITEM> <TARGET> --actor human:<login>
```

It stores the new hash and removes the target from `drifted`. If the exit code
is not 0, stop, and show the output. Do not report success, because the target
stays in `drifted`.

For each trace that needs rework, keep the flag. Ask the person what to change
in the item. Change the item page with the Edit tool, and change only the
fields and the text that the person agrees to. Then ask the person again
whether to accept the trace. If the item needs work that is not in this bundle,
for example a code change, keep the flag.

Some traces cannot be accepted:

- The target was deleted. Change the trace of the item to the new page, or
  remove the trace, as the person decides. Then run Step 2 again.
- The target has `status: deprecated`. An accept does not clear it. Change or
  remove the trace, as the person decides.

## Step 7: the write rule and the report

After your last write, run `prd.py regen` and then `prd.py check`. Step 2 wrote
the `drifted` fields, so run them also when the person accepted nothing. If
either exits with a code that is not 0, stop and report the output.
Do not report success, because the bundle is in a state that the checks reject.

Then run `prd.py drift --all` again. Exit code 1 is correct when the person
kept a flag. Each line must be a trace that the person kept. A line that the
person did not answer means the review is not complete. Tell the user, and do
not report success, because a drift is still open with no answer.

Report to the person:

| Item | Target | Result | By |
|------|--------|--------|----|
| FEATURE-22 | CAPABILITY-01 | Accepted | human:pilo |
| FEATURE-24 | CONSTRAINT-21 | Flag kept: needs rework | — |

List every accepted trace. The person can read the list and undo an accept with
Git.
