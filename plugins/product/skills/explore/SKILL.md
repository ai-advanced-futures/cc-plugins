---
description: Lens-driven Socratic exploration of product requirements — pick a lens (personas, journeys, scope...) or get guided to the next one in logical order
argument-hint: "[lens]"
model: opus
agent: prd-analyst
allowed-tools: AskUserQuestion, Read, Write, Edit, Grep, Glob, Bash
---

# Explore — Lens-Driven Product Discovery

Explore one product lens at a time through Socratic questions. The lens order
follows product-discovery practice: understand the problem, then the people,
then their journeys, then the solution, then its boundary, then how to measure
it.

This skill writes no page. The findings of the session go to `/product:learn`.

## Step 0: the bundle must exist

Run this command:

    ls docs/product/prd/index.md

If the file is absent and a v3 PRD file is present in `docs/product/`, stop.
Tell the user: "This repository holds a v3 PRD. Run `/product:migrate` first."
Leave the v3 PRD file as it is, because the migration reads it and a second
copy becomes a second source of truth.

If the file is absent and `docs/product/` holds no v3 PRD file, this repository
has no bundle. Bootstrap it:

1. Ask the user for the product name and one sentence that describes the
   product. Use one `AskUserQuestion`. Free text through "Other" is fine.
2. Run this command:

        uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py init --title "<name>" --description "<one sentence>"

   If `uv` is not installed, run `python3` with the same path. Run the command
   with the target repository as the current directory.
3. The command prints each path that it wrote. Show that list to the user. If
   the exit code is not 0, stop and show the output.
4. Tell the user: "Run `/product:setup` to add the router block to `CLAUDE.md`."
   This skill does not write `CLAUDE.md`.

## Step 1: read the bundle

Read these files, in this order:

1. `docs/product/prd/index.md` — the bundle index.
2. `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` — the layout, the page
   format, the IDs, the relationships, the read order, and the writing style.
3. `${CLAUDE_SKILL_DIR}/../shared/product-hat.md` — the product guardrail.
4. `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style (Google
   developer documentation style) for each line of PRD text. Its application
   to the bundle is in "Writing style" in `bundle-schema.md`.
5. `docs/product/prd/product.md` — the product summary and the `lenses` map.
   The map gives the status of each lens: `not-started`, `in-progress`, or
   `complete`.
6. The `index.md` of the directory of your lens, and the `index.md` of the
   directory of each prerequisite lens. The lens catalog gives both
   directories.

Do not read every file of a directory, because a large bundle fills the
context. Open a page only when a question of this session needs that page. For a question about the whole graph, run
`uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py list`.

If `product.md` has no `lenses` map, or the map does not parse, derive the
status of each lens from the indexes: a lens whose directory index holds a
line is `in-progress`. Ask the user which of those are `complete`.

The product hat applies to the whole session. Apply the deflection procedure
each time the conversation moves to implementation.

## The lens catalog

| Lens | Key | Kind | Directory | Prerequisites |
|---|---|---|---|---|
| Problem | `problem` | Spine 1 | `prd/problems/` | none |
| Personas | `personas` | Spine 2 | `prd/personas/`, `prd/needs/` | Problem |
| Journeys | `journeys` | Spine 3 | `prd/journeys/`, `prd/needs/` | Personas |
| Capabilities | `capabilities` | Spine 4 | `prd/capabilities/` | Personas. Journeys first is better |
| Scope | `scope` | Spine 5 | `prd/scope/` | Capabilities |
| Success Metrics | `success-metrics` | Spine 6 | `prd/metrics/` | Problem, Scope |
| Business Model | `business-model` | Satellite | `prd/business/` | Problem, Personas |
| Go-to-Market | `go-to-market` | Satellite | `prd/gtm/` | Personas, Scope |
| Risks & Assumptions | `risks-assumptions` | Satellite | `prd/risks/` | Problem |

The **spine** is the ordered core. Each spine lens builds on the ones before
it. The **satellites** are optional. A satellite opens when its prerequisites
are met. A prerequisite is met when its lens status is `in-progress` or
`complete`.

Any lens can also give a Constraint (`prd/constraints/`), a Decision
(`prd/decisions/`), or a Question (`prd/questions/`). The page format of each
type is in `bundle-schema.md`.

## Step 2: pick the lens

### If an argument was given

`{{lens}}` names the lens. Match it to the `Key` column of the lens catalog.
An unknown name shows the menu instead.

### If no argument was given

First ask what the goal of this session is, then offer the lenses that fit.
Use `AskUserQuestion`:

- **Recommend** the first spine lens that is not `complete` — that is the next
  logical step. Put it first, marked "(Recommended)".
- List the other open lenses: spine lenses and satellites whose prerequisites
  are met.
- Mark each covered lens as done in its description, so the user sees the
  progress.
- State the order logic in the question, as in "Journeys need Personas first".

### The soft gate

If the chosen lens has a prerequisite that is not met:

1. Name the missing prerequisite and say why the order matters, as in
   "Journeys describe how a persona moves through the product — with no
   persona there is no one to walk the journey".
2. Recommend the prerequisite first.
3. If the user overrides, run a **minimal bootstrap**: capture just enough of
   the prerequisite in the session, as in one question that names the
   personas. `/product:learn` writes those pages and sets the lens to
   `in-progress`, so the chosen lens has something to attach to. Then go on.

## Step 3: explore through Socratic questions

Apply the Socratic method of your agent definition: one question at a time,
options with a real difference between them, build on each answer, challenge
gently. Track the coverage inside the lens. Step 4 gives the stop rule.

Use the lens guide in "Lens guides" at the end of this file. The bullets are the ground that the lens must cover,
not a fixed script. Derive each concrete option from the earlier answers of the
user and from the pages that you read in step 1.

## Step 4: close the session

Stop when the "done when" of the lens is met, when the last 2 answers gave no
new finding, or when the user says to stop.

Summarize the findings of this session in a few bullets. Group them by the
page type that each finding becomes, so `/product:learn` can write them. Then:

Ask one question: "Learn these results?" On yes, run `/product:learn` with the
findings of this session.

If each of the six spine lenses is complete, also say: "The PRD is ready for
planning — run `/product:plan` to build the roadmap."

## Lens guides

### Problem — frame the opportunity
*Grounding: problem framing, Amazon working-backwards*
- What problem exists, in one sentence that a customer would say?
- Who feels this problem, and how much does it cost them: time, money, or
  frustration?
- How do they cope today: tools, workarounds, or nothing?
- Why is now the right time to solve it?
- How large is the opportunity?
- **Done when**: a sharp problem statement, the cost of the problem, the
  current alternatives, and the "why now" are captured. Each one becomes a
  `Problem` page.

### Personas — know the people
*Grounding: personas, jobs-to-be-done*
- Which user segments exist, and which one is primary? The primary segment
  gets `primary: true`.
- What constraints does each persona work under: budget, time, skills, or
  organization?
- What criteria drive the choice of a solution?

For each persona, ask these three questions. Each answer becomes one `Need`
page in `/product:learn`, and the `kind` field records which question it answers:

| Question | `kind` |
|---|---|
| Which job must the persona do? | `job` |
| What is the pain of doing that job today? | `pain` |
| What is the wanted outcome, in the words of the persona? | `outcome` |

- **Done when**: each persona has a name, and at least one job, one pain, and
  one wanted outcome. Each `Need` page `serves` its persona.

### Journeys — walk the path of each persona
*Grounding: journey mapping*
- Take one persona at a time. What starts their journey?
- Which steps do they take today, and where does each step hurt? A new pain
  here becomes another `Need` page with `kind: pain`.
- What does the future journey look like with the product?
- Which moments matter most: the first impression, the moment of value, the
  moment of truth?
- How does the persona know that they succeeded?
- **Done when**: each primary persona has a current-state pain map and a
  future-state journey with its key moments. Each `Journey` page `serves` its
  persona.

### Capabilities — define what the product does
*Grounding: Kano model, user-story thinking*
- Which capabilities remove the worst pain of the journey?
- For each capability, ask which need, journey, persona, or problem it
  addresses. The answer becomes the `addresses` field. A capability with no
  answer is not written — say so and drop it, or ask again.
- For each capability: what must the product do? Give behavior, not
  construction.
- Which capabilities are must-be, which are performance, and which are
  delighters? The answer becomes the `kano` field.
- How do the capabilities work together in one flow? A capability that needs
  another one gets `depends_on`.
- What must happen in an unusual situation, at the level of user-visible
  behavior?
- **Done when**: each capability has a behavior description, a `kano` class,
  and at least one `addresses` target.

### Scope — draw the boundary
*Grounding: MoSCoW, walking skeleton / MVP*
- What is the smallest set of capabilities that delivers the core value end to
  end? That set is a `Scope` page with `kind: release`.
- For each capability in the release: must, should, could, or wont? The answer
  becomes the `priority` of its `includes` entry.
- What are the explicit non-goals? Each one is a `Scope` page with
  `kind: non-goal`.
- Which phases follow the first release, one line each? Each phase is another
  `Scope` page with `kind: release`.
- Which criteria gate the first release? Each one is a `Scope` page with
  `kind: release-criterion`.
- **Done when**: one release boundary, the non-goals, the later phases, and
  the release criteria exist.

### Success Metrics — define what good looks like
*Grounding: North Star metric, counter-metrics*
- Which single metric best captures the value delivered? That metric gets
  `role: north-star`.
- Which metric per goal shows the progress: acquisition, activation,
  retention, or revenue? Each one gets `role: kpi`.
- Which counter-metrics guard the primary ones against gaming? Each one gets
  `role: counter` and `guards` the metric that it protects.
- Which target and which timeline make each metric measurable? The target goes
  in the `target` field.
- For each metric, ask which problem, need, journey, or capability it measures.
  The answer becomes the `measures` field.
- **Done when**: a north-star metric, the KPIs with their targets, and the
  counter-metrics are captured.

### Business Model (satellite)
*Grounding: lean canvas*
- What is the value proposition, in the words of the customer?
- How does the product earn money: the model, the tiers, the value metric?
- What would a customer pay, and against which alternative?
- How does the product stand against its competitors?
- **Done when**: the value proposition, the pricing model, and the positioning
  are captured. Each `Business` page `serves` a persona.

### Go-to-Market (satellite)
- Who gets the product first, and why them?
- Through which channels do they find it?
- What is the core message for each persona?
- What does activation look like for a new user?
- **Done when**: the launch audience, the channels, and the messages are
  captured. Each `GTM` page `serves` a persona.

### Risks & Assumptions (satellite)
*Grounding: riskiest-assumption testing*
- Which assumptions, if wrong, kill the product? Each one is a `Risk` page
  with `kind: assumption`. A known danger gets `kind: risk`.
- Classify each one: do people want it (desirability), does the business work
  (viability), can users use it (usability)?
- How can you test the riskiest ones cheaply? The answer goes in the
  `validation` field.
- Which page does each risk threaten? The answer becomes the `threatens`
  field.
- **Done when**: the assumptions are ranked and the riskiest ones have a
  validation idea.
