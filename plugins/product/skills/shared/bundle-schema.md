# Bundle schema

This document gives the format of the two OKF bundles. Every product skill obeys it.

## Layout

`docs/product/prd/` holds the PRD bundle. `docs/product/roadmap/` holds the roadmap bundle.

| Path | Type |
|---|---|
| `prd/index.md` | the bundle index. It holds `okf_version` |
| `prd/log.md` | the log. Save and Migrate entries |
| `prd/product.md` | Product |
| `prd/problems/` | Problem |
| `prd/personas/` | Persona |
| `prd/needs/` | Need |
| `prd/journeys/` | Journey |
| `prd/capabilities/` | Capability |
| `prd/experiences/` | Experience |
| `prd/scope/` | Scope |
| `prd/metrics/` | Metric |
| `prd/business/` | Business |
| `prd/gtm/` | GTM |
| `prd/risks/` | Risk |
| `prd/constraints/` | Constraint |
| `prd/decisions/` | Decision |
| `prd/questions/` | Question |
| `roadmap/index.md` | the bundle index. It holds `okf_version` |
| `roadmap/log.md` | the log. Plan, Sync, State, Claim, and Run entries |
| `roadmap/projects/` | Project. The bundle has exactly one Project page |
| `roadmap/milestones/` | Milestone |
| `roadmap/epics/` | Epic |
| `roadmap/features/` | Feature |
| `roadmap/stories/` | Story |
| `roadmap/tasks/` | Task |
| `roadmap/criteria/` | AcceptanceCriterion |
| `roadmap/runs/` | Run |

Each directory has an `index.md`. A directory that holds closed work items also has a generated
`closed.md` page, with `type: ClosedItems`. A directory with no pages does not exist.
`docs/product/archive/` holds the v3 files that the migration moves. It is not a bundle.

## IDs

- An ID is `<PREFIX>-<NN>`. The number has two digits or more: `CAPABILITY-03`, `STORY-112`.
- The file name is the ID plus `.md`. The name, the `type`, and the directory must agree.
- A Run is the exception. Its ID is `RUN-<UTC date>-<UTC time>-<4 hex characters>`.
- An ID is permanent. A removed page gets `status: deprecated`. The file stays.
- `aliases` holds each old ID, as in `aliases: [CAP-3]`. `prd.py resolve` accepts an ID or an alias.
- Never choose an ID yourself, because `prd.py new` assigns it and a hand-chosen ID can collide.

## Page format

Rules for each page:

1. The frontmatter holds the OKF fields first: `type`, `title`, `description`, `status`, `tags`,
   and `generated`. The type fields follow. The relationships come last. The script writes the
   keys in the order that the schema gives. The frontmatter has no comments.
2. `generated` is the OKF provenance field. It is a mapping `{ by: <string>, at: <UTC timestamp> }`.
   The save code writes `generated` on each page.
3. `status` is the page lifecycle: `draft`, `stable`, or `deprecated`. The work status of a roadmap
   item is `state`.
4. The body starts with `# <ID>: <title>`. The page text follows. `product.md` and `closed.md` have
   no ID, so their heading is the title only.
5. The script writes the `LINKS` block. It shows each stored relationship and each derived one.
   Never edit the block, because `prd.py regen` writes it and overwrites a hand edit.
6. A link in the frontmatter is bundle-relative and starts with `/`, as in `/needs/NEED-02.md`.
7. A link in the body is relative to its own file, as in `../needs/NEED-02.md`. GitHub and editors
   do not resolve a `/` link from the bundle root, so a body link never uses that form.
8. A target in the other bundle starts with the bundle name, as in
   `prd:/capabilities/CAPABILITY-03.md`. Only a roadmap page points to the other bundle. A PRD page
   stores no link to the roadmap, because the roadmap is built from the PRD and
   the PRD does not depend on it. `prd:`
   names the graph `prd`. OKF has no cross-graph link form, so a general OKF consumer does not
   follow it.
9. The description is the router. An agent sees only the index line before it opens a page. Write
   the description in the words of the task, and make it specific.
10. A Story holds `spec`: the path of the spec file that builds it, from the repository root, or
    `none` when the Story needs no build. `/product:specifying-stories` writes the field, and
    `/product:work` refuses a Story that has no value. The field is a path and not a closed list.

This is a page:

```markdown
---
type: Capability
title: Book a slot in under a minute
description: A customer books a free slot in less than one minute, with no account.
status: stable
tags: [booking]
aliases: [CAP-3]
kano: must-be
addresses: [/needs/NEED-02.md, /journeys/JOURNEY-01.md]
depends_on: [/capabilities/CAPABILITY-01.md]
---

# CAPABILITY-03: Book a slot in under a minute

The customer selects a day and sees each free slot. One tap books the slot.

<!-- LINKS:START (generated, do not edit) -->
## Links

- addresses: [NEED-02: Booking takes too long](../needs/NEED-02.md)
- depends on: [CAPABILITY-01: See free slots](CAPABILITY-01.md)
- traced by: [FEATURE-04: Scheduling](../../roadmap/features/FEATURE-04.md)
<!-- LINKS:END -->
```

## Relationships

| Field | From → To | Number |
|---|---|---|
| `serves` | Need, Journey, Business, GTM → Persona | 1 or more for Need and Journey |
| `addresses` | Capability → Need, Journey, Persona, Problem | 1 or more |
| `describes` | Experience → Capability, Journey | 1 or more |
| `depends_on` | Capability → Capability | 0 or more. No cycles |
| `includes` | Scope → Capability, with a `priority` | 0 or more |
| `measures` | Metric → Problem, Need, Journey, Capability | 0 or more |
| `guards` | Metric with `role: counter` → Metric | 0 or more |
| `threatens` | Risk → any PRD page | 0 or more |
| `constrains` | Constraint → any PRD page | 0 or more. Empty means the full product |
| `about` | Decision, Question → any PRD page | 0 or more |
| `supersedes` | Decision → Decision | 0 or 1 |

`includes` is a list of mappings: `- { to: /capabilities/CAPABILITY-03.md, priority: must }`. Each
other field is a list of paths.

**One rule for the direction.** Store a relationship one time, on the page of the later lens, and
point it to the earlier lens. A save of one lens does not change the frontmatter of an older page.
The script derives the opposite direction into the `LINKS` block.

## Indexes

- Each directory has an `index.md`. Each line is `* [<ID>: <title>](<file>) - <description>`. The
  script copies the description from the page.
- A PRD type index is one flat list.
- A work item index groups its lines under one heading for each milestone. An item with no
  milestone goes under "No milestone".
- A work item index lists open items only. An item with `state: done`, `state: released`, or `state: cancelled` goes to
  `closed.md` in the same directory.
- `runs/index.md` groups runs by work item and shows the last 10 for each item.
- In each list, lines are sorted by ID number.
- Never edit an index or a `closed.md`, because `prd.py regen` writes them and overwrites a hand
  edit.

## The read order

1. Read the bundle-root `index.md`.
2. Read the `index.md` of the directory that you need.
3. Open one page. The frontmatter is at the top, so the first 30 lines give each typed field.
4. Follow the links of that page.

Do not read every file of a directory, because a large bundle fills the context. For a question
about the full graph, call the script: `list`, `ready`, `check`, or `drift`. From the bundle root, each page is two steps away.

## The write rule

After your last page write, run these two commands:

    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py regen
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/prd.py check

If `uv` is not installed, run `python3` with the same path. Run each command with the target
repository as the current directory. If one command gives an exit code that is not 0, stop. Show
the output to the user. Do not report success, because the bundle is in a state that the checks
reject. A warning does not stop you, but you must show it.

Never write a status table, a percentage, or a hash by hand, because `prd.py regen` writes the
tables and the percentages, `prd.py new`, `prd.py drift --accept`, and `prd.py migrate --finish`
write each hash, and a hash written by hand hides a drift.

`prd.py check` is a strict producer linter for this bundle. It is not a general OKF consumer: it
rejects a page that a general OKF consumer would accept.

## Closed lists

| Enum | Values |
|---|---|
| `OkfStatus` | `draft`, `stable`, `deprecated` |
| `NeedKind` | `job`, `pain`, `outcome` |
| `ScopeKind` | `release`, `non-goal`, `release-criterion` |
| `ExperienceKind` | `structure`, `state-rule`, `interaction-rule` |
| `MetricRole` | `north-star`, `kpi`, `counter` |
| `KanoClass` | `must-be`, `performance`, `delighter` |
| `RiskKind` | `risk`, `assumption` |
| `Priority` | `must`, `should`, `could`, `wont` |

The schema `schema/product.yaml` is the source of these lists. When this table and the schema
disagree, the schema is correct.

## Writing style

All page text that a product skill writes follows the Google developer documentation style guide. The
rules are in `${CLAUDE_PLUGIN_ROOT}/skills/google-style/SKILL.md`. Read that file before you write
bundle text. Apply it to each line that you write.

**In scope**: titles, descriptions, page text, the body of `product.md`, the names and the text of
milestones, epics, features, stories, and acceptance criteria, and text that the migration writes.

**Out of scope** — never change these for style:
- IDs and aliases. A consumer matches them exactly.
- Frontmatter keys and frontmatter values.
- Links, in the frontmatter and in the body.
- Hashes, and each `traces` entry that holds one.
- The generated `LINKS` block and the generated `STATUS` block.
- The fixed headings. These are the page heading `# <ID>: <title>`, the generated headings
  `## Links` and `## Status`, the index heading `# <directory>`, and the index group headings
  `## <ID>: <title>` and `## No milestone`. A skill finds these headings by their exact text, so
  they keep their case.
- A direct quote from a user or from research. Keep a quote as it is.

**How the rules apply to a page**:
- Use sentence case for each heading that you add, and for each title and item name. Do not change
  a fixed heading.
- Use active voice and present tense. Name the actor: "The planner exports the schedule", not "The
  schedule is exported".
- Page text describes what a persona or the product does, so it uses the third person. Use "you"
  only in text that tells the reader what to do.
- Use "must" for a requirement, "can" for an ability, and "might" for a possibility. Do not use
  "should" or "may" in page text, because each of them can mean a requirement or a possibility.
- Write a date as `2026-08-18`. Use the serial comma. Put code, commands, paths, and literal values
  in code font.
- Cut a filler word, such as "simply", "easily", or "just".

**Hashes**: the script hashes the page body. Apply the style to text that you write or change in
this session. Do not restyle a page that the session did not change, because a new body gives a new
hash and the drift check flags each trace to that page. When the user asks to restyle an existing
page, do it as a normal edit: the drift check runs, and the user clears each flag.
