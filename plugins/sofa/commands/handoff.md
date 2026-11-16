---
description: Move the sofa factory of this repository to a new machine
---

A repository has 1 factory on 1 machine (`docs/adlc.md` section 1, `Factory`). This command moves the factory. Do the items in order, and stop at the first item that fails. Show each command for the user with the `$ ` prefix on its own line.

On the old machine:

1. Read the team prefix in `docs/adlc.md`. Send `TASK · user → orchestrator · handoff` with `SendMessage` to `<prefix>-orchestrator`. The orchestrator pauses the team at a safe point (as `/sofa:pause`) and makes sure each open branch is pushed. It writes `docs/adlc/handoff-<date>.md` with the `handoff` skill: the feature queue, each open item with its PR, branch and state, each open `ASK` and `BLOCKED`, the autonomous decisions of the last 24 hours, and the next step of each item. The file holds no machine path and no secret. The orchestrator lands the file through a PR and reports its link. The file is necessary, because the state store (`.sofa/state.db`) does not move.
2. Run `/sofa:stop` and stop all sessions. With the backend `plan`, it pushes the Plan backup. If the backup fails, stop here, because the new machine restores the Plan store from it.
3. With the backend `plan`, run `${CLAUDE_PLUGIN_ROOT}/scripts/sofa-plan --repo <main folder> list` from the main folder, and keep the record count for item 6.
4. The user removes the scheduler line from the crontab (`crontab -e`: the `bg-watch check` line), because it restarts stopped sessions.
5. The user moves the key file of the GitHub App to the new machine and keeps no copy on the old machine. The old machine must never start a team again, unless the `Factory` row changes to name it, because a second team takes the same items. The `Factory` row stays the same in a move, so the readiness item `factory-machine` does not stop a start on the old machine: the missing key file and this rule do.

On the new machine:

6. The user clones the repository and installs the `sofa` and `plan` plugins. With the backend `plan`, restore the Plan store as `references/planning.md` says ("Backup and restore"), then turn the automatic backup on (`/sofa:setup`, step 2.4). The record count of `list` must be the count of item 3.
7. The user runs `/sofa:setup`: the values of the same GitHub App (step 5.5, items 4 to 6), the scheduler line (step 4), and the Slack token (step 5, item 5). Change no value of `docs/adlc.md`.
8. The user runs `/sofa:start`, then `/sofa:request continue from docs/adlc/handoff-<date>.md`, so the new team continues the open items.
