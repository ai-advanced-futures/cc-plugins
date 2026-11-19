# Plan roadmap model

This model adapts Product's roadmap concepts to the Plan command line and Beads. `cli.md` describes the write interface. `planning.md` describes the planning decisions.

## Types and relationships

The following table gives the planned item types and their roles:

| Type | Role | Relationships |
| --- | --- | --- |
| Project | The product plan container | Project description and metadata |
| Milestone | One product phase, including an empty future phase | PRD traces and an optional target date |
| Epic | A group of capabilities that gives value together | Milestone and PRD traces |
| Feature | A deliverable user capability | Optional higher-level parent, Milestone, and PRD traces |
| Story | One user's action and benefit | Feature parent, inherited or explicit Milestone, optional narrower traces, and spec |
| Task | Engineering work within a Story | Higher-level parent and optional narrower traces |
| Criterion | One acceptance result with its own ID | Exactly 1 work item through `item` |

The CLI assigns new IDs in the form `PLAN-TYPE-NN`, such as `PLAN-STORY-01`. An imported item retains its Product ID. Typed numeric selectors use the ID's number suffix. A command's returned ID is the input for later commands. A Criterion is an item with its own ID, not a checkbox hidden in a Feature or Story body.

`parent` makes a tree of higher-level work. `milestone` names the phase. `blocked_by` names work that must close first. `owner` names the responsible actor. A claim names the actor that temporarily holds work. Ownership and a claim are separate: assignment is not a claim or a state transition. A bare owner name maps to `human:NAME`; `-` clears the owner. Explicit actor forms remain available.

PRD references keep their source identity, such as `prd:/capabilities/CAPABILITY-03.md`. Plan code captures the source hash. A Story without a direct trace uses its parent's requirement context. A later change to a parent Milestone does not change existing children automatically.

## Beads link limits

The supported store is Beads `bd` 1.3.4 with embedded Dolt. External Dolt servers are outside this supported setup.

Beads dependencies show a reduced view of Plan relationships. For each target, the adapter writes at most 1 Beads edge. A parent link takes priority and uses `parent-child`. Other target links use `related`, including blockers, milestones, discovery links, and criterion item links.

The full typed relationships remain in `metadata.plan`, including each parent, blocker, milestone, discovery, and item relation. Plan computes readiness from that typed data. Raw `bd ready` is not Plan's ready view; the supported ready query is Plan's `ready` command.

## Work states

The stored work states are:

`backlog`, `ready`, `claimed`, `in_progress`, `in_review`, `blocked`, `done`, `released`, and `cancelled`.

A new work item starts in `backlog`. A Milestone is a container rather than a work-state target. A Criterion belongs to work rather than following the work-state flow.

`ready` and `blocked` depend on blockers. A requested `ready` state becomes `blocked` while a blocker remains open. `done`, `released`, and `cancelled` close a blocker. The status command's result is the state to report.

A parent's state is stored separately from its children's states. Closing all children does not itself close a parent. A closed parent with open children is a check finding. Display progress is derived from closed children rather than authored percentages.

## Actors and approval

The actor forms are `human:LOGIN` and `agent:ID`. The executing agent uses its own `agent:ID`. A human actor identifies a command that a person runs. An actor is evidence about the executor, not a way to obtain broader permission.

These five agent transitions need no approval reference:

| From | To | Meaning |
| --- | --- | --- |
| `ready` | `claimed` | Take work |
| `claimed` | `in_progress` | Start work |
| `in_progress` | `in_review` | Request review |
| `claimed` | `ready` | Return unstarted work |
| `in_progress` | `ready` | Return work |

Other agent transitions need the approval reference accepted by Plan code. Promotion of a Story from `backlog` to `ready` also needs an existing spec file inside the configured source root. Cancellation and reopening closed work need the decision evidence required by code. A plan conversation is not an invented approval ID. CLI refusals identify missing evidence.

The CLI records state changes and manages actual dates. Page lifecycle (`draft`, `stable`, or `deprecated`) is separate from work state. `set ID lifecycle VALUE` changes the page lifecycle through its `status` field. Work state uses the dedicated `status` command. Other `set` values include accepted content fields and planned dates; actual dates remain CLI-managed. Beads' own write commands do not apply Plan's guards, so the supported Plan write interface is `plan.py`.

## Claims

A claim holds `by`, `at`, `lease_expires_at`, and `heartbeat_at`. The lease limits how long a claim lasts without renewal. Claims coordinate the sessions of one machine. A failed claim command gives no permission to start work. [One factory on one machine](single-factory.md) gives the rules. `claim` takes ready work, `heartbeat` renews the current holder's lease, and `release` gives work back. The requested lease is checked by code. Claim returns a token for the current work attempt. Heartbeat, release, and changes to held work need that exact token; a token from an earlier claim is refused.

Releasing a claim returns `claimed` or `in_progress` work to the computed ready or blocked state. Work in another state keeps that state. Claim release does not mark the work `released`. Product release status uses `status ... released` with the required approval.

## Check and report

Plan's check command reports invalid relationships, missing references, drift, and model problems that it supports. A report keeps each warning visible and separates errors from successful writes. The PRD remains unchanged by planning, status changes, claims, and migration. An accepted drift is an event in the history of the item, with its actor, its approval and both hashes.
