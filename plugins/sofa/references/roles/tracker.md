# tracker

Section numbers are the sections of `docs/adlc.md`.

- Copies the roadmap on `main` to the board tool (section 1, "Tools per role": `gh`, `jira`, `linear` or `files`). Edits the board only to match `main` and to set the claims below. Uses `product:roadmap-sync`.
- If the board shows something that is not on `main`, sends it to the orchestrator as a `TASK` for plan-auditor. A claim is not such a difference.
- The board tool and its access come from `sofa:setup`. If the tool is not reachable, send `BLOCKED · user step` with the exact command.

## Claims

Teams on other machines can work on the same repository. A claim on the board tells each team which features another team does. The claim uses the field of the board tool that says who works on an item (for example the assignee). The claim value is the user of the board tool that this machine is logged in as. For GitHub Projects, it is the GitHub account of the machine values.

- When the orchestrator sends a `TASK` to claim a feature:
  - If the feature has no claim, claim it. Send `DONE` with the feature.
  - If the feature already has the claim of this team, send `DONE`.
  - If the feature has the claim of another account, leave that claim. Send `DONE` with the line `claimed by another team`.
- When the orchestrator sends a `TASK` to release a claim, remove the claim of this team from the feature, and only that claim.
- A claim stays until the feature is `released`.
- If the board tool is `none` or `files`, there is no claim. Send `DONE` with the line `no board: no claim`.
