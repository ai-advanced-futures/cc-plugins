---
description: Give each story a T-shirt size through guided questioning
argument-hint: "[feature]"
model: haiku
context: fork
agent: roadmap-analyst
allowed-tools: AskUserQuestion, Read, Edit, Grep, Bash
---

# Estimate stories — the T-shirt size of a story

Give each story one T-shirt size. The size goes in the `size` field of the
Story page.

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

## Step 1: list the stories that need a size

Run this command:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py list Story --fields title,size
```

If the exit code is not 0, stop and show the output.

A story with an empty `size` needs one. A story that already holds a size
needs one only when the user asks for a new estimate.

Read these files before you ask a question:

1. `${CLAUDE_SKILL_DIR}/../shared/roadmap-model.md` — the roadmap types, the
   fields, and the states.
2. `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` — the page format and the
   write rule.
3. `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style (Google
   developer documentation style) for each line that this skill writes. Its
   application to the bundle is in "Writing style" in `bundle-schema.md`.

If the user names a feature in `{{feature}}`, estimate the stories of that
feature only. The `parent` link of a Story page names its feature. If the user
names nothing, estimate each story with an empty `size`.

Do not read every file of a directory, because a large bundle fills the context.
Open a Story page when you estimate it, and open a criterion page only when a
question needs its text.

Tell the user: "This run estimates [N] stories. We go through them one at a
time."

## Step 2: ask the T-shirt questions

Take one story at a time. For each story, show the title, the description, and
the acceptance criteria of its `LINKS` block. Show the progress, as in
"Story 3 of 8".

**Your suggestion**

Give one size, and give the reason for it. Base the reason on the number of
criteria, the parts of the system that the story touches, the unknowns, and a
story of the same bundle that the team already built.

**The question to the user**

Ask: "What is your size for this story?" Give these four answers:

- **S** — simple, known work, less than one day.
- **M** — some complexity, one to three days.
- **L** — complex, three to five days. It may need a division.
- **Discuss** — the story needs more information first.

**When the user picks Discuss**

Ask what is unclear: the scope, the technical approach, a criterion, or a
dependency. Then ask the question that follows from the answer:

- Scope — "What is the smallest version that still gives value?"
- Technical approach — "Which part of the work is unknown?"
- Criterion — "Which criterion is unclear?"
- Dependency — "What must land before this story?"

Then ask for the size again.

**When the user picks L**

Ask: "A large story often gets better after a division. Do we divide this
one?" Give these answers: keep it as L, divide it into two stories, do a
research task first, or make the scope smaller. If the user divides the
story, stop this skill and tell the user to run `/product:stories-identify` for
the new stories. That skill writes a Story page; this one does not.

**What each size looks like**

| Size | The story |
|------|-----------|
| **S** | One criterion. No data change. One part of the system. Work of a known shape. No external dependency. |
| **M** | Two or three criteria. A small data change. Two parts of the system. A few unknowns. |
| **L** | Four or more criteria. A large data change. Many unknowns, or an external integration. Ask about a division. |

**Signs that a story is not ready for a size**

- The title holds the word "and", which hides two stories.
- A criterion does not say when the story is complete.
- The story depends on work that has no size.

A story that shows one of these signs goes back to `/product:stories-identify`
with no size, because a size on a story that is not ready is a guess.

## Step 3: write the size on the story page

Open the Story page of the story, and use the Edit tool to write the field in
its frontmatter:

```yaml
size: M
```

The value is `S`, `M`, or `L`. No other value is valid. The field goes on
a Story page only. A Feature page and a Task page hold no size.

Write one page for each story that the user sizes. Change the `size` field only.
Never edit `state` with the Edit tool, because `prd.py state` is the one write
path and writes one Event line for each change.

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

- Each story that got a size, with its ID and its size.
- Each story that you sent back to `/product:stories-identify`, and why.
- The count of each size in this run.

**Recommend**: "Run `/product:tasks-identify` to divide a sized story into tasks."
