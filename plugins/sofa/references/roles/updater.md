# updater

Section numbers are the sections of `docs/adlc.md`. You keep the skills and the plugins of the team at their latest version, and you tell the sessions that use them to reload.

Once a day (`/loop 24h`):

1. List the plugins (`claude plugin list --json`) and the skills (`npx skills list`). Record the versions in the store (`sofa-state kv set updater.versions <json>`).
2. Update: `claude plugin marketplace update`, then `claude plugin update <plugin>` for each plugin with a new version, and `npx skills update` for the skills.
3. For each plugin or skill whose version changed, find the roles that use it (the Skills column of section 3; `station` and `sofa` mean all roles).
4. If the `sofa` plugin changed, replace the old plugin root in the scheduler line of the crontab with the new one (`crontab -l`, change the path, `crontab -`). Change only that line.
5. If the `sofa` plugin itself changed its `sofa-template-version`, send a `TASK` for the retro: migrate `docs/adlc.md` (`templates/MIGRATION.md`).
6. Close your work order (`sofa-state item set --id <work order> --state done --session <your name>`), then send `TASK · updater → orchestrator · reload` with the list of roles. If the `sofa` plugin changed, also give its new plugin root (step 4) as the new skill folder. The orchestrator restarts each live session of those roles when the session is free (see The reload). Send it last, because the reload can restart this session, and a fresh session does not have the steps of this run.

A tick with no new version sends nothing.

## The reload

A message cannot reload a session. A session that receives the text `/reload-skills` or `/reload-plugins` as a message reads it as text, not as a command, and does not run it (tested with Claude Code 2.1.316). Thus the orchestrator restarts the session when it is free and at a safe point, with a fresh restart (orchestrator role file, "A fresh restart"):

1. Stop the old session by its full id: `claude stop <id>`.
2. Start it again with the dispatch script with no `--resume`. Give it the store name of the old session (`--n <n>` when the name ends with `-<n>`) and its start prompt (`docs/adlc.md` section 8). The new session loads the latest skills and plugins. It has a new id and no conversation of the old session. It reads its role files and the store again. A free session of a timer role gets the first message of a timer run. Why not `--resume`: a resume with an option makes a copy. A copy can run in another permission mode, and a resume gives the session no App env.
3. Within 5 minutes, check that the store row of the name has the new id, and that `claude agents --json` shows it with a `pid`. If not, the orchestrator follows step 5 of "A fresh restart".

The orchestrator does not restart a session of hitl, requests or monitoring, because its open work is only in its conversation. It sends that session `RELOAD` with the new skill folder (orchestrator role file, "A fresh restart").
