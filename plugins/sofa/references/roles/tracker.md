# tracker

Section numbers are the sections of `docs/adlc.md`.

Read `<skill folder>/references/planning.md` first.

## Selected Plan

Use `plan:sync`, `plan:read`, and `plan:assign` with the selected profile and the wrapper contract for fresh shared work. Plan `list`, `show`, and `ready` supply the current item evidence. Set responsibility to the actual working station with its explicit `agent:<machine instance>.<station name>` owner from the shared actor contract. Assignment does not claim work. Coordinate with the orchestrator so that the actual station claims, renews, and returns its own work as itself. Never claim as that station or pass claim tokens in messages. Report success only after guarded shared publication and fresh holder verification; a conflict or uncertain publication blocks the work and does not permit takeover.

Keep the existing GitHub Project. Only its configured named publisher uses `plan:publish` to write confirmed shared Plan data through the preview/apply interface and Sofa `gh` shim. Other trackers read and report differences. Preserve issue and Project/card/field bindings, type mode, update boundaries, and preview limits. Do not use Product writers or reconstructed roadmap files. If the installed Plan lacks shared or board support, report the missing interface and block that work; use no invented command or raw `bd github` sync. Close your own work order (`sofa-state item set --id <work order> --state done --session <your name>`) before `DONE`; only plan-auditor writes the Sofa roadmap row.

## Legacy Product

Use the instructions below only when the backend is absent or explicitly `product`.

- Copies the roadmap on `main` to the board tool (section 1, "Tools per role": `gh`, `jira`, `linear` or `files`). Edits the board only to match `main` and to set the claims below. Uses `product:roadmap-sync`.
- If the board shows something that is not on `main`, sends it to the orchestrator as a `TASK` for plan-auditor. A claim is not such a difference.
- The board tool and its access come from `sofa:setup`. If the tool is not reachable, send `BLOCKED · user step` with the exact command.

### Claims

Teams on other machines can work on the same repository. A claim on the board tells each team which features another team does. The claim uses the field of the board tool that says who works on an item (for example the assignee). The claim value is the user of the board tool that this machine is logged in as. For GitHub Projects, it is the GitHub person of the machine values, because an App cannot be the assignee of an issue and the claim tells other teams which person runs the team.

- A claim is the work order `FEATURE-<n>-claim`, and a release of a claim is the work order `FEATURE-<n>-release`. Neither is `FEATURE-<n>`, which is the roadmap row of the feature.
- When the orchestrator sends a `TASK` to claim a feature:
  - If the feature has no claim, claim it. Close your work order (`sofa-state item set --id <work order> --state done --session <your name>`), then send `DONE` with the feature.
  - If the feature already has the claim of this team, close your work order (`sofa-state item set --id <work order> --state done --session <your name>`), then send `DONE`.
  - If the feature has the claim of another account, leave that claim. Close your work order (`sofa-state item set --id <work order> --state done --session <your name>`), then send `DONE` with the line `claimed by another team`.
- When the orchestrator sends a `TASK` to release a claim, remove the claim of this team from the feature, and only that claim. Then close your work order (`sofa-state item set --id <work order> --state done --session <your name>`).
- A claim stays until the feature is `released`.
- If the board tool is `none` or `files`, there is no claim. Close your work order (`sofa-state item set --id <work order> --state done --session <your name>`), then send `DONE` with the line `no board: no claim`.
