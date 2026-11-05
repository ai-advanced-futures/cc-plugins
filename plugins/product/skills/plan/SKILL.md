---
description: Turn the PRD into a roadmap — ask how to slice the scope (MVP, one phase, the full product), write one Milestone page for each phase, drive the three identify skills, and promote the items of the chosen slice
argument-hint: "[scope]"
model: sonnet
agent: roadmap-analyst
allowed-tools: AskUserQuestion, Read, Write, Edit, Grep, Glob, Bash
---

# Plan — the PRD to the roadmap

Turn `docs/product/prd/` into the roadmap bundle for a scope that the user
chooses. Each phase of the slice becomes a Milestone page. This skill drives
the three identify skills; it does not replace them. `/product:themes-identify`,
`/product:features-identify`, and `/product:stories-identify` stay available for a
smaller change.

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

This skill works on the two bundles through `${CLAUDE_PLUGIN_ROOT}/scripts/prd.py`.
Run each `prd.py` command with the target repository as the current directory.
If `uv` is not installed, run `python3` with the same path.

## Step 1: read the bundle

Read these files, in this order:

1. `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` — the layout, the page
   format, the IDs, the relationships, and the write rule.
2. `${CLAUDE_SKILL_DIR}/../shared/roadmap-model.md` — the roadmap types, the
   states, and the status tables.
3. `${CLAUDE_SKILL_DIR}/../shared/product-hat.md` — the product guardrail.
   The hat covers the text of each Epic, Feature, and Story.
4. `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style (Google
   developer documentation style) for each line that this skill writes. Its
   application to the bundle is in "Writing style" in `bundle-schema.md`.
5. `docs/product/prd/index.md` — the bundle index.
6. `docs/product/prd/product.md` — the product summary and the `lenses` map.
7. `docs/product/prd/scope/index.md` — the scope entries that the phases cut.

Do not read every file of a directory, because a large bundle fills the context.
Open a page only when a phase question needs it. For a question about the whole
graph, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py list Capability`.

**Soft gate**: a plan needs the Capabilities lens and the Scope lens. If the
`lenses` map of `product.md` shows one of the two below `in-progress`,
recommend `/product:explore capabilities` or `/product:explore scope` first. The user
can go on with what exists.

## Step 2: ask the slicing question

Ask the user how to slice the scope. Use one `AskUserQuestion` with these
options:

- **The MVP** — the first shippable phase. Each later phase stays a milestone
  with no items.
- **One phase** — the user names the phase to plan now.
- **The full product** — name each phase, then plan each one.

If `{{scope}}` was given, map the argument to one of the three options and
confirm that option in place of the question, because the argument already
answers it.

Then propose the phases. Derive each phase from the pages of the bundle, and
name the capabilities and the scope entries that the phase holds. Two or four
proposals are enough. Recommend one proposal, and say why.

## Step 3: write one Milestone page for each phase

Each phase becomes one Milestone page, so the whole shape stays visible. Run
one command for each phase:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py new Milestone \
  --title "MVP" --description "The first release holds booking only." \
  --set target_date=2026-12-01 --traces prd:/scope/SCOPE-01.md
```

The command prints the path that it wrote. If the exit code is not 0, stop and
show the output.

Never choose an ID, because `prd.py new` assigns it and a hand-chosen ID can
collide.

A phase that the user does not slice now is a milestone with no items. Write
its page in this step, and give it no epics and no features. A later run of
`/product:plan` fills it. No separate skill makes milestones.

## Step 4: drive the three identify skills

For the chosen slice only, run these skills in this order:

1. `/product:themes-identify` — the Epic pages of the slice.
2. `/product:features-identify` — the Feature pages of each epic.
3. `/product:stories-identify` — the Story pages and the criteria of each feature.

Each skill runs under its caller contract: the shared specifications are
already read, the milestones are the phases of step 3, and this skill runs
the write rule one time, in step 6.

Ask the user before you go down to the stories of each feature, so the user
can stop at any point. Keep the pace of the three skills: this is a session
with the user, not a batch.

A milestone of a phase that the user does not slice now gets no identify run.

## Step 5: promote the items of the chosen slice

Each new item starts in `backlog`. Promote each item of the chosen slice with
one command:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py state FEATURE-04 ready --actor human:<login>
```

A person runs `--actor human:<login>`. An agent runs `--actor agent:<id>
--approved-by <approval>` with the plan PR (`'#<n>'` or its URL) or the D-id of the
slice decision. A Story with no `spec` file in the tree gets exit code 1 from an
agent: specify it first with `/product:specifying-stories`. The script gives
`ready` or `blocked`, because the blockers decide. A request for `ready` on an item with an open blocker gives `blocked`.
Take the value that the script prints.

The exit code is the verdict. Exit code 0: the item has the state that the
script prints. Any other code: the item did not change. Show the `ERROR:` line to
the user, and stop.

Never edit `state` with the Edit tool, because `prd.py state` is the one write
path and writes one Event line for each change. An item of a phase that the user
does not slice now stays in `backlog`.

## Step 6: check the traces

Before the last step, check three things:

- Each milestone, each epic, and each feature has one trace or more. A story
  holds a trace only when it narrows the traces of its parent. Raise an
  untraced item with the user.
- Each trace target exists in the PRD bundle. A trace to an absent page is an
  error. Fix it now.
- Each scope entry of the chosen slice that no item traces to. The user says
  whether the entry is a gap or is intentional.

## Last step: run the checks

Run these two commands:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py regen
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py check

If one command gives an exit code that is not 0, stop and show the output to
the user. Do not report success, because the checks reject the bundle. "The
write rule" in `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` gives the rule
for a warning, a status table, and a hash.

Never write a status table by hand, because `prd.py regen` writes it and
overwrites a hand edit.

## Report

Tell the user:

- Each milestone that you wrote, and which one holds the chosen slice.
- The count of epics, features, and stories of the slice.
- Each item that the script set to `blocked`, and the blocker.
- Each untraced item and each uncovered scope entry of step 6.

**Recommend**: "Run `/product:tasks-identify` to divide a story into tasks, and
`/product:stories-estimate` with the team to size the stories. Run
`/product:roadmap-sync` to track the progress and the drift. Run `/product:plan`
again to plan the next phase."
