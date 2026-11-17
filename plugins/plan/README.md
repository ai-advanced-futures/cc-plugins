# Plan

Plan turns an existing Product requirements document (PRD) into work stored in Beads. It keeps Product's scope, theme, feature, and story questions, with a separate Plan command line for writes.

Plan is optional. It reads Product PRD files but does not need an installed Product or Sofa plugin. It does not write Product roadmap pages, change a knowledge graph registration, or start a team. Beads is its only work-item backend.

## Requirements

- macOS or Linux. The local file lock does not support Windows.
- `uv` and Python 3.11 or later.
- Beads `bd` 1.3.4 and an existing, initialized Beads directory. This release supports only Beads' embedded Dolt store, not an external Dolt server.
- An existing Product PRD bundle in the source repository.

## Set up a workspace

A workspace profile is an explicit file path, such as `.claude/plan/local.json`, that selects the Beads directory and source root. Setup uses a directory that you have already initialized with Beads; it does not initialize an unrelated store. Use an explicit profile, or set `PLAN_WORKSPACE` for later commands. An explicit `--workspace` takes priority.

Configure the profile through `/plan:setup` or the Plan command line. In the following command, `PROFILE` is the profile file path, `DIR` is the initialized Beads directory, and `ROOT` is the source repository root:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE setup --beads-dir DIR --source-root ROOT
```

`${CLAUDE_PLUGIN_ROOT}` is set inside a loaded plugin. From a repository checkout, replace it with the path to `plugins/plan`.

Setup does not copy an existing roadmap. Use `/plan:migrate` to preview that copy.

## One machine

A repository has one Plan workspace on one machine. Many sessions on that machine can use it at the same time: a file lock lets one command use the store at a time, and a claim gives one session the right to work on an item.

`backup --remote NAME --auto on` makes Plan push its data to a Git remote after each content write. A failed push does not fail the write. To restore, run `bd bootstrap` and then Plan `setup`. Plan 0.3.0 removed shared mode: run `unshare` one time on a profile from shared mode. [One factory on one machine](references/single-factory.md) gives each procedure.

## Plan from requirements

Use `/plan:generate` to choose the MVP, one phase, or the full product. Each agreed phase gets a Milestone, including future phases that have no work items yet. Only the selected slice gets Epics, Features, and Stories.

Generate delegates detailed work to `/plan:develop`. Develop uses the adapted Product helpers and asks before story work for each Feature. You can stop at that point and keep the confirmed plan. Each acceptance criterion is a separate item with its own ID, not a checkbox inside another item's text.

Continue an existing Milestone, Epic, or Feature with `/plan:develop`. The smaller helpers are also available on their own.

The following table lists the skills:

| Skill | Input | Result |
| --- | --- | --- |
| `/plan:setup` | Workspace, Beads directory, and source root | Configured Plan workspace |
| `/plan:generate` | Optional scope | Phase milestones and developed selected slice |
| `/plan:develop` | Milestone, Epic, or Feature | Confirmed missing work through the 3 helpers |
| `/plan:themes-identify` | Milestone | Epics with PRD traces |
| `/plan:features-identify` | Epic or Milestone | Features and Criterion items |
| `/plan:stories-identify` | Feature | Stories and Criterion items |
| `/plan:read` | Question or item | Plan and PRD evidence from the selected workspace |
| `/plan:assign` | Type, number, and owner | Stored responsibility |
| `/plan:status` | Type, number, and optional state | Current or requested work state |
| `/plan:claim` | Type, number, and actor | Leased claim on ready work |
| `/plan:heartbeat` | Type, number, actor, and claim token | Renewed claim lease |
| `/plan:release` | Type, number, actor, and claim token | Ended claim and stored work state |
| `/plan:migrate` | Optional source and apply choice | Preview or stable copy of a Product roadmap |
| `/plan:publish` | Explicit workspace and preview or apply choice | GitHub Project preview or checked publication |

The generation command is `/plan:generate`, not `/plan:plan`.

## Publish a GitHub Project

Configure one existing board and one named publisher through `github configure`. `/plan:publish` previews the Plan-to-board changes before an approved apply. Imported issue bindings stay attached to their Plan items. Publication uses the current `gh` authentication, including Sofa's wrapper when present. Apply paces its writes (1 second apart, 400 an hour) and can run in parts with `--part`.

The board is a view of Plan, not another work store. Publication does not pull issue state or assignees into Plan. A partial result remains visible and must complete through a checked retry. See the [command reference](references/cli.md) for configuration, fingerprints, and refusals.

## Requirements and completion evidence

Milestones, Epics, and Features trace existing PRD pages. Plan code records source hashes to detect changed requirements. A Story gets its own trace only when it narrows the Feature's requirement coverage.

The final summary names all milestones, the selected slice, item and criterion counts, blockers, trace gaps, uncovered scope, warnings, and the Plan check result. A failed check or a refused promotion is a partial result, not success.

Plan creates work in `backlog`. Promotion uses the actual executing actor. Agents use `agent:ID`; `human:LOGIN` identifies a command that a person runs. Agent promotion needs approval evidence, and Story promotion also needs the required spec evidence. Missing evidence remains a reported gap. Product's specification helper writes to the Product roadmap and is not used for Beads items.

Use Plan's command line for writes because direct Beads writes bypass Plan's lifecycle and relationship checks.

## Beads link limits

Beads dependencies show a reduced view of Plan relationships. The adapter writes at most 1 Beads edge per target. Parent links take priority and use `parent-child`. All other target links use `related`.

The full parent, blocker, milestone, discovery, and criterion item relationships remain in `metadata.plan`. Plan computes readiness from that data. Raw `bd ready` is not Plan's ready view; use Plan's `ready` command for work eligibility.

## Assign and change status

Assignment sets responsibility. A bare owner name maps to `human:NAME`; an explicit `agent:ID` names an agent owner. A claim is a separate, time-limited hold on work. A claim returns a token that identifies that work attempt. Heartbeat, release, and changes to held work need that exact token.

Releasing a claim returns `claimed` or `in_progress` work to `ready` or `blocked`. Work in another state keeps that state. Claim release does not set the work state to `released`.

The following commands assign an item, claim eligible ready work, and start that claimed work. `NUMBER` is the item's Plan number, `OWNER` is the responsible actor, and `ACTOR` is the executor's `agent:ID` or `human:LOGIN`. `TOKEN` is the exact claim token returned by the claim command:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE assign Story NUMBER OWNER
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE claim Story NUMBER --actor ACTOR
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE status Story NUMBER in-progress --actor ACTOR --claim-token TOKEN
```

`in-progress` maps to stored `in_progress`. A request for `ready` can return `blocked` when an open blocker exists. The command reports the stored state. A transition that needs approval also needs `--approved-by REF`, where `REF` identifies the actual approval. `status TYPE NUMBER` without a target state is read-only. Page lifecycle is a different field: `set ID lifecycle stable` marks page metadata stable rather than setting work state.

## Copy an existing roadmap

Migration previews the copy by default:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE migrate
```

Apply the reviewed copy:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE migrate --apply
```

Migration preserves source identity so a repeated apply of the same snapshot reuses mapped items. It leaves the Product source files unchanged and does not select Plan for a factory. `--source PATH` selects another source roadmap. A Git source defaults to the committed `HEAD` snapshot, not uncommitted edits.

The preview returns a source revision and a fingerprint, which identifies the source content. For an accepted preview, use `--revision COMMIT --fingerprint HASH --apply` with those returned values. The fingerprint check refuses a changed source. Apply requires an empty target or an incomplete import of the same snapshot; migration is not an ongoing sync.

## Inspect and check

Read the command help for the full interface:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --help
```

Read items and verify the plan:

```bash
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE list
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE ready
$ uv run ${CLAUDE_PLUGIN_ROOT}/scripts/plan.py --workspace PROFILE check
```

All output is JSON; global `--json` makes it compact. Creation returns the assigned ID in `record.id`. Mutation results include the stored record and operation. For an existing record, `--expected-revision NUMBER` refuses a stale item view. Creation and existing-record mutations accept `--request-id TEXT` for a retry of the same operation. A replay returns the original `operation` and `operation.result`, plus the current `record` view. `operation.result` holds the revision, state, owner, and claim token from that operation. The replay is not a full historical record snapshot.

Before you continue work from a replay, compare `operation.result.revision` with `record.revision`. If they differ, get a fresh view and the current claim needed for the work. An earlier claim token does not prove current ownership. Creation has no expected revision. Planning and lifecycle prompts use the `opus` model alias and are tuned against Claude Opus 5.5. Run the behavior and prompt checks again after a model change.
