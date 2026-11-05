---
description: Turn one Feature and its Stories into relay-ready spec files — infer each decision from ADRs, PRD decisions, and built specs, ask only the open ones, write accepted ADRs, and set the Stories to ready
argument-hint: "[FEATURE-ID]"
model: opus
allowed-tools: AskUserQuestion, Read, Write, Edit, Bash, Grep, Glob, Agent, Skill
---

# Specify stories — one Feature to relay-ready specs

Turn one Feature and its Stories into one spec file or more that
`/relay:implement --spec <path>` accepts.

Make the technical decisions of the feature one time. The table under "Where
a decision comes from" gives the source of each decision.

Write as an engineer. Name the code that changes and the interfaces. Name
the migration and the test of each acceptance criterion. The skill writes no
product text. The product words stay in the Story page and in its criteria.

This skill plans no task; relay does. It writes no code. It reviews no ADR; a
skill of the architecture plugin does.

Read these files before you write text on a page:

- `${CLAUDE_SKILL_DIR}/../google-style/SKILL.md` — the writing style.
- `${CLAUDE_SKILL_DIR}/../shared/bundle-schema.md` — the page format, the IDs,
  the read order, and the write rule.
- `${CLAUDE_SKILL_DIR}/../shared/roadmap-model.md` — the roadmap types, the
  states, and the `spec` field.

Run the script from the target repository:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py <subcommand>
```

If `uv` is not available, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py`
instead. The exit code is the verdict. Read the exit code, because the text alone can
look correct after a failure.

A person runs this skill with the actor string `human:<login>`. An agent session
uses its own `agent:<id>`, because only a person is a `human:` actor, and gives
`--approved-by` on each `state` call of Step 6. Get `<login>` one time:

```bash
gh api user -q .login
```

## Step 0: the preconditions

Run this command:

    ls docs/product/prd/index.md

If the file is absent and a v3 PRD file is present in `docs/product/`, stop.
Tell the user: "This repository holds a v3 PRD. Run `/product:migrate` first."
Leave the v3 PRD file as it is, because the migration reads it and a second
copy becomes a second source of truth.

If the file is absent and `docs/product/` holds no v3 PRD file, this
repository has no bundle. Tell the user to run `/product:explore` first, which
bootstraps the bundle. Then stop.

The spec shape and the self-review list of Step 4 come from the superpowers
`brainstorming` skill, so that plugin must be on disk:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/check-superpowers.sh
```

Read the exit code only. On a code that is not 0, stop and tell the user:
"Install the superpowers plugin first."

Then choose the branch:

```bash
git status --porcelain
git rev-parse --abbrev-ref HEAD
```

- If `git status --porcelain` prints one line or more, stop. Tell the user to
  commit the changes or to set them aside, then to start the skill again.
- If the branch is the default branch, create `spec/<FEATURE-ID>` off it and
  check it out. Do this before you write any file.
- If the branch is another branch, ask one question: "Write the spec on this
  branch, or on a new `spec/<FEATURE-ID>` branch?"
- If the chosen branch already has an open pull request, add the work to that
  pull request. Step 6 then opens no second one.

Never commit to the default branch, because the spec reaches it through the
reviewed pull request of Step 6.

## Step 1: read the context

Read these, in this order. Do not read every file of a directory, because a
large bundle fills the context.

1. The Feature page. Its `traces` name the PRD pages. Read those pages and
   nothing else of the PRD bundle, with one exception: read the index of
   `docs/product/prd/decisions/`, then each Decision page whose `about` names
   a traced page.
2. Each Story page whose `parent` is the Feature, and each
   AcceptanceCriterion whose `item` is one of those Stories:

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py list Story --where parent=/features/FEATURE-03.md --fields title,state,spec,size
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py list AcceptanceCriterion --fields item,title,check
   ```

   The second command reads the criteria directory one time. Group its lines by
   `item` yourself, and keep the ones whose `item` is a Story of the first
   command. One call for each Story re-reads every criterion page each time.

3. The ADR register, through the `architecture:ask` skill in
   `subagent` mode. Ask one question for each decision area of the fixed list
   in Step 2. Step 2 then drops each area that does not apply. If
   `.claude/adr.json` is absent, note "no ADR corpus" and go on.
4. Every file in `docs/superpowers/specs/` whose frontmatter has `feature` or
   `stories`. Read the frontmatter and the Decisions table only. Mark each
   file as built or not built with this rule: a spec counts as built when
   every Story of its `stories` list has `state: done`, or when a Run page
   names the spec with `outcome: passed`. A Run with `not-checked`, `failed`,
   or `abandoned` does not count, and a later `failed` Run on one spec
   cancels an earlier `passed` Run. A spec with no `stories` field counts as
   not built.
5. A summary of the code, from the `relay:scout` agent. Test for relay first:

   ```bash
   bash ${CLAUDE_PLUGIN_ROOT}/scripts/check-relay.sh
   ```

   On exit code 0, dispatch the agent with the `Agent` tool and
   `subagent_type: relay:scout`. The relay plugin registers the agent under
   that name. The bare name `scout` finds no agent. The Agent tool fills no `{{...}}` placeholder of
   the agent body, so give both values as named lines of the prompt text:

   ```
   TASK_DESCRIPTION: <the feature, in one or two sentences>
   CONTEXT_SUMMARY_OUTPUT_PATH: ${TMPDIR:-/tmp}/prd-specifying-stories-FEATURE-03-context-summary.md
   ```

   Never commit that file, because it is a build artifact. After the agent ends, read
   the path from the `CONTEXT_SUMMARY_PATH=` line of its final text, and read
   that file.

   On a code that is not 0, or when the `CONTEXT_SUMMARY_PATH=` line is
   absent, or when the file is absent or empty, treat relay as absent. Then
   run a short `Glob` and `Grep` sweep of the directories that the traced
   capabilities of the Feature name. Say in your report which of the two
   paths you took.
6. The system design, when `.claude/knowledge.json` names the graph
   `system-design`. Ask `system-design:ask` (or run
   `knowledge.py pages system-design --type Component`) for the components
   whose `realizes` names a Capability of the Feature, the Area pages, their
   `area_state`, the Convention pages, and the Deferred pages.

   Find which areas the Feature touches: the `areas` of each of those
   components, plus `conventions`. When no component realizes a Capability of
   the Feature, each `open` area and each `fog` area counts as touched.

   Warn one time when the graph is absent, or when an area that the Feature
   touches is `open` or `fog`: "The system design is incomplete for this
   Feature. Run `/system-design:learn` first for a complete design." Then ask
   one question: go on, or stop. It does not refuse.

## Step 2: list the decisions

Write a Decision Ledger in the session. Write no file yet. One row for each
technical decision that the feature needs. Seed the rows from this list, and
drop each area that does not apply:

data model and storage · interfaces (API, CLI, events) · UI surface ·
migration and compatibility · error handling · test strategy · rollout and
flags · observability · security and permissions · third-party dependencies ·
performance budget.

Each row holds four values: `decision`, `choice`, `source`, and `confidence`.
`confidence` is `inherited`, `inferred`, or `open`. Find the source with the
table below.

## Where a decision comes from

| Source | Treatment |
|---|---|
| ADR with status `accepted` | **Inherit.** Cite the ADR filename. |
| PRD Decision page in `prd/decisions/` | **Inherit.** Cite the page ID. |
| Past spec that counts as built, same choice in the same area, and no later ADR or spec contradicts it | **Inherit.** Cite the spec path. |
| Code convention from Step 1 item 5, with no document behind it | **Infer.** Cite the file. Put the row in the Assumptions list. |
| ADR with status `proposed` | **Ask.** Use it as the recommended option. |
| Past spec that does not count as built | **Ask.** Use it as the recommended option. |
| System design, a `decided` area with an `accepted` ADR | **Inherit.** It binds the spec. Cite the ADR. |
| System design, a `decided` area with a `proposed` ADR or no ADR | **Ask.** It is an open decision to confirm. Use it as the recommended option. |
| System design, an `open` or `fog` area | **Ask.** It is a question for the person. Show the area name. |
| System design, a Deferred page | Out of scope. Cite the page and its trigger. |
| System design, a `deferred` area | Out of scope. Name the area. |
| Two sources that disagree | **Ask.** Show both. |
| No source | **Ask.** |

A row whose treatment is "Out of scope." is not asked and does not go into
the Decision Ledger. It goes into the **Out of scope** section of the spec in
Step 4, with the Deferred page or the area name as its reason.

Show the full ledger one time, and mark each `inherited` and each `inferred`
row. Then ask one question: "These rows come from existing sources. Reject any
row you want to decide again." This is the only review of those rows.

- Four `inherited` and `inferred` rows or fewer: ask one multi-select
  `AskUserQuestion`, with an explicit "reject none" option.
- Five rows or more: ask for free text that names the row numbers, and accept
  "none".

Move each rejected row to `open`.

## Step 3: ask the open rows

This step asks three kinds of question, and no other kind: one question for
each `open` row, one question for the Stories that need no build, and one
question for the spec grouping. Ask them in that order.

Ask one `AskUserQuestion` for each `open` row, in dependency order: a row that
other rows depend on comes first. When two rows depend on each other, ask the
one with the lower row number first.

Each row question has 2 or 3 options, one recommendation, and one line for
each option that names its consequence. Each row question also has an "other,
I will say it" path, and an answer on that path is the choice.

Record each answer with the source `human:<login>, <date>`.

If the person stops the session part way, write nothing. The next session
starts again from Step 1.

Then ask the no-build question: "Which Stories of this Feature need no
build?" Name each Story that has no `spec` field yet.

- Four Stories or fewer: ask one multi-select `AskUserQuestion`, with an
  explicit "all need a build" option.
- Five Stories or more: ask for free text that names the Story IDs, and
  accept "none".

Each Story that the person names gets `spec: none` in Step 6. No spec covers
it, and no grouping question names it.

Then ask one question for the spec grouping of the other Stories. The default
is one Story, one spec. Two Stories share a spec only when they cannot ship
apart. Propose the groups, say why any two Stories share a spec, and let the
person change the groups. Each Story belongs to at most one spec.

## Step 4: write the specs

Write one file for each group:
`docs/superpowers/specs/<date>-<FIRST-STORY-ID>-<slug>-design.md`. The slug
holds no space. `<FIRST-STORY-ID>` is the lowest Story ID of the group.

The frontmatter:

```yaml
---
title: "<feature title>: <group title>"
feature: FEATURE-03
stories: [STORY-12, STORY-13]
kind: build
gh_issue: 42
lifecycle_state: draft
inherits: [SCENARIO-02, CONVENTION-01]
session: <CLAUDE_CODE_SESSION_ID>
---
```

- `kind` is `build` or `spike`.
- `gh_issue` is the `github.number` of the lowest Story ID of the group that
  has one. If no Story of the group has one, leave the key out.
- `lifecycle_state` starts at `draft`.
- `inherits` holds each ID of the system design that this spec inherits: a
  `SCENARIO-<NN>`, an `INTERFACE-<NN>`, a `COMPONENT-<NN>`, a `CONVENTION-<NN>`,
  or a `DEFERRED-<NN>`, for example `inherits: [SCENARIO-02, CONVENTION-01]`.
  An old ID (`QS-n`, `C-<slug>`) resolves through `aliases`. Write
  `inherits: [<IDs>]` into the spec frontmatter, and leave the key out when
  the spec inherits nothing. A spec choice that contradicts an inherited
  entry is a conflict row: show both and ask.
- `session` holds the `CLAUDE_CODE_SESSION_ID` variable of this session. It is
  the same identifier that `plugins/relay/scripts/retro-run.sh` uses to find
  a transcript. An ADR names this spec in its `parent_spec` field, so a reviewer
  of the ADR finds the session through the spec. When the variable is not
  set, write `session: unknown` and tell the person.

The body holds these sections, in this order:

1. **Problem** — in the words of the Story and its traced PRD pages.
2. **Decisions** — the full ledger of the feature, so each spec is
   self-contained for relay. Columns: #, Decision, Choice, Source.
3. **Design** — one section for each area of the ledger. Name the code paths.
   Give each AcceptanceCriterion of the covered Stories with the test that
   proves it.
4. **Build order** — the steps, in order, one Story at a time.
5. **Assumptions** — each `inferred` row, with the file it came from.
6. **Risks** — each risk, with the signal that shows it has
   happened.
7. **Out of scope** — what this spec does not build, with the Story or the
   spec that does.

A `kind: spike` spec replaces sections 3 and 4 with **Question**, **Probe**,
and **Stop rule**, and names the decision that the probe must produce.

Self-review each spec against this list: placeholders, contradictions,
ambiguity, and scope. Fix each finding inline. Then ask the person to review
the spec. On "change", edit the spec and self-review it again. On "approve",
set `lifecycle_state: specified`.

## Step 5: write the ADRs

A decision becomes an ADR when it binds code outside the Stories of this
feature: a shared convention, cross-cutting infrastructure, or an external
interface. A decision that only the code of this feature must obey stays in
the Decisions table of the spec.

For each decision with the source `human:` that meets that rule, invoke the
`architecture:learn` skill with the `Skill` tool. Its argument is one
`[decision]`: give the decision in one sentence. In the same message, give
these facts for the Context and the Alternatives sections of the ADR:

- each option of the Step 3 question, one line each
- the chosen option
- the parent spec, as a path from the repository root, for example
  `docs/superpowers/specs/2026-10-02-STORY-12-slug-design.md`

That skill passes the parent spec to `adr_new.py` as `--parent-spec`.
`adr_new.py` prints the path of the new file. Read the path from that
output, and do not list the ADR directory before and after to find the
difference, because the printed path is exact and a directory difference can
catch a file that another session wrote.

Pass no `--evidence`. That argument holds a dated measurement only, and a
session ID is not one. The session ID is in the `session` key of the spec.

Read the frontmatter of the new ADR. The new ADR has
`lifecycle: accepted` and `status: stable`. Do not change or add a field of
the ADR, because the architecture plugin owns that frontmatter and lints it.
Name the ADR in your report as "no `parent_spec`" when it has no
`parent_spec` key.

Then change the Source of the ledger row in each spec to the ADR filename.

If the skill fails, or prints no path, keep the Source as `human:<login>,
<date>`. Name the decision in your report as "no ADR".

## Step 6: link, set the state, and commit

1. Edit each covered Story page: `spec: <path>`, as a path from the repository
   root. Edit each Story that the person named in the no-build question of
   Step 3: `spec: none`. Then move each `spec: none` Story to its end state:

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py state STORY-14 cancelled --actor human:<login>
   ```

   The end state is `cancelled` and not `done`, because `done` writes an
   `actual_end_date` and counts a Story that shipped nothing as delivered. An
   agent runs `--actor agent:<id> --approved-by <approval>`, where the approval is
   a hitl card link or a D-id that hitl decided.

2. Set each covered Story of an approved spec to `ready`:

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py state STORY-12 ready --actor human:<login>
   ```

   An agent runs `--actor agent:<id> --approved-by <approval>`, with the hitl card
   link or the D-id that approved the spec. The spec PR does not exist yet at this
   step. The spec file is in the tree, because Step 4 writes it.

   A `spike` spec sets its Story to `ready` as well. `product:work` reads `kind`
   and calls no relay for it.

   Read the exit code of each `prd.py state` call of items 1 and 2. On a
   code that is not 0, stop and show the output. Do not commit, and open no
   pull request. Do not report success.

   A failed call leaves the Story pages part way, so a commit ships them and a
   report of success hides the failure.

   The command prints the state that it stored. For a `ready` request, read
   that line. The script stores `blocked` when a page in `blocked_by` is not
   done. For a `blocked` Story, name the Story and its open blockers in your
   report. Do not count that Story as ready.

   A `blocked` Story waits on its blockers, so it is not ready for an agent.

3. The write rule:

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py regen
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py check
   ```

   If one of them exits with a code that is not 0, stop, show the output, and
   report the failure. Do not report success, because the bundle is in a
   state that the checks reject.

4. On the branch of Step 0, commit the spec files, the Story pages,
   `roadmap/log.md`, and the ADRs. Push the branch, and open one draft pull
   request. The body lists each spec, each ADR, and one `Refs #n` line for
   the issue of each covered Story. Do not write `Closes #n`, because a merged
   spec pull request then closes each Story issue before any code exists. The
   relay build pull request delivers the Story, so it closes the issue.

## Your report

Give the user these facts:

- each spec file, with its `kind` and its `lifecycle_state`
- each ADR file, with `lifecycle: accepted`, and each ADR with no `parent_spec`
- each Story and its new state, and each `blocked` Story with its blockers
- each `inferred` row of the ledger, and the file it came from
- the pull request URL
- whether the code summary came from the `relay:scout` agent or from a sweep
