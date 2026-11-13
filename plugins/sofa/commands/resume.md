---
description: Resume a paused sofa team
---

Read the team prefix in `docs/adlc.md`. Send `RESUME · user → orchestrator · team` with `SendMessage` to `<prefix>-orchestrator`. The orchestrator sets `team.state` to `running`. It does a fresh restart of each stopped session that has an open item (orchestrator role file, "Stopped sessions", "A fresh restart"). The fresh restart uses the dispatch script with no `--resume` and the store name of the session. Its first message is a `RESUME` that names the open item, its branch, its PR and its worktree. Then the orchestrator sends `RESUME` to each paused live session, and gives new items again.

If the orchestrator is not live, tell the user to start the team with `/sofa:start`; the new orchestrator continues the open items from the state store.
