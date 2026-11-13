---
description: Stop the sofa team (pause at a safe point, then stop all sessions)
---

Read the team prefix in `docs/adlc.md`. Send `PAUSE · user → orchestrator · safe` with `SendMessage` to `<prefix>-orchestrator` and wait for its report. Then show the user the live sessions of the team (`ListAgents`, names that start with `<prefix>-`) and ask with `AskUserQuestion`: stop them all, or keep them. On stop, run `claude stop <id>` for each, the orchestrator last. The state store keeps the open items, so the next `/sofa:start` continues them. Do not run `claude rm`, because it deletes the transcript of the session.
