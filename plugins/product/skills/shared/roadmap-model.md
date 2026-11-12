# Roadmap model

This document gives the model of the roadmap bundle. Every roadmap skill obeys it.
`bundle-schema.md` gives the layout, the IDs, the page format, and the write rule.

## Core types

| Type | Prefix | Directory | GitHub |
|---|---|---|---|
| Project | PROJECT | `projects/`, exactly one page | ProjectV2. It holds the Status options and the date fields |
| Milestone | MILESTONE | `milestones/` | Milestone. It has `target_date`, and `traces` and `drifted` as a work item has. It is a container: no parent and no state |
| Epic | EPIC | `epics/` | Issue with the issue type "Epic" |
| Feature | FEATURE | `features/` | Issue with the issue type "Feature" |
| Story | STORY | `stories/` | Issue with the issue type "Story" |
| Task | TASK | `tasks/` | Issue with the issue type "Task" |

Epic, Feature, Story, and Task are the work items. They share one field set. The
level order is Epic, Feature, Story, Task. A parent is of a higher level. A level
can be skipped: a Story can have an Epic as its parent, and a Feature can have no
parent.

These are not pages: an owner is an actor string, a label is an OKF tag, and a
pull request is a URL on a Run.

A Project page holds the OKF fields and `github: { owner, number, node_id }`. The
three GitHub keys are optional. The work-item `github` shape does not apply to a
Project.

## Agent types

| Entity | Form | Content |
|---|---|---|
| AcceptanceCriterion | Page in `criteria/`, prefix CRITERION | The criterion text, `item`, and an optional `check` (an argv list) with `check_declared_by` |
| Run | Page in `runs/`, prefix RUN | One agent execution: `agent`, `started_at`, `ended_at`, `outcome`, `spec`, `pull_request`, `commit`, and `results[]` (`criterion`, `exit_code`, `commit`) |
| Claim | A field group on the work item | `claim: { by, at, lease_expires_at, heartbeat_at }` |
| Event | One line in `roadmap/log.md` | A state change, a claim, a plan, a sync, or a run |

The script writes a Run page one time. After that the page is read-only.

An Event line has this form:

    * **State**: [STORY-12](stories/STORY-12.md) ready -> claimed, by agent:x, at 2026-09-20T14:30:00Z

A change with an approval names it before the time:

    * **State**: [STORY-12](stories/STORY-12.md) in_review -> done, by agent:x, approved by #12, at 2026-09-20T14:30:00Z

`log.md` has no frontmatter. It starts with `# Log`. Entries are under `##
YYYY-MM-DD` headings in UTC, newest heading first. A new entry goes at the top of
the heading for its date, and the script adds the heading if it does not exist.
The log is append only. `prd.py init` writes only `# Log`.

An actor string is `human:<login>`, `agent:<id>`, or `process:<id>`. Only the
scripts use `process:` actors, and each `--actor` option of `prd.py` refuses
them. `--actor` must match the whole text, so a line break is refused.

## Relationships

| Field | From → To | Number | GitHub |
|---|---|---|---|
| `parent` | Feature, Story, Task → a work item of a higher level | 0 or 1. A tree | `Issue.parent`, `addSubIssue` |
| `blocked_by` | Work item → work item | 0 or more. No cycles | `blockedBy`, `addBlockedBy` |
| `milestone` | Work item → Milestone | 0 or 1 | `Issue.milestone` |
| `owner` | Work item → actor string | 0 or 1 | The first assignee, for a `human:` actor only |
| `discovered_from` | Work item → work item | 0 or 1 | None |
| `item` | AcceptanceCriterion, Run → work item | 1 | None |
| `results[].criterion` | Run → AcceptanceCriterion | 0 or more | None |
| `traces` | Milestone, work item → PRD page, with a `hash` | 0 or more | None. The issue body shows the links |

A `traces` entry is `- { to: prd:/capabilities/CAPABILITY-03.md, hash: a1b2c3 }`.
An Epic and a Feature must have one trace or more, or the checker gives a warning.
A Story or a Task stores a trace only when it narrows the traces of its parent.

A new Story with a `parent` and no `milestone` takes the milestone of its parent.
When the parent has a milestone, the checker gives a warning for a Story with no
milestone or with another milestone. A later change of the milestone of the
parent does not change the milestone of its Stories.

These values are derived and not stored: the children of an item, `blocks`, the
criteria of an item, the runs of an item, the items of a milestone, and "traced
by" on a PRD page. The script writes each derived value into the `LINKS` block or
into a status table. Never store one in the frontmatter, because `prd.py regen`
derives it again and a stored copy goes out of date.

## Fields of a work item

- OKF: `type`, `title`, `description`, `tags`, `generated`, and `status`.
- `state`: `backlog`, `ready`, `claimed`, `in_progress`, `in_review`, `blocked`,
  `done`, `released`, or `cancelled`.
- Dates: `planned_start_date`, `planned_end_date`, `actual_start_date`, and
  `actual_end_date`.
- `github: { node_id, number, url, synced: { state, owner }, pushed_hash }`.
- `claim: { by, at, lease_expires_at, heartbeat_at }`.
- `traces`, and `drifted`, which lists the trace targets whose hash changed.
- `size`: `S`, `M`, or `L`. Stories only. It replaces the v3 estimate.
- `spec`: the spec file that builds the item, as a path from the repository root,
  or `none` when the item needs no build. Stories only. `/product:specifying-stories`
  writes it, and `/product:work` refuses a Story that has no value.
- `aliases`, which holds each old ID.

`status` is the page lifecycle. `state` is the work status. The two fields are
different.

## State rules

- **One write path.** The commands `claim`, `release`, `expire`, and `regen`
  call `prd.py state`. Never edit `state` with an edit tool, because
  `prd.py state` is the one write path and logs each change.
- **The log.** Each change adds one Event line to `roadmap/log.md`.
- **Computed values.** `ready` and `blocked` are computed from `blocked_by`. For an
  item in `ready` or `blocked`, the script sets `blocked` when one blocker or more
  is not `done`, `released`, or `cancelled`. If not, it sets `ready`. Ask for `ready`; the
  script gives the computed value. `prd.py regen` applies this rule to each item,
  and it writes one Event with the actor `process:regen` for each change that it
  makes.
- **Promotion.** A new item starts in `backlog`. `/product:plan` promotes the items of
  the chosen slice.
- **Agent transitions.** An `agent:` actor can make each change of an Epic, a
  Feature, a Story or a Task when the call gives `--approved-by`: a PR URL or
  `'#<n>'`, a D-id, an `ANSWER:<id>`, a hitl card link (a Slack message link), or
  another URL. `prd.py` checks the shape only. Five changes need no approval, because
  they take work and give it back: `ready -> claimed`, `claimed -> in_progress`,
  `in_progress -> in_review`, `claimed -> ready` and `in_progress -> ready`. A change
  to `cancelled`, and a reopen from `done` or `released`, need a hitl card link or a
  D-id that hitl decided. A Story goes from `backlog` to `ready` only when its `spec`
  file is in the tree. A `human:` actor can set each state with no approval.
  An agent writes its own `agent:<id>` actor, because only a person is a
  `human:` actor (DECISION-03).
- **Parents.** The state of a parent is stored, not computed. The checker gives a
  warning when a parent is `done` or `released` and a child is open.
  `/product:roadmap-sync` proposes `done` for a parent whose children are all `done`,
  `released`, or `cancelled`.
- **Actual dates.** The script sets `actual_start_date` at the first change to
  `in_progress`, and `actual_end_date` at the change from an open state to `done`
  or `released`. A change between `done` and `released` keeps the date. A change
  from `done` or `released` to another state removes it. No other writer sets these
  two fields.
- **Released.** `released` follows `done` in the flow, and it is a closed state. A
  `human:` actor, or an agent with an approval, sets it with `prd.py state`.
  `prd.py release` ends a claim and sets `ready`. It does not set `released`.
- **Progress.** Progress is derived for display: the children that are `done` or
  `released`, divided by the children that are not `cancelled`.

## Status tables

A status table is between `<!-- STATUS:START (generated, do not edit) -->` and
`<!-- STATUS:END -->`.

The columns are Item, State, Progress, Owner, Blocked by, and Drift.

| Page | Rows |
|---|---|
| Project | The milestones and the epics only |
| Milestone | Its epics and its features |
| Feature | Its stories |
| Story | Its tasks and its criteria |

No page holds the full tree, so each page stays below 100 lines.

A Milestone row has no state and shows `-`. The Progress cell is `<done>/<not
cancelled> (<P>%)`, where P is an integer that is rounded down. An item with no
children shows `-`. An empty cell shows `-`. A drifted Story or Task also shows
its parent Feature as drifted, but the `drifted` field of the parent does not
change.

`prd.py regen` writes each status table. Never edit one, because the next `regen`
overwrites a hand edit. The page hash removes
the STATUS block, the same as the LINKS block.

## Closed lists

| Enum | Values |
|---|---|
| `WorkState` | `backlog`, `ready`, `claimed`, `in_progress`, `in_review`, `blocked`, `done`, `released`, `cancelled` |
| `Size` | `S`, `M`, `L` |
| `RunOutcome` | `passed`, `failed`, `not-checked`, `abandoned` |

The schema `schema/product.yaml` is the source of these lists. When this table
and the schema disagree, the schema is correct.

## How the v3 roadmap maps

This table is for a reader of a migrated roadmap.

| v3 | Now |
|---|---|
| Milestone, which is a phase such as MVP or Phase 2 | `Milestone`. `target_date` is optional. The checker gives a warning when it is absent |
| Theme | v3 has no theme item. The v3 skill wrote each theme as a milestone |
| The `Not Planned` milestone | A milestone with no items |
| `Not Started` | `ready` or `blocked`, computed from `blocked_by` |
| `In Progress` | `in_progress` |
| `Completed` | `done` |
| `Needs Review` | `drifted` is not empty. `state` keeps its value |
| A milestone that depends on a milestone | Dropped as a relationship. The migration writes it as a sentence in the milestone body |
| An acceptance criteria checkbox | One AcceptanceCriterion page for each checkbox |
| A T-shirt estimate | `size` on the story |

A migrated roadmap holds no Epic page, and a migrated Feature has no `parent`.
`/product:themes-identify` writes the first Epic pages after the migration.
