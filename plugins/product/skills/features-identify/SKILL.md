---
description: Divide an epic or a milestone into features through Socratic questioning
argument-hint: "[epic-or-milestone]"
model: opus
context: fork
agent: roadmap-analyst
allowed-tools: AskUserQuestion, Read, Edit, Grep, Bash
---

# Identify features — the features of an epic

Divide the work of one epic, or of one milestone, into features. Each feature
becomes one Feature page in `docs/product/roadmap/features/`, and each
acceptance criterion becomes one AcceptanceCriterion page in
`docs/product/roadmap/criteria/`.

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
   The hat covers the text of each Feature and of each criterion.
4. `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style (Google
   developer documentation style) for each line that this skill writes. Its
   application to the bundle is in "Writing style" in `bundle-schema.md`.
5. `docs/product/roadmap/milestones/index.md` — the milestones.
6. `docs/product/roadmap/epics/index.md` — the epics.
7. The page of the epic or of the milestone that the user names in
   `{{epic-or-milestone}}`. If the user names nothing, show the two indexes
   and ask which one this run divides.
8. `docs/product/prd/capabilities/index.md` — the capabilities that the
   features trace to.

Do not read every file of a directory, because a large bundle fills the context.
Open a page only when a question needs it. For a question about the whole graph,
run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py list Feature`.

If the epics index holds no page and the user names a milestone, this run
writes features with a `milestone` link and no `parent`. That is correct: a
Feature can have no parent.

**Caller contract**: when `/product:plan` calls this skill, the shared documents
are already read (skip items 1 to 4), the epic or the milestone comes from the
caller, and the caller runs the write rule one time at its end (skip Step 5).

## Step 2: ask the Socratic questions

Explore the work with the user. Find the features, then examine each one.

**Feature discovery**

- Which capabilities must exist to reach the goal of this epic?
- What is the smallest version that still gives value?
- What happens if this feature is absent?
- Is this one feature, or two features together?

**For each feature**

- **Scope** — what is the smallest version that still gives value?
- **User value** — who gets the value, and how?
- **Dependencies** — does another feature come first? Does this feature let
  another one start?
- **Difficulty** — is the work known, partly known, or unknown? Unknown work
  needs a spike first.
- **Priority in the epic** — must have, should have, or nice to have.

**Challenge each feature**

- "Can this feature be more simple?"
- "Does this feature do too much?"
- "What can go wrong with this feature?"
- "How does the user find this feature and learn it?"

**Consolidation**

Ask: "Is the scope of this set correct for the epic?" A feature that the epic
does not need, a missing feature, and two features that overlap are all answers
that change the set. Ask the user to confirm the set before you write.

Then, for each feature that the user confirms, agree the acceptance criteria.
A criterion is one sentence that tells when the feature is complete. Keep the
product hat on: a criterion says what the user gets, not how the code does it.

## Step 3: write one Feature page for each feature

Run one command for each feature:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py new Feature \
  --title "Slot search" --description "The customer sees each free slot of a day." \
  --link parent=/epics/EPIC-01.md --link milestone=/milestones/MILESTONE-01.md \
  --traces prd:/capabilities/CAPABILITY-03.md
```

The command prints the path that it wrote. If the exit code is not 0, stop and
show the output.

Never choose an ID, because `prd.py new` assigns it and a hand-chosen ID can
collide. Give `--link parent=` the epic that holds the feature. When the run
divides a milestone and no epic holds the feature, give `--link milestone=`
only.

Give `--traces` one time for each PRD page that the feature satisfies, usually
a Capability page. A Feature must have one trace or more. Warning W2 reports a
Feature with no trace. A feature that traces to nothing is out of scope, or the
PRD misses a page. Ask the user which of the two it is before you write.

`prd.py new` writes the hash of each trace, and `prd.py hash` gives the hash of
a page.

Each new feature starts in `backlog`. `/product:plan` promotes the items of the
chosen slice with `prd.py state`.

## Step 4: write one AcceptanceCriterion page for each criterion

Run one command for each criterion of each feature:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py new AcceptanceCriterion \
  --title "A full day is not in the list" \
  --description "The list holds a day only when one slot of that day is free." \
  --link item=/features/FEATURE-04.md
```

Give `--link item=` the Feature page that the criterion belongs to. A
criterion belongs to one work item.

Write the criterion text only. Leave out the `check` command and the person,
because `/product:checks-declare` adds the `check` argv and the person who
declares it later.

## Step 5: run the checks

Run these two commands:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py regen
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py check

If one command gives an exit code that is not 0, stop and show the output to
the user. Do not report success, because the checks reject the bundle. "The
write rule" in `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` gives the rule
for a warning, a status table, and a hash.

## Report

Tell the user:

- Each feature that you wrote, with its ID, its parent, and its milestone.
- The number of criteria that you wrote for each feature.
- Each feature with no trace, and each capability of the epic that no feature
  holds.

**Recommend**: "Run `/product:stories-identify` to divide a feature into stories."
