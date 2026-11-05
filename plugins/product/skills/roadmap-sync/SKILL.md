---
description: Sync the roadmap bundle with GitHub, check requirement drift, and find evidence for items that GitHub does not hold
argument-hint: ""
model: sonnet
context: fork
agent: roadmap-analyst
allowed-tools: Agent, AskUserQuestion, Read, Edit, Grep, Glob, Bash
---

# Roadmap sync

Sync `docs/product/roadmap/` with its GitHub Project, flag each requirement that
drifted, and find evidence for each item that GitHub does not hold.

Read these first:

- `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` — the layout, the page format, and the write rule
- `${CLAUDE_SKILL_DIR}/../shared/roadmap-model.md` — the types, the states, and the relationships
- `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style of each line you write

Run the command as `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py <subcommand>` from
the repository root. If `uv` is not available, run `python3` with the same path.

Stop before you start if `docs/product/prd/index.md` does not exist and a v3
PRD file is present in `docs/product/`. Tell the user to run `/product:migrate`.
Leave the v3 file as it is, because the migration reads it and a second copy
becomes a second source of truth.

**The exit code is the verdict.** After each command, read the exit code. A code
that is not 0 stops the skill: show the output and do not report success,
because the command did not do its work. A
warning does not stop you, but show it.

## Part 1: the GitHub round trip

1. Run `prd.py github pull`. It reports each field a person changed in GitHub,
   each conflict, and each issue that has no page.
2. For each `DIFFERENT:` line, ask the user with `AskUserQuestion`: keep the
   bundle value, or take the GitHub value. To take the GitHub value, change the
   page with the Edit tool. To keep the bundle value, note the page ID: the
   page did not change, so the plan sends nothing for it without `--keep`.
3. For the `BOUND:` lines, ask 1 `AskUserQuestion` that lists them: which
   issues get the bundle text? The default is none. Each issue that you do not
   name keeps the title and the body that a person wrote. Note each page ID
   that the user names, and give it `--keep <ID>` in the plan step and the
   apply step.
4. For each `CONFLICT:` line, ask the user which value is correct, then set it.
   For a `state` conflict use `prd.py state <ID> <state> --actor human:<login>`.
   An agent uses `--actor agent:<id> --approved-by '#<n>'`, with the issue whose
   value it takes. For `cancelled`, or a reopen from `done`, give a hitl card link
   or a D-id that hitl decided, because `'#<n>'` is refused there. Never use the
   Edit tool, because `prd.py state` is the one write path and logs each change.
5. For each `UNKNOWN:` line, ask the user whether to adopt the issue. Run
   `prd.py github pull --adopt` when the user agrees to all of them.
6. Run `prd.py github plan`, with `--keep <ID>` for each page of steps 2 and 3
   whose bundle value the user keeps. Show the change set to the user.
7. Ask the user to confirm with `AskUserQuestion`. Run `prd.py github apply`,
   with the same `--keep` options, only after the user agrees. A `REFUSE:` line means no apply: fix the bundle
   first.
8. A `create_issue_type` line adds that name to every repository of the
   organization, not to this one. [inferred] Name that effect in the question
   of step 7, and let the user answer before the apply. [inferred]

## Part 2: requirement drift

Follow `${CLAUDE_SKILL_DIR}/../review/SKILL.md` from its accept rule to
the end of its Step 6. The review lives in that one file.
Only a person clears a flag. Do not give this part to an agent, because an
agent cannot accept a drift.

- Its Step 2 runs `prd.py drift --all --write`. Each work item whose traced
  requirement changed gets that target in `drifted`, and the issue gets the
  label `needs-review` on the next apply.
- That step is an exception to **The exit code is the verdict**. Exit code 1
  with no `ERROR:` line on stderr is the drift that this part reviews. Do not
  stop. Part 2 exists to review this drift, so the skill continues. Its Step 2
  gives the rule for each exit code.
- When no trace drifted, go to Part 3.

The write rule at the end of this skill is also the write rule of the review.

## Part 3: the evidence scan

For each work item that has no `github` field, look for evidence that the work
happened. A match is evidence, not a verdict. The user confirms each state.
[inferred]

1. Run `git log --oneline -50` from the repository root. If the exit code is not
   0, for example because the directory is not a git repository, tell the user
   that the scan did not run. Do not stop the skill for this code, because Parts
   1 and 2 can have changes that the write rule must check. Go to the write rule.
   Do not report the scan as a success, because no scan ran. [inferred]
2. Run `git branch -a` to get the branch names. [inferred]
3. Run `prd.py list Story --where github=- --fields title,state,aliases` for
   each work-item type to get the items that GitHub does not hold. Do the same
   for `Epic`, `Feature`, and `Task`. An absent field prints as `-`, so
   `--where github=` matches no page and the scan would read as a success over
   zero items. [inferred]
   If a type gives no row, say so in the report. Do not report a scan of zero
   items as a success, because it found nothing to check. [inferred]
4. Look for the ID of each item, and for each of its aliases, in the commit
   subjects and the branch names. Match the full ID (`STORY-12`), not a prefix.
   [inferred]
5. Dispatch one Explore agent to search the code and GitHub for the ID of each
   item and for each of its aliases. See
   `${CLAUDE_SKILL_DIR}/references/sync-sources.md` for the search patterns.
6. For each item with evidence, show the user the item, the evidence line, and
   the state that you propose. Ask the user to confirm each one. After the user
   agrees, set the state with `prd.py state <ID> <state> --actor human:<login>`.
   An agent uses `--actor agent:<id> --approved-by <the URL of the evidence>`, for
   example the merged PR.

## The write rule

After your last write, run `prd.py regen` and then `prd.py check`. If either
exits with a code that is not 0, stop and report the output. Do not report
success, because the bundle is in a state that the checks reject.
