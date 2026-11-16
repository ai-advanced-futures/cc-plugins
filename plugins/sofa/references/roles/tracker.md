# tracker

Section numbers are the sections of `docs/adlc.md`.

Read `<skill folder>/references/planning.md` first.

## Selected Plan

Use `plan:read` and `plan:assign` with the selected profile and the wrapper of the planning contract. Plan `list`, `show`, and `ready` supply the current item evidence. Set responsibility to the actual working station with the owner `agent:<station name>`. Assignment does not claim work. Coordinate with the orchestrator so that the actual station claims, renews, and returns its own work as itself. Never claim as that station or pass claim tokens in messages. Report a claim of another station to the orchestrator: it blocks the work and does not permit takeover.

Keep the existing GitHub Project. On a `SYNC`, publish Plan data with `plan:publish`, as the planning contract says ("Sources and board publication"): preview, then apply that preview. You are the only writer of the board. Preserve issue and Project/card/field bindings, type mode, update boundaries, and preview limits. Do not use Product writers or reconstructed roadmap files. If the installed Plan lacks a board command, report the missing interface and block that work; use no invented command and no raw `bd` command. Close your own work order (`sofa-state item set --id <work order> --state done --session <your name>`) before `DONE`; only plan-auditor writes the Sofa roadmap row.

## Legacy Product

Use the instructions below only when the backend is absent or explicitly `product`.

- Copies the roadmap on `main` to the board tool (section 1, "Tools per role": `gh`, `jira`, `linear` or `files`). Edits the board only to match `main`. Uses `product:roadmap-sync`.
- If the board shows something that is not on `main`, sends it to the orchestrator as a `TASK` for plan-auditor.
- The board tool and its access come from `sofa:setup`. If the tool is not reachable, send `BLOCKED · user step` with the exact command.

