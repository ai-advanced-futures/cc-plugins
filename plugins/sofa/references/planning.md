# Sofa planning contract

Read the `Roadmap backend` row of `docs/adlc.md` on `main` before roadmap work. `plan` selects this contract and the Plan instructions of your role. An absent row or the explicit value `product` selects the legacy Product instructions. An unknown value is a setup error: send `BLOCKED · team` and make no roadmap write. Installation, a template update, or the presence of a Plan profile does not change this choice.

## Selected Plan workspace

A repository has 1 factory on 1 machine (`docs/adlc.md` section 1, `Factory`). The Plan store is on that machine, and only that machine writes it. Several sessions of the team write the same store, so the claim rules below apply.

The `Plan workspace` row names the profile, relative to the main checkout, usually `.claude/plan/local.json`. Do not choose a store from a worktree, and do not initialize a second store, because the team then has 2 plans. A Sofa row and the GitHub Project are reports, not Plan claims.

Use this prefix for every Plan command:

```text
<skill folder>/scripts/sofa-plan --repo <main folder> <Plan command args>
```

The wrapper reads the selected backend and profile, resolves the installed Plan plugin, and binds the absolute profile path. Do not replace it with a source-tree `plan.py`, a cache path from a previous run, a raw `bd` command, or a Product roadmap writer. Read the installed Plan `references/cli.md`, `references/planning.md`, and `references/roadmap-model.md`; use command `--help` for exact arguments. The wrapper stops each Plan command after `SOFA_PLAN_TIMEOUT` seconds, default 300. A Plan command can wait up to 120 seconds for the store lock while another session writes, so give the shell call of a Plan command a time limit of 300 seconds or more. For Plan skills, pass this wrapper, the same absolute profile, and the claim and private-token rules below as the caller contract for the whole run.

Sofa readiness runs `describe`, `check`, and `list`. The source root must be the main checkout. When a command of the installed Plan is missing, report it and keep the affected work blocked; do not invent a command.

## Claims between sessions

Before dependent work, read `describe`, `check`, `ready`, `list`, `show`, or `history` as needed. A failed or refused Plan write blocks the affected work until a fresh read shows its result. Never continue implementation while you do not know which station holds the item.

Each station executes as `agent:<station name>`, with `--actor` where a command requires it. The station name is your session name. Do not use the App bot login, a human actor, or the name of another station. Responsibility (`assign TYPE NUMBER OWNER`) is separate from a claim. Tracker coordinates assignment; the actual working station runs `claim`, `heartbeat`, and `release` as itself. Tracker never claims as another station. Check that you hold the claim before work continues, also after a restart. Another holder, an expired lease, or a conflict is not permission to take the work. Use only `expire`, `release`, or a `TASK` of the orchestrator.

A claim returns a private `claim_token`. The holder keeps it locally and obtains its current claim through a fresh Plan read after a restart. It supplies that exact token for heartbeat, release, and mutations of held work. Capture output that can hold a token in a private file under the ignored `.sofa/` folder; show only token-free fields. Read the token into command arguments from that file without printing it or putting its literal value in command text. Never put tokens in messages, start prompts, PRs, logs, transcripts, Sofa rows, GitHub fields, snapshots, or exports. Renew a lease while work continues and return the claim when work stops. A stale token is not ownership.

Use `--expected-revision` for existing-record mutations and one `--request-id` for a retried exact operation. After a replay, compare `operation.result.revision` with `record.revision`; read the current record and claim if they differ. Make dependent writes in order and run `check` after the group. A refusal needs the stated evidence or a decision, not a direct store change. Run no raw `bd` command on the store, because Plan cannot check such a write.

Use IDs returned by Plan, including `PLAN-STORY-NN` and preserved imported Product IDs. Work state uses `status TYPE NUMBER STATE --actor ACTOR`, never `set ... state`. Supply the actual accepted approval reference with `--approved-by` when required. Do not invent an approval ID. `release` returns a claim; only `status ... released` records a product release.

## Sources and board publication

Plan reads the Product PRD from the configured source root. Product `explore` and `review` may maintain that PRD through the normal PR process. Do not call Product roadmap planning, specification, task, estimate, check-declaration, or sync helpers for Plan items. Plan does not write the PRD and has no spec-writing skill. A historical Product roadmap graph is not evidence of current Plan work.

Publication is optional. Follow `<skill folder>/references/publication.md` for setup approval, status, and failure handling. Keep the existing GitHub Project and its bindings, even when publication is disabled. Published work comes from Plan records, not reconstructed Product roadmap files. The tracker is the only board writer and uses the factory GitHub App. Read `publication status` through `sofa-plan` before each board round. When disabled, do no board work; assignment and claim coordination continue. After setup approval, use the part loop below. Both `sofa-plan` and `sofa-publish` check local approval before each apply and supply the App environment.

1. Preview (`github preview`). It changes nothing on the board. `sofa-publish` makes this preview for you.
2. Apply that preview in parts with `<skill folder>/scripts/sofa-publish --repo <main folder>`, and only after a `SYNC` of the orchestrator, because the `SYNC` approves that round. `base` saves the first preview of the `SYNC`. Each `step` after it makes a new preview, compares it with the first one, and applies the fingerprint of its own preview for at most 1 part. Repeat `step` until its outcome is `published`. A `published` closes the `SYNC`: the next `step` needs a new `base`. When the removal of the `SYNC` preview file and the `published` log line both fail, the `SYNC` stays open after the apply; the tracker role file gives the stop. An open `SYNC` is a state of the `SYNC` preview, not of the `SYNC` message: the last `base` gave `base-saved`, and no `published` came after it. Do not apply a preview that has a refusal: report it. The tracker role file gives the action for each outcome word.

If the App lacks permission, publication is blocked; use no person's token. A failed or partial publication stops board work as the tracker outcome table specifies, not local factory work. Retain the last verified result. Both command entry points refuse apply without local approval or when the approved target differs. Only `published: true` with `complete: true` advances the verified result; exit zero alone does not.

Preserve imported issue numbers, Project and card IDs, field bindings, type mode, and the repository's update boundaries. Keep the sub-issue and depth limits, and save confirmed bindings through `github configure` so a retry does not create duplicate issues. A board edit is evidence for a decision or Plan correction, not a state or claim change. The assignee of the Project is not the claim authority. Never invoke a Product writer against temporary roadmap files to publish Plan work.

## Role boundaries

- Planner owns scope and planned items. Use `plan:generate`, `plan:develop`, and `plan:read` with the selected profile. Preserve confirmed work and requirement traces. A Plan-only result is a checked Plan change, not a roadmap Markdown PR. Report returned IDs and the token-free result; PRD changes still need a PR.
- Specifier reads the Feature and Stories through Plan and writes the spec through a reviewed repository PR. Only after the spec merges and exists inside the configured source root, attach its path with `set ID spec PATH`, then request promotion with the real actor and actual `--approved-by` reference. Missing spec, proof, approval, or an open decision keeps unpromoted stories in backlog. Plan returns `ready` or `blocked`; do not remove blockers to force readiness.
- Tracker reads Plan, sets responsibility through `assign`, and coordinates the actual holder. Report a conflicting claim without changing it. It publishes Plan data to the existing GitHub Project as the section above says.
- Plan-auditor reconciles merged code and tests with Plan `show`, `history`, `status`, and `check`. Request `done` only after code and required tests merge, with the required approval evidence. Coordinate a held-work change with the actual holder; do not take its token. Keep discovery PR evidence in the body; `discovered_from` is a relation to another Plan item, not a PR field. A parent's completion is a separate checked change.
- Monitoring alone requests `status ... released` after the healthy window and required approval evidence. It reports the state that Plan returns and the signal window; it does not use claim `release` to record deployment.
- Orchestrator reads Plan order and readiness, asks tracker to assign responsibility, then asks the working station to claim. It waits for the claim before execution starts. The sequence is spec merge, attach spec, approved promotion, working-station claim, code and tests merge, audited completion, then monitored release. It sends a `SYNC` to the tracker after a Plan change.
- Requests, scribe, and decision-judge read Plan for roadmap facts and make no Plan writes. Scribe keeps knowledge, not a second roadmap or Plan veracity fields. Decision-judge uses the current stage and real decision evidence.

## Sofa records and proofs

Sofa work orders remain role-owned. Only plan-auditor writes Sofa roadmap projections from Plan state: `claimed` and `in_progress` become `in progress`; `in_review` becomes `in review`; other supported states keep their word. Use the returned item ID and `--reopen` only for a supported reopening. A Sofa row does not change Plan state or prove a claim. A failed Plan read stops the projection, with no fallback to historical Product pages.

Interactions, decisions, trips, and metrics stay in Sofa. Do not write `hitl_questions`, `autonomous_decisions`, `review_defects`, `trips`, `picked_up_at`, `released_at`, or `proofs` into Plan fields. A versioned metric report can remain in `docs/adlc/metrics/` through a PR. Plan controls its actual dates and derived progress.

Keep the Proofs block of each PR. Its `product` line means that the verifier ran the product as a user, not the roadmap backend. The `process` line names the Plan item ID and merged spec PR. Plan writes need a checked result; associated PRs keep their review and merge rules.

## Backup and restore

Plan pushes its data to `origin` (the ref `refs/dolt/data`) after each content write: a create, a change of a state or a field, an import, and `github apply`. A claim, a heartbeat, a release and a read push nothing. The backup is a copy for a restore. No session reads it for work.

- `/sofa:setup` turns the automatic backup on 1 time: `<skill folder>/scripts/sofa-plan --repo <main folder> backup --remote origin --auto on`. `unshare` turns it on by itself. `describe --json` shows the state in `backup`: `remote`, `auto`, `pending`, `last_push_at` and `last_error`.
- `<skill folder>/scripts/sofa-plan --repo <main folder> backup` pushes 1 time. The `/sofa:stop` command runs it at each stop of the team (`commands/stop.md`).
- A failed push does not block or undo the write. Plan marks the push as pending, and the next push sends all the data. When a result has `backup.pushed: false`, go on with your work, and name it in your next `STATUS`. Do not run the write again, and do not push by hand. The orchestrator reads `describe` and raises the user step (orchestrator role file, "Backup check").

Restore on a new machine, with no team live on it (`commands/handoff.md`):

1. Clone the repository. `<main folder>` is that checkout.
2. In `<main folder>`, run `bd bootstrap --dry-run`. Its plan must say that it clones from the remote or from the git origin. Then run `bd bootstrap --yes`. It is the only raw `bd` command of a restore, and it copies the data only when no local Beads database exists.
3. Configure the Plan workspace with the `plan:setup` skill of the plan plugin: the profile of the `Plan workspace` row (`<main folder>/.claude/plan/local.json`), the Beads directory `<main folder>/.beads`, and the source root `<main folder>`. Do not use the `sofa-plan` wrapper for this step, because it refuses each command while the profile does not exist. Setup finds the workspace in the restored data and keeps its identity.
4. Run `describe`, `check`, and `list` with the prefix `<skill folder>/scripts/sofa-plan --repo <main folder>`. `check` gives 0 errors, and the record count of `list` is the count of the old machine after its last backup.

An error that names `unshare` means that the backup is older than the conversion to a local store. In step 3, the `plan:setup` skill runs `unshare` after the user approves. In step 4, run `<skill folder>/scripts/sofa-plan --repo <main folder> unshare`, then do step 4 again. If a step refuses or stops for another cause, stop the restore and show the error.

## One-time unshare

Plan 0.3.0 has no shared mode. A profile of an earlier Plan can have a `sharing` block. Readiness then gives `roadmap-backend` as `wrong` with "the Plan profile is still shared". Do these in order:

1. Stop the team (`/sofa:stop`), because a session must not write the store during the change.
2. Update the plan plugin to 0.3.0 or later.
3. Run `<skill folder>/scripts/sofa-plan --repo <main folder> unshare`. It makes no call to the remote.
4. Run `sofa:readiness`. `roadmap-backend` must be `ok`.

## Conversion of a legacy Product factory

A Product factory stays legacy until the user approves a separate change. Do not import, change its profile, or activate Plan during installation, readiness, start, or an ordinary template update.

For an approved conversion, stop the team, because a session must not write the roadmap during the copy. Configure the Plan workspace (`plan:setup`). Preview `migrate` from a fixed committed source with `--revision`, and obtain approval of its fingerprint. Apply only that snapshot with `migrate --apply --revision COMMIT --fingerprint HASH`; use `--source` when the accepted source is not the default. Migration leaves Product files unchanged and is not ongoing sync. Inspect mappings and claims without disclosing tokens, then run `check`.

Before the next start, check a board preview against the existing GitHub Project, land the backend and profile rows of `docs/adlc.md`, and correct each repository role override that names a Product writer. A preview or an empty store is not a conversion. If a step fails, keep the team stopped and report the partial result; do not run both roadmap backends.
