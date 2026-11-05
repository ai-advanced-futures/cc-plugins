---
description: Resume a paused sofa team
---

Read the team prefix in `docs/adlc.md`. Send `RESUME · user → orchestrator · team` with `SendMessage` to `<prefix>-orchestrator`. The orchestrator sets `team.state` to `running`, resumes each stopped session that has an open item (dispatch script with `--resume`, prompt `You were resumed. Continue your open item from its branch.`; if the open item has a worktree in the store, the prompt starts with the worktree sentence of "Stopped sessions" in the orchestrator role file), sends `RESUME` to each paused live session, and gives new items again.

If the orchestrator is not live, tell the user to start the team with `/sofa:start`; the new orchestrator continues the open items from the state store.
