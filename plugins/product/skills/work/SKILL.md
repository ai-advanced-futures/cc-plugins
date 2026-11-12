---
description: The agent protocol for one roadmap item — claim it, do the work, run its checks, and give it back for review
argument-hint: "[ID]"
model: sonnet
allowed-tools: AskUserQuestion, Bash, Read, Write, Edit, Grep, Glob, Skill
---

# Work on one roadmap item

This skill gives the steps around the work. It does not say how you write the
code.

Read these files before you write text on a page:

- `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style.
- `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` — the page format, the IDs,
  the read order, and the write rule.

## Step 0: the bundle must exist

Run this command:

    ls docs/product/prd/index.md

If the file is absent and a v3 PRD file is present in `docs/product/`, stop.
Tell the user: "This repository holds a v3 PRD. Run `/product:migrate` first."
Leave the v3 PRD file as it is, because the migration reads it and a second
copy becomes a second source of truth.

If the file is absent and `docs/product/` holds no v3 PRD file, this
repository has no bundle. Tell the user to run `/product:explore` first, which
bootstraps the bundle. Then stop.

## The command

Run the script from the target repository:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py <subcommand>
```

If `uv` is not available, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py`
instead. The exit code is the verdict. Read the exit code, because the text alone can
look correct after a failure.

Your actor string is `agent:<id>`, where `<id>` names you. Use the same string
for every command of one run.

Build `<id>` from the session ID that your runtime gives you. [inferred] If
you have none, ask the user for a name and use that. [inferred] The `<id>`
must be different for each agent that runs at the same time: two agents that
both use `agent:x` take and extend one another's claim, and no command gives
an error. [inferred]

Exit code 0 is success. [inferred] Exit code 1 means the script refused the
data, such as an item that another agent holds. [inferred] Exit code 2 means
the command was called wrong, such as a bad actor string or a missing
argument. [inferred] For code 1 and code 2 the script prints one `ERROR:`
line on stderr. [inferred] Step 5 gives the two causes of a `run-checks`
code 1.

Exit code 2 with "is held by another prd.py process" on stderr means that
another `prd.py` run holds the write lock. The command wrote nothing: wait,
then run the same command again. `run-checks` is the exception. It writes
its Run page and its `Run` line in a first lock, and then runs the regen in a
second lock. So after `run-checks` exits 2 with the lock message, list the Run
pages of the item first: `prd.py list Run --where item=/<directory>/<ID>.md`,
with the bundle path of the item (for example `/stories/STORY-12.md` or
`/tasks/TASK-07.md`). A Run ID holds its UTC time to the second
(`RUN-<date>-<time>-<token>`), so note the UTC time
(`date -u +%Y%m%d-%H%M%S`) before you run `run-checks`. If a Run page has a
time that is not before that noted time, run `prd.py regen` only, because the
checks already ran and a second run writes a second Run page. If no such page
is there, run `run-checks` again.

## Step 1: Take one item

If the user gave an ID, use it. If not, ask the script for the work that is
free:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py ready
```

Each line is `ID<tab>title<tab>milestone`. The first line is the item with the
nearest milestone date. Every Story that the command lists has a spec.

If `ready` prints no line, do not report "no free work" yet.

The list hides a `ready` Story with no `spec` field or with `spec: none`, so
the list can be empty while work waits. Run the checker:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py check
```

Read the exit code. If it is 2, show the error output and stop. Do not
report that no work is free.

Code 2 means that the check did not run, so it shows no hidden Story.
On 0 or 1, the output holds the warnings.

If its output holds a `W7` line, name each Story of those lines. Tell the
user to run `/product:specifying-stories` on the Feature of each one. Then stop.
If its output holds no `W7` line, report that no work is free, and stop.

### The gates of a Story

Read the `spec` field of the item page before you claim anything. These five
gates refuse the work, and each one tells the user what to do:

1. A Story with no `spec` field: refuse the item. Tell the user to run
   `/product:specifying-stories` on its Feature. `/product:plan` sets `ready` before
   any spec exists, so `ready` alone does not mean specified. The `spec` field
   does.
2. A Story with `spec: none`: refuse the item. The Story needs no build, so
   it has no spec file to read.
3. A `spec` path to a file that does not exist: refuse the item. Tell the
   user that the Story page names a missing spec file. Tell them to correct
   the path, or to run `/product:specifying-stories` on its Feature again.
4. A spec whose `stories` list does not hold the Story: refuse the item. Tell
   the user that the Story page and the spec do not agree. A person must
   correct one of the two.
5. A spec file whose `lifecycle_state` is not `specified`: refuse the item.
   The person has not approved the spec. Relay reads no `lifecycle_state`, so
   this skill is the one gate.

These gates cover `Story` only. Claim an `Epic`, a `Feature`, or a `Task` as
before, with no `spec` check: only a Story holds the slot.

### Claim the whole group

Read the `stories` list of the spec. One spec is built one time. Claim every
Story of that list in one call. The command is all or none. It refuses the
group when one Story is already claimed or is not ready. Then it writes
nothing.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py claim STORY-12 STORY-13 --actor agent:x --lease 30m
```

Exit code 1 means one Story of the group is held or is not ready. Name the
Story that the command refused. Say that the rest of the group waits on it.
Then take the next line of `ready`. A Story of a group whose other
member is already `done` or `in_review` stays on the `ready` list and no
group claim takes it, so a person must split the spec or move that member
back to `ready`. Exit code 0 means every Story of the group is yours, and the
state of each one is now `claimed`.

Make the `spec` path absolute before you give it to relay. The Story page
holds it as a path from the repository root.

## Step 2: Read the item and its links only

Read the item page. Then follow these links, and stop:

- `parent`
- each AcceptanceCriterion whose `item` is this item:
  `prd.py list AcceptanceCriterion --where item=/stories/STORY-12.md --fields title,check`
- each page in `traces`, which is a page of the PRD bundle
- each page in `blocked_by`

Read nothing else. The indexes and these links hold every fact that the item
needs. A full read of a directory costs the context that the work needs.

## Step 3: Do the work

For a Story whose spec is `kind: build`, make no state call in this step.
Step 3a sets `in_progress` after the consent. Write no code: Step 3a owns
the build.

For an Epic, a Feature, a Task, or a `kind: spike` Story, tell the script
that the work started. For a spike, make one call for every Story that you
claimed in the group:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py state STORY-12 in_progress --actor agent:x
```

Read the exit code of each call. On a code that is not 0, stop, show the
output, and go to Step 6.

Then do the work of the Epic, the Feature, or the Task yourself. For a spike,
Step 3a gives the path.
While you work, send a heartbeat for each claimed item before the lease
ends, so no `expire` run takes the item from you:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py heartbeat STORY-12 --actor agent:x --lease 30m
```

Never edit `state`, `claim`, or `drifted` with an edit tool, because the
script is the one write path for them.

## Step 3a: Call relay for a `kind: build` spec

Read `kind` from the spec frontmatter.

For `kind: spike`, do not call relay, because relay builds a `kind: build`
spec and a spike has none. If `engineering:prototype` is in your
list of skills, call it. If it is not, stop and tell the user to run the
probe. When the probe ends, move each Story from
`in_progress` to `in_review`, and the person who ran the probe writes the ADR
or the spec line. A probe that answers nothing leaves the Story in
`in_progress`, and the person records "no decision" in the Stop rule section
of the spec.

For `kind: build`, relay must be on disk:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/check-relay.sh
```

Read the exit code. On a code that is not 0, tell the user:
"Install the relay plugin first." Call no relay, and go to Step 6. Step 6 releases the
group, so no Story stays hidden from `ready` until the lease ends. The
printed root is for the user.

Relay owns the launch contract. Read `<root>/docs/calling-relay-from-another-plugin.md`,
where `<root>` is the root that `check-relay.sh` printed. That guide is the
source of truth for the flags, for the way you watch the child, and for the
engine rules. The rest of this step is what the product plugin adds on top of it.

Ask one `AskUserQuestion` for the consent to `bypassPermissions` and to
`--non-interactive`. On a refusal, call no relay, leave each Story
`claimed`, and go to Step 6.

With the consent, set `in_progress` on every Story that you claimed in the
group. Make one call for each Story:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py state STORY-12 in_progress --actor agent:x
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py state STORY-13 in_progress --actor agent:x
```

Read the exit code of each call. On a code that is not 0, stop and show the
output. Launch no relay, and go to Step 6.

Then launch relay through `Bash` with `run_in_background: true`:

```bash
claude -p "/relay:implement --non-interactive --worktree current --verify --spec /abs/path/to/spec.md" \
  --permission-mode bypassPermissions --output-format stream-json --verbose --max-turns 300 \
  > "${TMPDIR:-/tmp}/prd-work-STORY-12-relay.jsonl" 2>&1
```

`--worktree current` makes no worktree, so relay builds on this branch and
the spec pull request need not be merged first. The redirect writes the
stream file that each poll below reads. Without it, the child writes to a
place that this skill does not read, so the result does not reach you.

Then watch the child by the rules of the guide. These four decide whether the
result ever reaches you:

- Never end your turn while the child runs, because the child then has no
  watcher and nobody reads its result.
- Stop each poll call at 540 seconds, with a bash loop on `$SECONDS`. A `Bash`
  call stops at 10 minutes.
- Launch relay from this skill, never from a sub-agent, because a sub-agent
  has no `Workflow` tool and the run cannot start.
- Run one relay at a time in one working tree, because relay closes each
  open session of the tree when its run ends.

While you poll, keep the claims alive. The lease is 30 minutes, so one
heartbeat for each claimed Story every 10 minutes is enough. A heartbeat on
every poll spends a process and a tool call for nothing:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py heartbeat STORY-12 --actor agent:x --lease 30m
```

The result is the last fenced `json` block with
`"schema": "relay.implement-result/1"`. No block means `error`. The exit code
does not give the status.

- `ok`: move each Story from `in_progress` to `in_review`.
- `blocked` or `error`: each Story stays in `in_progress`, the state that
  Step 3a set. Report the `reason`.

The declared checks set the Run page outcome, through `prd.py run-checks`.
The relay result sets the Story state only.

## Step 4: Record the work that you find

Work that the item does not cover becomes its own Task, in `backlog`:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py new Task \
  --title "Add the index on the day column" \
  --description "The slot query reads the full table without it." \
  --discovered-from STORY-12
```

Do not do that work now. A person plans it.

## Step 5: Run the checks

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py run-checks STORY-12 --actor agent:x \
  --pr https://github.com/owner/repo/pull/12 --spec /abs/path/to/spec.md
```

The command writes one Run page and prints its path. Exit code 0 means no
declared check failed. Read the `outcome` of the Run page: `passed` means each
check ran and passed, and `not-checked` means no check ran, because the item
has no criterion or no criterion has a declared check. For `not-checked`, say
in your report that no check ran. Do not report that the checks passed,
because no check ran.
Exit code 1 with an `ERROR:` line on stderr means the command failed and no
check ran: fix the call, and run it again. [inferred]
Exit code 1 with no `ERROR:` line means one check or more failed: read the
output, and then either continue the work and run the checks again, or give
the item back:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py release STORY-12 --actor agent:x
```

A criterion with no check gets the result `not-checked`. It is not a failure,
and it is not proof.

## Step 6: Hand the item back

This step reads the current state of each Story, not the relay result. It
makes no state call for a Story:

- `in_review`: report the Story, and release it. Step 3a already moved it
  there.
- `claimed`: report the Story, and release it. In this case the build never started.
  Relay is absent, or Step 3a's consent question was refused, or one of its
  `in_progress` calls failed.
- `in_progress`: report the Story only. The build is blocked, or a spike
  reached no decision. Make no `release` call, so the Story stays claimed for
  the person who reads the report.

For an Epic, a Feature, or a Task, Step 3a did not run, so make the two calls
as before.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py state TASK-07 in_review --actor agent:x
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py release TASK-07 --actor agent:x
```

For an `in_review` or a `claimed` Story, make the `release` call only, as
below. The claim then does not outlive the build, and the next agent can claim the Story. When
the release fails, report that failure.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py release STORY-12 --actor agent:x
```

An agent makes five state changes with no approval: `ready` to `claimed`,
`claimed` to `in_progress`, `in_progress` to `in_review`, and a release back to
`ready` from `claimed` or from `in_progress`. An agent sets `done` only with `--approved-by <the merged PR URL>`, and
this skill makes no `done` call, because the merge comes after the hand back. A
person sets `done` with `--actor human:<login>`. An agent never writes `human:`.

## Step 7: The write rule

`run-checks` regenerates the bundle itself, so a run alone leaves nothing to
do here. [inferred] If you wrote or changed any other page of the two
bundles, run these two commands in this order:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py regen
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py check
```

If one of them exits with a code that is not 0, stop, show the output, and
report the failure. Do not report success, because the bundle is in a state
that the checks reject.

## Your report

Give the user these facts:

- the item ID and its new state
- the Run page path and the outcome
- each criterion that is `not-checked`
- the ID of each Task that you added
