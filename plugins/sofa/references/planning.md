# Sofa planning contract

Read the `Roadmap backend` row of `docs/adlc.md` on `main` before roadmap work. `plan` selects this contract and the Plan instructions of your role. An absent row or the explicit value `product` selects the legacy Product instructions. An unknown value is a setup error: send `BLOCKED · team` and make no roadmap write. Installation, a template update, or the presence of a Plan profile does not change this choice.

## Selected Plan workspace

The `Plan workspace` row names a machine-local profile relative to the main checkout, usually `.claude/plan/local.json`. Each participating machine binds its profile to the same published Plan workspace and control identity through the same approved Git remote. Do not initialize an independent workspace on each machine or choose a store from a worktree. A local copy alone is not the shared work state. A Sofa floor snapshot and the GitHub Project are reports, not Plan claims.

Use this prefix for every Plan command:

```text
<skill folder>/scripts/sofa-plan --repo <main folder> <Plan command args>
```

The wrapper reads the selected backend and profile, resolves the installed Plan plugin, and binds the absolute profile path. Do not replace it with a source-tree `plan.py`, a cache path from a previous run, a raw `bd` command, or a Product roadmap writer. Read the installed Plan `references/cli.md`, `references/planning.md`, and `references/roadmap-model.md`; use command `--help` for exact arguments. For Plan skills, pass this wrapper, the same absolute profile, and the shared-write and private-token rules below as the caller contract for the whole run.

Before activation, verify that the installed Plan supports shared publication, guarded claims, and GitHub Project publication. Sofa readiness runs `describe`, `check`, and `list`; it requires `shared`, `distributed_claims`, and `automatic_publish` to each be the exact Boolean `true` in `describe`. The source root must be this machine's main checkout. Local-only Plan support or truth-like strings are not sufficient. Until the installed CLI documents and verifies these operations, report the missing support and keep affected work blocked; do not invent commands or promise that a local write is shared. Use the installed command reference for the exact shared and GitHub interfaces.

## Shared writes and claims

Before dependent work, refresh and verify the selected shared workspace through Plan, then read `describe`, `check`, `ready`, `list`, `show`, or `history` as needed. Plan's guarded operation must check the current shared revision, publish the accepted change, and confirm the result before the caller reports success. A local claim or local commit is not a successful shared claim. A failed, refused, or interrupted publication blocks affected work until the supported recovery and fresh shared read confirm its outcome. Never continue implementation while shared ownership is uncertain.

Each shared-factory station executes as `agent:<machine instance>.<station name>`, with `--actor` where a command requires it. Use the validated `machine.instance`/GitHub person machine value from the start prompt, not the App bot login; each part uses Plan's accepted actor characters. Confirm that participating machines have distinct instance values before work starts. A bare station name can repeat on another machine and is not a shared actor identity. Do not use another actor's token or a synthetic human actor. A shared gate's private attempt token is separate from this actor identity. Outside a shared Sofa factory, a Plan skill still uses its caller's explicit actor. Responsibility (`assign TYPE NUMBER OWNER`) is separate from a claim. Tracker coordinates assignment; the actual working station runs `claim`, `heartbeat`, and `release` as itself. Tracker never claims as another station. Check shared ownership before work continues, including after a restart or lost connection. Another holder, an expired lease, or a conflict is not permission for automatic takeover. Use only the supported expiry, release, or operator-approved recovery path.

A claim returns a private `claim_token`. The holder keeps it locally and obtains its current claim through a fresh Plan read after a restart. It supplies that exact token for heartbeat, release, and mutations of held work. Capture output that can hold a token in a private machine-local file under the ignored `.sofa/` folder; show only token-free fields. Read the token into command arguments from that file without printing it or putting its literal value in command text. Never put tokens in messages, start prompts, PRs, logs, transcripts, Sofa rows, GitHub fields, snapshots, or exports. Renew a lease while work continues and return the claim when work stops. A stale token is not ownership.

Use `--expected-revision` for existing-record mutations and one `--request-id` for a retried exact operation. After a replay, compare `operation.result.revision` with `record.revision`; read the current shared record and claim if they differ. Make dependent writes in order and run `check` after the group. A refusal needs the stated evidence or a decision, not a direct store change. Do not run raw `bd` sync, push, pull, GitHub sync, or manual data-ref replacements around Plan's guards.

The approved Beads transport exception applies only to guarded replacement of `refs/dolt/data` and its `refs/heads/__dolt_remote_info__` information branch by the supported Plan transport. It does not permit a forced push or rebase of `main`, a PR branch, or another source branch. Stations do not issue manual replacement commands for these data refs. A shared data remote must not expose private claim tokens in reports or exports.

Use IDs returned by Plan, including `PLAN-STORY-NN` and preserved imported Product IDs. Work state uses `status TYPE NUMBER STATE --actor ACTOR`, never `set ... state`. Supply the actual accepted approval reference with `--approved-by` when required. Do not invent an approval ID. `release` returns a claim; only `status ... released` records a product release.

## Sources and board publication

Plan reads the Product PRD from the configured source root. Product `explore` and `review` may maintain that PRD through the normal PR process. Do not call Product roadmap planning, specification, task, estimate, check-declaration, or sync helpers for Plan items. Plan does not write the PRD and has no spec-writing skill. A historical Product roadmap graph is not evidence of current Plan work.

Keep the existing GitHub Project. Its published work comes from confirmed shared Plan records, not reconstructed Product roadmap files. Only the configured named board publisher writes it; another tracker checks and reports differences without publishing or taking over. Use `plan:sync` for a verified shared refresh and `plan:publish` for the Plan-native preview and publication through the Sofa `gh` shim and the existing App identity. If permissions or publisher support are missing, publication is blocked; this does not permit use of a person's token.

Preserve imported issue numbers, Project and card IDs, field bindings, type mode, and the repository's update boundaries. Preview changes before apply, keep the sub-issue and depth limits, and save confirmed bindings through Plan's supported interface so a retry does not create duplicate issues. A board edit is evidence for a decision or Plan correction, not an unguarded state or claim change. The Project displays shared work; its assignee is not the claim authority. Never invoke a Product writer against temporary roadmap files to publish Plan work.

## Role boundaries

- Planner owns scope and planned items. Use `plan:generate`, `plan:develop`, and `plan:read` with the selected profile. Preserve confirmed work and requirement traces. A Plan-only result is a checked, published shared change, not a roadmap Markdown PR. Report returned IDs and the token-free shared result; PRD changes still need a PR.
- Specifier reads the Feature and Stories through Plan and writes the spec through a reviewed repository PR. Only after the spec merges and exists inside the configured source root, attach its path with `set ID spec PATH`, then request promotion with the real actor and actual `--approved-by` reference. Missing spec, proof, approval, or an open decision keeps unpromoted stories in backlog. Plan returns `ready` or `blocked`; do not remove blockers to force readiness.
- Tracker reads shared Plan, sets responsibility through `assign`, and coordinates the actual holder. Report a conflicting claim without changing it. The named publisher alone publishes confirmed Plan data to the existing GitHub Project through the supported Plan interface and `gh` shim.
- Plan-auditor reconciles merged code and tests with Plan `show`, `history`, `status`, and `check`. Request `done` only after code and required tests merge, with the required approval evidence. Coordinate a held-work change with the actual holder; do not take its token. Keep discovery PR evidence in the body; `discovered_from` is a relation to another Plan item, not a PR field. A parent's completion is a separate checked, published change.
- Monitoring alone requests `status ... released` after the healthy window and required approval evidence. It reports the confirmed shared state and signal window; it does not use claim `release` to record deployment.
- Orchestrator reads shared Plan order and readiness, asks tracker to assign responsibility, then asks the working station to claim. It waits for confirmed publication and fresh holder evidence before execution starts. The sequence is spec merge, attach spec, approved promotion, published working-station claim, code and tests merge, audited completion, then monitored release. Route confirmed changes to the named board publisher.
- Requests, scribe, and decision-judge read shared Plan for roadmap facts and make no Plan writes. Scribe keeps knowledge, not a second roadmap or Plan veracity fields. Decision-judge uses the current shared stage and real decision evidence.

## Sofa records and proofs

Sofa work orders remain role-owned. Only plan-auditor writes Sofa roadmap projections from confirmed shared Plan state: `claimed` and `in_progress` become `in progress`; `in_review` becomes `in review`; other supported states keep their word. Use the returned item ID and `--reopen` only for a supported reopening. A Sofa row does not change Plan state or prove a claim. Plan roadmap snapshots use `source: plan` and `read_at`; Git `commit` and `committed_at` are null. A failed Plan read stops the snapshot, not a fallback to historical Product pages.

Interactions, decisions, trips, and metrics stay in Sofa. Do not write `hitl_questions`, `autonomous_decisions`, `review_defects`, `trips`, `picked_up_at`, `released_at`, or `proofs` into Plan fields. A versioned metric report can remain in `docs/adlc/metrics/` through a PR. Plan controls its actual dates and derived progress.

Keep the Proofs block of each PR. Its `product` line means that the verifier ran the product as a user, not the roadmap backend. The `process` line names the Plan item ID and merged spec PR. Plan writes need a checked, confirmed shared result; associated PRs keep their review and merge rules.

## Explicit activation of an existing factory

A Product factory stays legacy until the operator approves a separate change. Do not import, change its profile, or activate Plan during installation, readiness, start, or an ordinary template update.

For an approved conversion, pause previous roadmap writers and board publishers on every machine. Configure one selected Plan workspace, preview `migrate` from a fixed committed source with `--revision`, and obtain approval of its fingerprint. Apply only that snapshot with `migrate --apply --revision COMMIT --fingerprint HASH`; use `--source` when the accepted source is not the default. Migration leaves Product files unchanged and is not ongoing sync. Inspect mappings and claims without disclosing tokens, then run `check`.

Before resume, verify shared publication and identity, bind every machine to that same published workspace and control, test guarded claim conflict and interrupted-write recovery, and verify a preview against the existing GitHub Project with its named publisher. Land the explicit backend/profile choice and review repository role overrides for Product writers. Resume only after these activation checks pass. A preview, empty local store, or unshared import is not activation. If a step fails, keep affected writers paused and report the partial result; do not run both roadmap backends or automatically take over another writer.
