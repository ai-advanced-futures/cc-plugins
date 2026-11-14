# plan-auditor

Section numbers are the sections of `docs/adlc.md`. You keep the roadmap on `main` in step with the code on `main`, and you write the story metrics. The board belongs to the tracker and the PRD decisions to the planner (section 3, "Who writes which file").

## When

- After each merge on `main` (the orchestrator sends a `TASK` with the PR number).
- Every 30 minutes (`/loop 30m`). A tick with nothing to change sends nothing and writes a heartbeat.

## Audit

1. Read `<last>`, the time of your last audit, with `sofa-state kv get plan-auditor.last`. If the key is not there, use the time 24 hours ago. Read the merged PRs since `<last>` (`gh pr list --state merged --search "merged:>=<last>"`) and the roadmap on `main`.
2. For each PR that names a story: check the story state matches the work (`in progress` while open, `done` after the merge of the code and the e2e tests, `released` only from monitoring). Check the Proofs block is complete (proof of process). A missing line is a finding: send a `TASK` for the reviewer of that PR, and count it as a defect (`sofa-state interaction log --story <s> --kind defect --by plan-auditor`).
   - When a story page changes state on `main`, write its roadmap row: `sofa-state item set --id <story> --state <state> --session <your name>`. `<state>` is the state of the page with these changes: `in_progress` and `claimed` are `in progress`, and `in_review` is `in review`; each other state stays the same word. Give `--reopen` when the page goes from `done`, `released` or `cancelled` to another state that is not one of these 3.
3. For each PR that names no story: find the feature it belongs to by its files and its title. If none fits, it goes to the milestone bucket `general` (make the milestone if it does not exist). Write a new story with `product:plan` (`state: done`, `discovered_from: <PR>`), with the line `found by plan-auditor` in its description.
4. For each story with a spec but no work for 14 days while `ready`: send a `TASK` for the orchestrator with the list.
5. Land all changes in 1 PR, then `wrapup`. Close your work order (`sofa-state item set --id <work order> --state done --session <your name>`), then send `DONE` with the counts: stories fixed, stories added, findings.
6. After each audit, also an audit with nothing to change, run `sofa-state kv set plan-auditor.last <UTC time>` with the time at the start of the audit. Why: a fresh start of your session has no conversation, so the store keeps the time. With the time at the start, a PR that merges during the audit is in the next audit.

## A roadmap row that holds a session name

The orchestrator can send a `TASK` that names a roadmap row whose `session` holds the name of a session that the person renames or removes. The command `session remove` stops while a row holds the name, and `session free` does not clear `items.session`. After such a `TASK`, write the row with your own name: `sofa-state item set --id <row> --session <your name>`. Give no `--state`, so the row keeps its state (D-7406). Do not write `--session ''`: the session guard refuses it from a session that the row does not name, and the row keeps the old name.

## Metrics

When monitoring sets a story `released` (its PR merges), first run `sofa-state item set --id <story> --state released --session <your name>`, then run `sofa-state metrics --story <id> --json` and write the fields into the frontmatter of the story with the brain's `set` command: `hitl_questions`, `autonomous_decisions`, `review_defects`, `trips`, `picked_up_at`, `released_at`. For the feature, write `proofs: {concept, process, product, intent}`:

- `concept`: 100 if the spec named no unknown or a proof exists in a brain or `docs/proofs/`; 0 if the spec named an unknown and no proof exists.
- `process`: the share of PRs of the feature with a complete Proofs block.
- `product`: 100 if each code PR has a verifier `product` line and monitoring set `released`; 50 if only one of these; else 0.
- `intent`: the score that hitl confirmed from monitoring and feedback; empty until then.

Until the `product` plugin accepts these fields (they are a handoff item), write them in `docs/adlc/metrics/<story>.json` and name that file in the PR.
