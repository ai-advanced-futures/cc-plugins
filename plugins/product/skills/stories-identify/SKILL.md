---
description: Divide a feature into user stories through Socratic questioning
argument-hint: "[feature]"
model: sonnet
context: fork
agent: roadmap-analyst
allowed-tools: AskUserQuestion, Read, Edit, Grep, Bash
---

# Identify stories — the stories of a feature

Divide the work of one feature into stories. Each story becomes one Story page
in `docs/product/roadmap/stories/`, and each acceptance criterion becomes one
AcceptanceCriterion page in `docs/product/roadmap/criteria/`.

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
   The hat covers the text of each Story and of each criterion.
4. `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style (Google
   developer documentation style) for each line that this skill writes. Its
   application to the bundle is in "Writing style" in `bundle-schema.md`.
5. `docs/product/roadmap/features/index.md` — the features.
6. The page of the feature that the user names in `{{feature}}`. If the user
   names nothing, show the index and ask which feature this run divides.
7. The criteria of that feature. The `LINKS` block of the feature page lists
   them. Open a criterion page only when a question needs its text.
8. The `traces` of the feature page, and each PRD page that it names. These
   traces tell what the feature must satisfy.

Do not read every file of a directory, because a large bundle fills the context.
Open a page only when a question needs it. For a question about the whole graph,
run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py list Story`.

The feature page gives the `milestone` link that each story of this run gets.
If the feature page has no milestone, ask the user which milestone holds the
stories, or write no `milestone` link.

**Caller contract**: when `/product:plan` calls this skill, the shared documents
are already read (skip items 1 to 4), the feature comes from the caller, and
the caller runs the write rule one time at its end (skip Step 5).

## Step 2: ask the Socratic questions

Explore the work with the user. Find the stories, then examine each one.

**Story discovery**

- What is the first action that the user does in this feature?
- Which actions follow it?
- What happens when an action fails?
- How does the user know that the action was a success?

Write each story in this form:

    As a <persona>, I want to <action>, so that <benefit>.

Name a Persona page of the PRD bundle in the `<persona>` part when one exists,
as in "As a returning customer (PERSONA-02)". The form goes in the description
and in the body text of the page.

**For each story**

- **Independent** — can the team build this story alone, with no other story
  first?
- **Negotiable** — can the scope change as the team learns?
- **Valuable** — who gets the value, and how?
- **Estimable** — is the work known enough for `/product:stories-estimate` to give
  it a T-shirt estimate?
- **Small** — does the story fit in one sprint?
- **Testable** — does each criterion say when the story is complete?

A story that fails one of the six questions is not ready. Divide it, or ask
the user for the missing scope.

**Challenge each story**

- "Is this one story, or two stories together?"
- "What is the smallest version that still gives value?"
- "What can go wrong, and does a criterion cover it?"

**How to divide a story that is too large**

- By the steps of the workflow.
- By the persona.
- By the data: the simple case first, then the complex case.
- By the operation: create, read, change, remove.
- By the level: the basic version first, then the fast version.

**Consolidation**

Ask: "Do these stories give the full feature?" A missing action, two stories
that overlap, and a story that goes past the feature are all answers that
change the set. Ask the user to confirm the set and its order before you write.

Then, for each story that the user confirms, agree the acceptance criteria. A
criterion is one sentence that tells when the story is complete. Keep the
product hat on: a criterion says what the user gets, not how the code does it.

## Step 3: write one Story page for each story

Run one command for each story:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py new Story \
  --title "Pick a day" \
  --description "The customer picks a day and sees the free slots of that day." \
  --link parent=/features/FEATURE-04.md \
  --link milestone=/milestones/MILESTONE-01.md
```

The command prints the path that it wrote. If the exit code is not 0, stop and
show the output.

Never choose an ID, because `prd.py new` assigns it and a hand-chosen ID can
collide. Give `--link parent=` the feature that holds the story.

A story stores a `traces` entry only when it narrows the traces of its parent,
as in a story that satisfies one step of a journey while the feature traces the
whole journey. Add the narrower target with
`--traces prd:/journeys/JOURNEY-01.md`. A story that does not narrow them stores
none: the parent holds the link. `prd.py new` writes the hash of each trace, and
`prd.py hash` gives the hash of a page.

Each new story starts in `backlog`. `/product:plan` promotes the items of the
chosen slice with `prd.py state`. `/product:stories-estimate` adds the T-shirt
estimate later, and `/product:tasks-identify` divides the story into tasks. This
skill writes neither one.

## Step 4: write one AcceptanceCriterion page for each criterion

Run one command for each criterion of each story:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py new AcceptanceCriterion \
  --title "A full day shows no free slot" \
  --description "The day view shows the words 'no free slot' when each slot of the day is taken." \
  --link item=/stories/STORY-12.md
```

Give `--link item=` the Story page that the criterion belongs to. A criterion
belongs to one work item.

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

- Each story that you wrote, with its ID, its parent, and its milestone.
- The number of criteria that you wrote for each story.
- Each story that stores a trace, and why it narrows the traces of the feature.

**Recommend**: "Run `/product:stories-estimate` to give each story a T-shirt
estimate, then `/product:checks-declare` to add the `check` argv of each criterion."
