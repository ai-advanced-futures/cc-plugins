---
description: Divide one story into engineering tasks with an engineer persona
argument-hint: "[story]"
model: sonnet
agent: roadmap-analyst
allowed-tools: AskUserQuestion, Read, Bash, Grep
---

# Identify tasks — the tasks of a story

Divide the work of one story into tasks. Each task becomes one Task page in
`docs/product/roadmap/tasks/`.

A task is engineering work inside one story. A task is therefore
outside the product hat. Wear the engineer hat for this skill: name the code
that changes, the work that comes first, and the test that shows that the task
is done. Keep the product language in the Story page and in its criteria.

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
3. `${CLAUDE_SKILL_DIR}/../shared/product-hat.md` — read "The limit of the
   hat". A Task page is one of the three parts that the hat does not cover.
4. `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style (Google
   developer documentation style) for the title and the description of each
   task. Its application to the bundle is in "Writing style" in
   `bundle-schema.md`.
5. `docs/product/roadmap/stories/index.md` — the stories.
6. The page of the story that the user names in `{{story}}`. If the user names
   nothing, show the index and ask which story this run divides.
7. The criteria of that story. The `LINKS` block of the story page lists them.
   The criteria tell when the story is complete, so they tell which tasks the
   story needs.
8. The `traces` of the parent of the story, and each PRD page that they name.
   These traces tell what the story must satisfy. A story stores a trace only
   when it narrows the traces of its parent, so read the parent page too.

Do not read every file of a directory, because a large bundle fills the context.
Open a page only when a question needs it. For a question about the whole graph,
run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py list Task`.

The story page gives the `milestone` link that each task of this run gets. If
the story page has no milestone, ask the user which milestone holds the tasks,
or write no `milestone` link.

## Step 2: ask the engineer questions

Explore the work with the user, one task at a time. For each task, ask these
three questions:

- **What changes in the code?** Name the part of the system that the task
  changes: the file, the module, the endpoint, the table, or the screen. A task
  that names no part of the system is too large. Divide it.
- **What does the task need first?** Name each task that must be done before
  this one starts. That answer becomes a `blocked_by` link.
- **How does a person see that it is done?** Name the test, the command, or the
  screen that shows the result. A task with no answer here is not ready.

Then challenge each task:

- "Is this one task, or two tasks together?"
- "Can one engineer do this task in one day?"
- "Which criterion of the story does this task move forward?"

**Consolidation**

Ask: "Do these tasks give the full story?" A missing step, two tasks that
overlap, and a task that goes past the story are all answers that change the
set. Ask the user to confirm the set and its order before you write.

Each task stays inside one story. Work that no criterion of the story needs
belongs to another story, or the story misses a criterion. Ask the user which
of the two it is before you write.

## Step 3: write one Task page for each task

Run one command for each task:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py new Task \
  --title "Add the free-slot query" \
  --description "The API gives the free slots of one day." \
  --link parent=/stories/STORY-12.md \
  --link milestone=/milestones/MILESTONE-01.md
```

The command prints the path that it wrote. If the exit code is not 0, stop and
show the output.

Never choose an ID, because `prd.py new` assigns it and a hand-chosen ID can
collide. Give `--link parent=` the story that holds the task.

Give `--link blocked_by=` one time for each task that must be done first, as in
`--link blocked_by=/tasks/TASK-07.md`. Write a task that comes first before the
task that it blocks, because the target page must exist.

A task stores a `traces` entry only when it narrows the traces of its parent.
Add the narrower target with `--traces prd:/capabilities/CAPABILITY-03.md`. A
task that does not narrow them stores none: the story or the feature holds the
link. `prd.py new` writes the hash of each trace, and `prd.py hash` gives the
hash of a page.

Write the title and the description of a task in engineering language. The
title names the change. The description says what the code does after the
change. A task holds no acceptance criterion: a criterion belongs to the story.

A new task starts in `backlog`. `/product:plan` or a person promotes it. This skill
does not change the state of a task.

## Step 4: run the checks

Run these two commands:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py regen
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py check

If one command gives an exit code that is not 0, stop and show the output to
the user. Do not report success, because the checks reject the bundle. "The
write rule" in `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` gives the rule
for a warning, a status table, and a hash.

## Report

Tell the user:

- Each task that you wrote, with its ID, its parent, and its milestone.
- The order of the tasks, and each `blocked_by` link that holds that order.
- Each criterion of the story that no task moves forward.

**Recommend**: "Run `/product:checks-declare` to add the `check` argv of each
criterion of the story."
