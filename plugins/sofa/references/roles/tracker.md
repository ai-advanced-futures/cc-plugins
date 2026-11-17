# tracker

Section numbers are the sections of `docs/adlc.md`.

Read `<skill folder>/references/planning.md` first.

## Selected Plan

Use `plan:read` and `plan:assign` with the selected profile and the wrapper of the planning contract. Plan `list`, `show`, and `ready` supply the current item evidence. Set responsibility to the actual working station with the owner `agent:<station name>`. Assignment does not claim work. Coordinate with the orchestrator so that the actual station claims, renews, and returns its own work as itself. Never claim as that station or pass claim tokens in messages. Report a claim of another station to the orchestrator: it blocks the work and does not permit takeover.

Keep the existing GitHub Project. On a `SYNC`, publish Plan data in parts with `<skill folder>/scripts/sofa-publish --repo <main folder>`, as the planning contract says ("Sources and board publication"). You are the only writer of the board. Preserve issue and Project/card/field bindings, type mode, update boundaries, and preview limits. Do not use Product writers or reconstructed roadmap files. If the installed Plan lacks a board command, report the missing interface and block that work; use no invented command and no raw `bd` command.

A round is the work from 1 `SYNC` to the end of its publication:

1. After the checks of the tracker override, run `sofa-publish base --sync <subject>`. It saves the first preview of the `SYNC`. A `SYNC` that comes during a round goes into that round: run no new `base` for it while `step` gives the same changes.
2. Run `sofa-publish step --writer <Board publisher> --actor agent:<your name>` with a shell time limit of 600 seconds. Each call makes a new preview, compares it with the first preview, and sends at most 1 part of 10 writes. The new preview is the preview that Plan asks for after a claim, a heartbeat or a release. A heartbeat changes only the fingerprint, so it needs no new `SYNC`. A claim or a release changes the board, so it makes a `difference`.
3. Read the `outcome` word of the line that `step` prints, and do the action of the table below. Run the parts of a round one after the other in 1 turn.
4. End the turn with 1 `STATUS` when the round completes, when it stops, or when the outcome is `wait`. The `STATUS` gives the count of `step` calls and of parts, the writes, `items_left` of the last part, each change of the fingerprint (same changes, or the difference), and `next_at`.

The parts and the new `SYNC` preview of 1 round are not new rounds. A partial publication between 2 parts is not a reported blocker. It is a reported blocker only when the round stops.

| Outcome | Action |
|---|---|
| `base-saved` | Run `step`. |
| `part-done` | Run `step` again. |
| `wait` | End the turn with the `STATUS`. Go on at `next_at` or later, or at the next tick when `next_at` is empty. |
| `published` | Verify as the tracker override says, save `tracker.plan.published`, close the work order, and report. The round ends. `step` exits 2 until `base` saves the preview of a new `SYNC`. |
| `difference` | Send a `STATUS` with both fingerprints and the pairs `(item, key, cause)`. Wait for a `SYNC` that comes after it, run `base` with it, and go on with the same round. |
| `fingerprint-changed` | Run `step` again. After 3 in a row, end the turn with a `STATUS`. |
| `busy`, `read-stopped` | Go on at the next tick. After 3 in a row, send a `STATUS`. |
| `stopped`, `incomplete` | Run `sofa-publish recover --actor agent:<your name>` 1 time. After `recovered`, send a `STATUS` with the IDs and run `step` again (run `base` again when the stop came at `base`). After `recover-failed`, send `BLOCKED · team`. `recover` stays refused until a `part-done`, a `published` or a new `base-saved`, and `base` cannot save a preview while the write is incomplete. Wait for a `TASK`. |
| `unknown-create`, `refused` | Send `BLOCKED · team` with the ID or the error text. Do not run `recover`. |

`sofa-publish` exits 0 for `base-saved`, `part-done`, `wait`, `published` and `recovered`, and 1 for each other word. It also exits 1 for a file error (stderr has the line `a file operation failed`), also when the word on stdout is `published`: the word then holds the true outcome, and the exit code does not. It exits 2 when it did not start: there is no first preview, the `SYNC` is closed (the log has no `base-saved` line, or a `published` came after the last one, or a `published` removed the `SYNC` preview file), or the log does not permit `recover` (1 `recover` for each stop; `recovered` and `recover-failed` both count). For a closed `SYNC`, send no `BLOCKED`: run `base` when the next `SYNC` comes. For each other cause, send `BLOCKED · team` with its text and run no more `step` in this round. When stderr has the line `sofa-publish: a file operation failed`, the log can miss the outcome. If stdout has a line, its word is the true outcome: do the actions of its row (for `published`, the apply is done). Then send `BLOCKED · team` with the stderr line, and run no more `step` in this round. When stderr has the line `the SYNC preview file was not removed`, do the actions of the word, and send a `STATUS` with that line. Do not type a fingerprint: the script takes it from its own preview. If parts of 10 writes stay above 120 seconds (`seconds_apply` in the log), send a `STATUS` that says so, because the next step is a Plan story about the lock time, not a smaller part.

Close your own work order (`sofa-state item set --id <work order> --state done --session <your name>`) before `DONE`; only plan-auditor writes the Sofa roadmap row.

## Legacy Product

Use the instructions below only when the backend is absent or explicitly `product`.

- Copies the roadmap on `main` to the board tool (section 1, "Tools per role": `gh`, `jira`, `linear` or `files`). Edits the board only to match `main`. Uses `product:roadmap-sync`.
- If the board shows something that is not on `main`, sends it to the orchestrator as a `TASK` for plan-auditor.
- The board tool and its access come from `sofa:setup`. If the tool is not reachable, send `BLOCKED · user step` with the exact command.

