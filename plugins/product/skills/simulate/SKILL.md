---
description: Simulate developer implementation of the PRD capabilities, one capability at a time, and surface the gaps and the uncaptured decisions of that capability. An assessor agent picks the answer of each small gap, and the owner accepts those picks at the end
argument-hint: "[capability | --all] [--decide autonomously|interactively]"
model: opus
context: fork
agent: prd-simulator
allowed-tools: AskUserQuestion, Agent, Read, Grep, Bash
---

# Simulate — walk the capabilities as a developer

Walk the capabilities of `docs/product/prd/`, one capability at a time, as
the developer who must build them, to find the gaps. This skill writes no page,
because `/product:learn` writes the decisions of the session.

**The output boundary**: every decision that you capture is product behavior
or a product constraint — never a technology choice. Read
`${CLAUDE_SKILL_DIR}/../shared/product-hat.md` for the constraint test,
`${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` for the page format and the
ID format, and `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` for the writing
style (Google developer documentation style) of each line that you give to
`/product:learn`.

## Arguments

- `[capability]`: start with that capability. Match the argument against the
  ID, an alias, or the title.
- `--all`: walk each capability of the index, in the order of the index.
- No capability and no `--all`: start with the first line of the index.
- `--decide autonomously`: the default. The owner answers only the gaps that
  need the owner. An assessor agent picks the answer of each other gap, and
  the owner accepts those picks at the end. Step 3 gives the rule.
- `--decide interactively`: the owner answers each gap that counts, one at a
  time. The "build it now" test of step 3 applies in both modes.

If the Agent tool is not available, use `--decide interactively`, and tell the
user why at the start. Never pick and grade an answer yourself: the assessor
exists so that a second agent checks your view.

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

## Step 1: read the capability index and the stages

Read `docs/product/prd/capabilities/index.md`. Each line gives the ID, the
title, and the description of one capability. The description says what the
capability does, so the index alone is enough to choose the next capability.

In `--decide autonomously` mode, run this command one time:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py stage

Each line gives a capability ID, its stage, and the done or released work item that makes
it mature:

    CAPABILITY-03	mature	STORY-12
    CAPABILITY-04	early	-

A capability is **mature** when a roadmap work item in state `done` or `released` traces to
it. Each other capability is **early**. If the exit code is not 0, stop and
show the output.

Walk the capabilities one capability at a time:

- With `--all`, go to the next capability of the index after each
  capability, with no question, because `--all` already gives the answer.
- Without `--all`, after each capability, tell the user which capability comes
  next, and ask whether to go on. Use one `AskUserQuestion`.

Do not read every file of a directory, because a large bundle fills the
context. For a question about the whole graph,
run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py list`. If `uv` is not
installed, run `python3` with the same path.

## Step 2: open the one capability page

Open the page of the chosen capability. Read its frontmatter and its body,
then follow the `LINKS` block of that page only:

- Each `addresses` link: the need, the journey, the persona, or the problem
  that the capability serves.
- Each `depends_on` link: the capability that it needs.
- Each derived link of the block that constrains the capability, as in a
  `Constraint` page or a `Risk` page.

Read nothing else. The links of that one page give the context of the
simulation. A link that goes one more step away stays closed unless a gap
question of step 3 needs it.

## Step 3: find the gaps of that capability

Ask yourself the developer questions against the capability and its links:

- Behavioral ambiguity: which behavior does the text not fix?
- Missing error paths: what happens when the step fails?
- Unstated assumptions: which fact does the text take for granted?
- Integration gaps: which other capability or system must answer?
- Data questions: which data must exist, and who gives it?
- State management: which states exist, and which change is permitted?
- Performance and scale: which limit does the user feel?
- Edge cases: which unusual situation has no answer?

Raise a point only when it fails the "build it now" test below. Skip a clear
point in silence.

### The "build it now" test

A gap counts only when a developer who builds this capability now, as
written, gets stuck or must guess. Put each other gap in the **Later** list of
the summary, with one line. Examples of a later gap: a scale that the product
does not have yet, a capability that is not in the index, or a phase after the
current Milestone. A later gap gets no assessment and no question.

### Prepare each gap

For each gap that counts:

1. **Quote** the line of the page, as-is, with its ID.
2. **Explain** what is missing or ambiguous for the developer.
3. **Write 2 to 4 concrete options.** Each option is product behavior ("reject
   the upload and tell the user why"), not technology ("use S3 multipart
   upload"). Give each option a pro, a con, and the pages that it changes.
4. **Give your level** of the gap: detail, middle, or direction. The levels
   are defined in `${CLAUDE_SKILL_DIR}/assessor.md`.

In `--decide interactively` mode, ask the user about each gap through
`AskUserQuestion`, with your recommendation first. If the answer of the user
opens a new unknown, ask again before you move on. Then go to "Record each
answer".

### Assess each gap (`--decide autonomously`)

Start one `general-purpose`
subagent for each gap with the Agent tool. Its prompt is the full text of
`${CLAUDE_SKILL_DIR}/assessor.md`, then a brief with these parts:

- The capability ID and its stage from step 1.
- The quote, the page ID, the absolute path of each quoted page, and what is
  missing.
- The options, with no recommendation and no level, because the assessor
  forms its own view.
- Each decision that the owner gave in this session.
- Each set-aside pick so far, marked as a pick that the owner did not accept
  yet.
- The absolute path of `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md`.

The assessor replies with a pick, a level, a confidence, and a visibility. If
the reply does not have these four values, send the gap to the owner.

**Cross-check the pick.** Read the reasons of the assessor against the quoted
pages. Agree, or object with one reason: a factual error, a conflict with a
page, or a conflict with an owner decision. A gap with an objection goes to
the owner, not back to the assessor, because the owner settles a disagreement
between the two agents.

**Find the verdict.** Use the higher of your level and the level of the
assessor. Then find the cell for the stage, the visibility, the level, and the
confidence:

Early, visible:

| Level | High | Medium | Low |
|---|---|---|---|
| Detail | Set aside | Set aside | Set aside |
| Middle | Set aside | Set aside | Ask |
| Direction | Set aside | Ask | Ask |

Early, hidden:

| Level | High | Medium | Low |
|---|---|---|---|
| Detail | Set aside | Set aside | Ask |
| Middle | Set aside | Ask | Ask |
| Direction | Ask | Ask | Ask |

Mature, visible:

| Level | High | Medium | Low |
|---|---|---|---|
| Detail | Set aside | Set aside | Set aside |
| Middle | Set aside | Ask | Ask |
| Direction | Ask | Ask | Ask |

Mature, hidden:

| Level | High | Medium | Low |
|---|---|---|---|
| Detail | Set aside | Ask | Ask |
| Middle | Ask | Ask | Ask |
| Direction | Ask | Ask | Ask |

- **Ask:** ask the user now, through `AskUserQuestion`. Put the pick of the
  assessor first, and mark it "(Recommended)". If the answer of the user opens
  a new unknown, ask again before you move on.
- If the gap goes to the owner because of an objection, or because the reply
  has no valid pick, do not mark the pick "(Recommended)". Put your own
  recommendation first, and give the objection in the question text.
- `AskUserQuestion` takes 4 options at most. If the pick is a new option and
  you wrote 4 options, put the new option first, leave out your last option,
  and name that option in the question text.
- **Set aside:** keep the gap, the pick, the level of the verdict, the
  confidence, the visibility, and the stage for the owner review of step 4,
  and go to the next gap.

Assess the gaps of one capability one at a time, in the order in which a
developer meets them.

### Record each answer

Record each answer as one of two pages for `/product:learn`:

| The answer gives | The page |
|---|---|
| A product behavior, and why it was chosen | `Decision`, with `about` pointing to the capability |
| A limit that the product must respect | `Constraint`, with `constrains` pointing to the capability |

A point that stays open is a `Question` page. A gap that needs a new
capability or a new need is a finding for the matching lens of
`/product:explore`.

## Step 4: review the set-aside gaps

Do this step when the walk ends: when the user stops, or when each capability
of the index is walked. Skip it when no gap is set aside.

First, compare each set-aside pick with the owner decisions that came after
it. A pick that conflicts with an owner decision does not go in the list. Ask
the user about that gap through `AskUserQuestion`, as for a held-back gap.

Print the set-aside gaps as chat text, numbered, and grouped by capability.
Put the direction gaps first in each group, with the mark **Direction**. Give
each gap one line:

    3. CAPABILITY-04 — a cancelled slot within one hour: refund in full. Detail, visible, high, early.

Then ask the user to reply with `all`, or with `all except` and the numbers to
hold back, for example `all except 3, 7`. Ask in chat text, not with
`AskUserQuestion`, because the dialog hides the list.

- Each accepted gap is a decision of the owner. Record it as in step 3.
- Ask the user about each held-back gap, one at a time, through
  `AskUserQuestion`. Put the pick of the assessor first. Record the answer as
  in step 3.
- If the answer to a held-back gap is not the pick, find each accepted pick
  that depends on that pick. Tell the user about each one, and ask again
  about it.
- If the user asks why for a number, give the reasons of the assessor.

## Step 5: close the session

Summarize the session:

```markdown
## Simulation Summary

### Capabilities walked: X of Y

### Gaps found: X
- **Asked**: [count]
- **Set aside and accepted**: [count]
- **Set aside and held back**: [count]

### Decisions of this session
| Capability | Gap | How | Page for /product:learn |
|---|---|---|---|
| CAPABILITY-03: [title] | [what was missing] | Asked / Accepted | Decision: [the behavior] |

### Open questions
| Capability | Question |
|---|---|
| CAPABILITY-05: [title] | [what stays open] |

### Later (not for /product:learn)
| Capability | Gap |
|---|---|
| CAPABILITY-05: [title] | [what only matters later] |
```

The Later list does not go to `/product:learn`. Give a Later gap to `/product:learn`
only when the user asks for it.

Ask one question: "Learn these results?" On yes, run `/product:learn` with the
findings of this session. The Later list is not part of these findings.
