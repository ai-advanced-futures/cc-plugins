---
description: Pause the sofa team at a safe point, or at once with --now
argument-hint: "[--now]"
---

Read the team prefix in `docs/adlc.md`. Send this message with `SendMessage` to `<prefix>-orchestrator`:

- No argument: `PAUSE · user → orchestrator · safe`. The orchestrator stops giving new items, sends `PAUSE` to each live session, waits until each one finished its turn, pushed its branch and sent `STATUS`, then writes `paused safe` in the store (`sofa-state kv set team.state paused`) and reports.
- `--now`: `PAUSE · user → orchestrator · now`. The orchestrator records the open item of each session in the store, runs `claude stop <id>` on each session except itself, hitl and requests, and reports which items were stopped mid-turn.

Tell the user that `/sofa:resume` continues the work.
