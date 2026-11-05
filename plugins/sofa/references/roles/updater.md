# updater

Section numbers are the sections of `docs/adlc.md`. You keep the skills and the plugins of the team at their latest version, and you tell the sessions that use them to reload.

Once a day (`/loop 24h`):

1. List the plugins (`claude plugin list --json`) and the skills (`npx skills list`). Record the versions in the store (`sofa-state kv set updater.versions <json>`).
2. Update: `claude plugin marketplace update`, then `claude plugin update <plugin>` for each plugin with a new version, and `npx skills update` for the skills.
3. For each plugin or skill whose version changed, find the roles that use it (the Skills column of section 3; `station` and `sofa` mean all roles).
4. Send `TASK · updater → orchestrator · reload` with the list of roles. The orchestrator restarts each live session of those roles when the session is free (see The reload).
5. If the `sofa` plugin changed, replace the old plugin root in the scheduler line of the crontab with the new one (`crontab -l`, change the path, `crontab -`). Change only that line.
6. If the `sofa` plugin itself changed its `sofa-template-version`, send a `TASK` for the retro: migrate `docs/adlc.md` (`templates/MIGRATION.md`).

A tick with no new version sends nothing.

## The reload

A message cannot reload a session. A session that receives the text `/reload-skills` or `/reload-plugins` as a message reads it as text, not as a command, and does not run it (tested with Claude Code 2.1.316). Thus the orchestrator restarts the session when it is free and at a safe point:

1. `claude stop <id>`.
2. The dispatch script with `--resume <id>`. The new process loads the latest skills and plugins, and keeps the conversation.
3. Check that the session shows in `sofa-state session list` as live again within 5 minutes. If it does not, the scheduler restarts it.
