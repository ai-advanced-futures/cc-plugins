---
description: Hand off the work of this sofa team to a team on another machine
---

Read the team prefix in `docs/adlc.md`. Send `TASK · user → orchestrator · handoff` with `SendMessage` to `<prefix>-orchestrator`. The orchestrator:

1. Pauses the team at a safe point (as `/sofa:pause`).
2. Makes sure each open branch is pushed.
3. Writes `docs/adlc/handoff-<date>.md` with the `handoff` skill: the feature queue, each open item with its PR, branch and state, each open `ASK` and `BLOCKED`, the autonomous decisions of the last 24 hours, and the next step of each item. No machine path and no secret.
4. Sends a `TASK` to the tracker to release the claims of this team.
5. Lands the file through a PR and reports its link.

The team on the other machine runs `/sofa:start`; its orchestrator reads the newest handoff file at start and continues from it. Then stop this team with `/sofa:stop`.
