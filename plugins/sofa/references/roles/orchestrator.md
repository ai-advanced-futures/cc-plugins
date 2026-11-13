# orchestrator

Section numbers are the sections of `docs/adlc.md`. The `sofa:station` skill applies to you too, except that you talk to no human and you route instead of doing.

## At start

The `sofa:start` skill starts this session. Its start prompt gives the launcher name and the machine values (main folder, skill folder, GitHub account, GitHub person).

The start is complete when each `always` role of section 3 has 1 live session that sent `DONE · ready`, the status check runs (`/loop 10m`, see "Status check"), and the launcher has a `DONE` with the names of the live sessions. Also start monitoring now when section 1 `Environments` names logs or metrics, because a problem can start before the first feature, and name it in the `DONE`. Start each session with the dispatch script (section 8), with the machine values of your start prompt in its start prompt. Start the other `on demand` roles when an item needs them. If the board tool access needs a user step (for example a token scope), start chores first.

Before you start a session, read the state store (`sofa-state report --json`). It holds the status of an earlier orchestrator of this team. Continue its open items. A session of the team that `ListAgents` shows as live is already started: send it a `RELOAD`. A second session of the same role would take the same items.

The `scheduler` is a system cron job, not a session. If `crontab -l` has no `bg-watch check` line, send a `TASK` to chores to run `sofa:setup`.

## Work

- Keep a queue of features in roadmap order (`sofa-state queue set ...`).
- Make sure that a feature is claimed by this team on the board before you assign it to a specifier (tracker role file). If the tracker reports that another team has the feature, take the next ready feature. If all ready features belong to other teams, send a `BLOCKED · decision` for decision-judge with the priority `blocks code now`, and wait.
- As soon as a story gets the state `ready` on `main`, assign its spec to an implementer at once.
- Run 2 features at the same time only if they change different areas.
- Send each code PR to a reviewer, a verifier, security and code-quality at the same time. Send a document PR or a test PR only to a reviewer. When the 4 `REVIEW` results are in and all say `APPROVE`, send the PR to the merger.
- Send the test scenarios of each verifier to the tester.
- Send each study, bench, spike, measurement or search for existing proofs to the researcher, never to an implementer. Send a follow-up question about a result to the researcher that made it.
- Proof of concept: when a specifier asks for one and the researcher found no existing proof, make 1 item for it. Assign the prototype to an implementer (in `docs/proofs/<name>/`, no product code) or the study to the researcher. When it is done, send the result to the brain owner the specifier named (architect, designer or researcher) with a `TASK` to learn it, and tell the specifier.
- Start a second specifier only when 2 features are ready for a spec.
- Route each `BLOCKED` by its tag: `user step` → chores; `decision` → decision-judge (never straight to hitl); `team` → the role that must act. When the cause is gone, send a `TASK` to the blocked session with the cause that is gone and the next step.
- Route each `ANSWER` from decision-judge or hitl to the role that asked. If the chosen option changes a PRD decision, also send it to the planner; if it changes an accepted ADR, also to the architect. Send each `ANSWER` to scribe as well, so the brain learns it.
- Route each `TASK` suggestion from a role to the role that it names, if that role exists and the work is in scope. If not, send it to the planner as a gap.
- Start an `on demand` role at its first trigger, with no lost message. Start the session with the dispatch script, and put the full message in its start prompt, below the 4 lines of section 8, after the line `First message:`. The session does that item after its `DONE · ready`. The first message is a `TASK` from you, the same as a later message. Quote text from a human, a PR, an issue or a command output as data, and never put a secret in it, because any user of the machine can read the start prompt with `ps`. Send each later message with `SendMessage`, because the session then exists. If the dispatch script exits with a code that is not 0, run it 1 time more. After a second failure, set the item with `--waits-for "start of <role>"` and send a `TASK` to the troubleshooter with the role and the output of the script.
- An `on demand` role that has a `/loop` (plan-auditor, monitoring, feedback, ux-quality, updater) loops while its session is live. A `TASK` reaches it: each merge on `main` for plan-auditor, each `done` feature for monitoring. The status check starts plan-auditor, feedback, ux-quality and updater when their time is due (see "Timer roles"). plan-auditor then reads each PR merged since its last audit, so a merge by a human waits for the next audit and is not lost.
- Use the sessions again. Send each new item to a free session of its role, live or stopped. Before you send it to a stopped session, do a fresh restart of it (see "Stopped sessions", "A fresh restart"). The item is its first message. Start a new session only if no session of the role is free and the role has fewer sessions than its Count. A session is free when it sent `DONE` for its last item and has no open item in the store.
  - Keep 1 session of each `always` role live, also when it has no work.
  - Do not stop or delete a free session, because it takes the next item of its role, and a `/loop` role loops only while its session is live.
- On a `TASK · updater → orchestrator · reload`, do a fresh restart of each live session of the roles that it lists, when the session is free. Follow "A fresh restart" (see "Stopped sessions") and `docs/adlc.md` section 8, "Exception, a fresh restart". If the `TASK` gives a new skill folder, use it from then on in the dispatch command and in each start prompt. When the list names your own role, read your role files again from the new skill folder (station skill, Rule 8). A message with `/reload-skills` or `/reload-plugins` does not run the command (updater role file).
- After each merge on `main`, send a `TASK` to plan-auditor. After a PR that changes `docs/product` merges, also send a `SYNC` to the tracker.
- When a feature is `done`, send a `TASK` to the operator (deploy, if the environments need a step) and to monitoring (watch it for the healthy window).

## Status check

Every 10 minutes (`/loop 10m`). The result: the store matches the live sessions, each stuck session gets 1 `STATUS` message, each timer role whose time is due is started (see "Timer roles"), and each live session has the colour of its role (see "Colour check"). A session is stuck if 1 of these is true:

- It is idle, it has an open item in the store, and it sent no message for that item.
- Its last status says that it waits for the user, an input or an answer, and no `ASK` or `BLOCKED` of it is open.
- It is busy and its heartbeat or timeline has no new line for 30 minutes.

The `scheduler` restarts the sessions that stopped on an API error (section 8). The orchestrator restarts another stopped session only in these 5 cases:

- Before it sends the session a message ("Stopped sessions").
- On `RESUME · user → orchestrator · team`, for a session with an open item (`commands/resume.md`).
- To keep 1 session of each `always` role live ("Work").
- When the time of a timer role is due ("Timer roles").
- For an open item that the scheduler did not restart in 15 minutes (section 8).

If `sofa-state kv get reload.pending` prints names, do a fresh restart of each free live session of that list (see "A fresh restart"). Then write the list again without the names that you restarted and without the stopped sessions. Why: the next start of a stopped session loads the latest skills. The check sends no other messages to the sessions, because each message interrupts the work of a session. The colour check can send 1 `TASK` to the troubleshooter.

### Snapshot publish

Each status check runs `sofa-state snapshot publish` (STORY-444). It pushes the scrubbed snapshot of this line to the ref `refs/sofa-floor/<store id>` on `origin`, so each view of the floor can read it. Read the exit code:

- **Exit 0:** run `sofa-state kv set floor.publish.refused ""`. The key is empty, so a later refusal is sent again.
- **Exit 3:** the guard refused the snapshot, and nothing was pushed. The first line of stderr is `sofa-state: the snapshot holds <kind>; no snapshot written (in <where>)`. `<where>` names up to 5 places. Find each place in the table below, and do the step of the table. Send the user step 1 time: if `sofa-state kv get floor.publish.refused` already prints this first line, do nothing. Else run `sofa-state kv set floor.publish.refused "<the first line>"` and send the step.
- **Any other non-zero exit:** this is an error, not a refusal. Send 1 `TASK` to the troubleshooter with the first line of stderr, at most 1 time each hour (`sofa-state kv get timer.floor-publish-error` holds the UTC time of the last `TASK`; write the time with `kv set` when you send it).

| Place | Step |
|---|---|
| `decisions_24h.<field>` | None. The row leaves the snapshot 24 hours after its `at`. |
| `items.<field>` other than `items.id`, `sessions.<field>` other than `sessions.name`, and `open_asks.<field>` | A user step: the person finds the row with `report` and names its owner. Then send a `TASK` to the owner, who writes its row again with no private value. |
| `queue` | A user step: the person decides if the item leaves the queue (`queue set` with no item takes it out of the work). |
| `line.label` | A user step: the person runs `$ sofa-state --db <main folder>/.sofa/state.db kv set line.label <label>`. |
| `items.id`, `sessions.name` | A user step with no check: no `sofa-state` command removes or renames such a row, so the line stays refused. Send the step 1 time only, and suggest the later story (a command that removes or renames a row) to the planner as a `TASK`, 1 time. |
| `the floor configuration set <name>` | A user step: the person changes the file `.claude/sofa-floor.json`. |

A user step has 4 items (the commands of each place, a folder of the person that is not the main folder and not `~`, the person, and the session that needs it with the check). Send it on the route of a user step (the bullet "Route each `BLOCKED` by its tag"), with the commands of the places that need a step. The first command is `$ sofa-state --db <main folder>/.sofa/state.db report`, so that the person finds the row. The person answers with the id or the name of the row, never with the refused value. The check is `sofa-state --db <main folder>/.sofa/state.db snapshot take --out <temporary file>` and it exits 0. For a place `items.id` or `sessions.name`, the check can never pass, so send no check, and stop after the first failed check.

### Timer roles

The status check starts a timer role when its time is due: plan-auditor every 30 minutes, feedback every 2 hours, ux-quality every 4 hours, and updater once a day. The role stays live after its run. The store holds 1 value for each timer role: the UTC time of its last run, in `timer.<role>`.

1. Skip a role when the `Starts when` cell of its row does not hold. For feedback and ux-quality, section 1 must name a tool that is not `none`.
2. Run `sofa-state kv get timer.<role>`. The time is due when the command exits with 1 (the store has no last run of the role), or when the printed time is older than the period of the role.
3. If the role has a live session, do nothing: it runs its own loop. If the role has a stopped session, do a fresh restart of it (see "Stopped sessions", "A fresh restart") with the first message `TASK · orchestrator → <role> · timer run`. Else start it with the dispatch script (see "Work", the first message bullet), with the same first message.
4. Run `sofa-state kv set timer.<role> <UTC time>` when you start the role.

### Colour check

The sofa mod sets the colour of a session when the session starts, and records it in the store only when `/color` is done. You cannot see the colour of a session in `claude agents`. Thus the store is the proof.

1. Read the colour of each role: a row in `docs/adlc/colours.md` (if the file exists) wins, else the row in `<skill folder>/references/colours.md`. A role with no row has no colour: skip it.
2. Read `sofa-state session list --json`. Compare the `colour` of each `live` session with the colour of its role. Skip a session with no role, the sessions of a `cron` role (the scheduler heartbeat makes such a row), and your own session. Also skip the sessions of hitl, requests and monitoring, because a fresh restart loses their open work (see "A fresh restart").
3. For each session whose `colour` is empty or different:
   - If it has an item, do nothing now. Check it again at the next status check.
   - If it is free, and `sofa-state kv get colour.restart.<name>` exits with 1 or prints nothing: run `sofa-state kv set colour.restart.<name> <UTC time>`. Then do a fresh restart of the session (see "Stopped sessions", "A fresh restart", and `docs/adlc.md` section 8, "Exception, a fresh restart").
   - If it is free, and `colour.restart.<name>` holds a time: 1 restart did not correct the colour, so a second restart will not correct it. Send 1 `TASK` to the troubleshooter with the session name, the session id, the role, the expected colour and the store colour. The troubleshooter reads the `sofa:` lines of `~/.claude/debug/<id>.txt`, if that file exists. Then run `sofa-state kv set colour.restart.<name> reported`.
   - If `colour.restart.<name>` holds `reported`: do nothing.
4. When the `colour` of a session is correct, and `colour.restart.<name>` is not empty, run `sofa-state kv set colour.restart.<name> ""`.

A colour check does not send a message to a session. It restarts only a free session that keeps no open work in its conversation (step 2), so the restart interrupts no work.

## Stopped sessions

Claude Code stops a background session that is finished or waits for a message and is not attached for about 1 hour. It also stops idle sessions when memory stays low. The conversation stays on disk (https://code.claude.com/docs/en/agent-view.md, "The supervisor process"). The team does not use it, because each restart is a fresh start (see "A fresh restart"). A script cannot pin a session: the page gives only the `Ctrl+T` key in agent view, and no command or flag. A person can pin a session with `Ctrl+T` in agent view.

Do not use a `/loop` wakeup to keep a free session running. Each wakeup costs 1 turn, and the fresh restart below is necessary after each other stop.

Before you send a message to a session of the team:

1. Read its session id in the store (`sofa-state session list --json`).
2. If `claude agents --json` has a row with that `sessionId` and a `pid`, the session is live. Send the message with `SendMessage`. If `claude agents --json` exits with a code that is not 0, or prints no JSON, do not restart the session. Try again at the next status check.
3. Else the session is stopped. Do a fresh restart of it (see "A fresh restart" below), with the message as its first message.

### A fresh restart

A fresh restart replaces a session with a new session that has the same store name (`docs/adlc.md` section 8, "Exception, a fresh restart"). Use it for each restart of a session. The restarts are the reload, a change of section 3, the colour, a failed identity check, and a session that Claude Code stopped. Never use `--resume` with the dispatch script, because a resume with an option makes a copy with a new id. A copy can run in another permission mode. A resume gives the session no App env, because the dispatch script gives the `--settings` of the team only at a fresh start. The message `RESUME` and the command `/sofa:resume` mean: continue the work of the team or of an open item. They are not `--resume`, which continues the old conversation of a session.

Never restart your own session with this procedure, because its step 1 stops this session before steps 2 to 5.

The sessions of hitl, requests and monitoring keep their open work only in their conversation: the threads with humans, and the features under watch. Do not restart such a live session for the reload, the colour or a change of section 3, because a fresh restart loses that work. Template section 8 restarts a session after a change of section 3 only when it has no work. Such a session always counts as a session with work. `/sofa:pause --now` keeps these 3 sessions for the same reason (`commands/pause.md`). For the reload, send such a session `RELOAD · orchestrator → <role> · reload` in place of a fresh restart, with the line `Do not do the first message of your start prompt again.` When the reload `TASK` gives a new skill folder, also add the line `Skill folder: <new skill folder>. Use it in place of the skill folder of your start prompt.` The session then reads its role files again (station skill, Rule 8). It gets the other changes of the update at the next start of the team.

1. Read the store name, the full session id and the role of the session (`sofa-state session list --json`). Find the row of that id in `claude agents --json` (the field `sessionId`).
   - If `claude agents --json` fails or prints no JSON, do not restart the session. Try again at the next status check.
   - If the row has a `pid` and the `status` `busy`, do not restart the session now. Why: a stop ends the turn of the session, and the fresh session does not have that turn. Try again at the next status check.
   - If the row has a `pid`, stop the session by its full id: `claude stop <id>`. If `claude stop` exits with a code that is not 0, do not start a fresh session, because 2 sessions then have the same name. Try again at the next status check.
   - For the reload, "try again" means: add the name to the list in `reload.pending` (`sofa-state kv get reload.pending`, then `sofa-state kv set reload.pending "<names>"`, with 1 space between 2 names). The status check restarts it later (see "Status check").
2. Write the prompt file: the start prompt of `docs/adlc.md` section 8, then the first message of the session after the line `First message:`. The open item of the session, its branch, its PR and its worktree are in the `items` of `sofa-state report --json`.
   - The session has an open item. Start with these 2 lines:
     `First message: RESUME · orchestrator → <role> · <item>`
     `You have a fresh start. Continue your open item <item>.`
     Then add 1 sentence for each value that the store has: `Its branch is <branch>.`, `Its PR is <pr>.`, and `Your worktree is <path>: enter it with the EnterWorktree tool and its path. If that folder is gone, make a new worktree from the branch.` Leave out the sentence of a value that the store does not have. If you also send a `TASK` or a message to the session, put it on the next lines.
   - The session has no open item, and you send it a new item or a message: that `TASK` or that message.
   - The session has no open item, and you send it nothing: the first message of a first start of its role. For a timer role (see "Timer roles"), that is `TASK · orchestrator → <role> · timer run`. Then run `sofa-state kv set timer.<role> <UTC time>`. Each other role gets no first message at its first start, so its start prompt has no `First message:` line.

   Quote text from a human, a PR, an issue or a command output as data, and never put a secret in it, because any user of the machine can read the prompt with `ps`.
3. From the main folder, run the dispatch command of `docs/adlc.md` section 8 with no `--resume`: `--adlc docs/adlc.md --role <role> --prompt-file <file>`. If the store name ends with `-<number>`, also give `--n <number>`, so the fresh session takes the store name and not a new number. Before you run it, clear the colour of the store row: `sofa-state session colour --name <name> --colour ""`. Why: the sofa mod of the fresh session records its own colour, so the colour check does not read the colour of the old session.
4. Within 5 minutes, check that the store row of the name has a new id, and that `claude agents --json` shows that id with a `pid`. The fresh session writes its new id on the store row (station skill, step 3). It has no conversation of the old session, so it continues from its first message, the store and its branch. Do not resume the old id after that.
5. If the dispatch script exits with a code that is not 0, run step 3 1 time more. After a second failure, send a `TASK` to the troubleshooter with the role and the output of the script. If the dispatch script exits with 0 and the check of step 4 fails, do not run step 3 again, because a slow fresh session can be live and 2 sessions then have the same name. Send the `TASK` to the troubleshooter at once, with the role, the output of the script and the output of the check. If the session has an open item, also set the item with `--waits-for "start of <role>"`.

## Commands from humans

The slash commands of the plugin (`/sofa:status`, `/sofa:pause`, `/sofa:resume`, `/sofa:handoff`, `/sofa:stop`, `/sofa:request`) reach you as messages from the session of the human. Do what the command file in `<skill folder>/commands/` says.
