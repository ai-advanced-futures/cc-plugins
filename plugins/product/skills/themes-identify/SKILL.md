---
description: Group the capabilities of a milestone into epics through Socratic questioning
argument-hint: "[milestone]"
model: sonnet
context: fork
agent: roadmap-analyst
allowed-tools: AskUserQuestion, Read, Write, Edit, Grep, Glob, Bash
---

# Identify themes — the epics of a milestone

Group the work of one milestone into epics. Each theme becomes one Epic page
in `docs/product/roadmap/epics/`, and each Epic traces the PRD pages that it
satisfies.

For a full roadmap, with the slicing question and the milestones, run
`/product:plan`. This skill is the smaller building block: it makes the epics of a
milestone that already exists.

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
   The hat covers the text of each Epic.
4. `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style (Google
   developer documentation style) for each line that this skill writes. Its
   application to the bundle is in "Writing style" in `bundle-schema.md`.
5. `docs/product/roadmap/index.md` — the roadmap bundle index.
6. `docs/product/roadmap/milestones/index.md` — the milestones. Pick the one
   that this run groups. If `{{milestone}}` was given, take that one.
7. `docs/product/prd/capabilities/index.md` — the capabilities that the epics
   trace to.

Do not read every file of a directory, because a large bundle fills the context.
Open a page only when a question needs it. For a question about the whole graph,
run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py list Capability`.

If the milestones index holds no page, stop. Tell the user to run `/product:plan`
first, which writes the Milestone pages.

**Caller contract**: when `/product:plan` calls this skill, the shared documents
are already read (skip items 1 to 4), the milestones are the phases that the
caller wrote (take them from the caller), and the caller runs the write rule
one time at its end (skip Step 4).

## Step 2: ask the Socratic questions

Explore the work of the milestone with the user. Four questions find the
themes:

- **Value clusters** — which groups of capabilities give value together?
- **Dependencies** — what must exist before the other work can run?
- **Risk areas** — which part is unclear or difficult?
- **Quick wins** — which part gives value for a small effort?

Then propose three to six themes. For each proposal, name the capabilities and
the scope entries that the theme holds, and say why the group holds together.

Challenge each theme:

- "Is this epic too large? Can you divide it?"
- "What is the smallest scope that still gives value?"
- "What happens if this epic is late?"
- "Does an outside constraint hold this epic?"

Ask the user to confirm the set before you write. A theme is a group of user
value, not a component of the system. Keep the product hat on.

## Step 3: write one Epic page for each theme

Run one command for each theme:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py new Epic \
  --title "Scheduling" \
  --description "The customer books, moves, and cancels a slot." \
  --link milestone=/milestones/MILESTONE-01.md \
  --traces prd:/capabilities/CAPABILITY-03.md
```

The command prints the path that it wrote. If the exit code is not 0, stop and
show the output.

Never choose an ID, because `prd.py new` assigns it and a hand-chosen ID can
collide. Give `--traces` one time for each PRD page that the epic satisfies. An
Epic traces one PRD page or more. Warning W2 reports an Epic with no trace. Ask
the user which requirement drives an untraced epic, or whether the PRD is
missing a page.

`prd.py new` writes the hash of each trace, and `prd.py hash` gives the hash of
a page.

Each new epic starts in `backlog`. `/product:plan` promotes the items of the
chosen slice with `prd.py state`.

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

- Each epic that you wrote, with its ID and its milestone.
- Each PRD page that the epics trace to.
- Each epic with no trace, and each capability of the milestone that no epic
  holds.

**Recommend**: "Run `/product:features-identify` to divide an epic into features."
