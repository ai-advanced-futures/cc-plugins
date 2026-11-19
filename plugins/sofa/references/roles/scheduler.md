# scheduler

Section numbers are the sections of `docs/adlc.md`. The scheduler is not a session. It is a line in the crontab of the factory machine, so it fires even when a Claude call of the last run failed on an API error:

```
*/5 * * * * PATH=<claude folder>:/usr/local/bin:/usr/bin:/bin:<jag folder>; cd <main folder> && python3 <plugin root>/scripts/bg-watch check >> <main folder>/.sofa/scheduler.log 2>&1; <plugin root>/scripts/sofa-state --db <main folder>/.sofa/state.db session heartbeat --name <prefix>-scheduler
```

`scripts/bg-watch check` starts `claude-sonnet-5-5` with `--permission-mode auto` and `--permission-prompts none`. It passes per-run settings through inline `--settings` JSON, not project settings, which auto mode ignores. It keeps the built-in classifier rules, sets `autoMode.classifyAllShell` to `true`, and adds the scope of the check: read session logs, write watcher state, respawn selected idle sessions, and send `retry`. It offers only Bash, SendMessage, and ToolSearch, denies file-edit tools, and disables bypass mode. It changes no user settings and has no fallback to bypass mode or another model.

Use Claude Code 2.1.259 or later, with Sonnet 5.5 and auto mode available to the account. If the command is unsupported, auto mode is disabled by policy, or an action is denied, stop and report the cause from the log. Do not add an allow-all rule or bypass the denial. Auto mode checks the watcher's actions; it does not isolate the disk or change the permissions of a session that it respawns.

For an existing installation, preserve the old cron line and replace only that line with this launcher after the user agrees. Refresh `bg-watch` through setup step 2.5 when readiness reports an old or missing pin. The older copy uses stop-then-respawn and has no check lock. `/bg-watch stop` cancels a session schedule only; it does not remove this OS cron line. Never use `crontab -r` to stop only this watcher.

The machine values:

- `<claude folder>`: the folder of the `claude` command (`dirname "$(command -v claude)"`). Cron runs with a short `PATH` that does not have it.
- `<jag folder>`: the folder of the `jag` command (`dirname "$(command -v jag)"`). `bg-watch check` asks jag which sessions are stuck, and cron runs with a short `PATH` that does not have it. It comes after `/bin`, because the folder of jag (often `~/.cargo/bin`) holds the other tools of the user, and they must not hide a system tool. When this folder is the `<claude folder>` or a folder that is already in the line, write the line with no second copy of it. Use the value only when it starts with `/` and has none of these characters: `%` `;` `&` `|` a space `'` `"`. In a crontab, `%` ends the command, and the others change how the shell reads the line. When the value is not safe (for example `command -v jag` finds an alias or a function), do not write the line, because cron would run a different command from it, and tell the user to put `jag` in a folder with a plain path.
- `<main folder>`: the main checkout of the repository. Claude Code must trust this folder (start `claude` in it 1 time and accept the trust question). Else `claude -p` stops with "Workspace not trusted".
- `<plugin root>`: the folder of the installed sofa plugin. A plugin update can change it. Thus the updater replaces the path in the crontab line after each update of sofa.
- `bg-watch` is a factory skill (`references/factory-skills.txt`): `/sofa:setup` installs it at project level. The cron line runs in the main folder, so the project skill works.

The install of jag. This is a value of the plugin, not a machine value. `<jag commit>` is the full commit ID of the jag repository that this version of sofa was tested with: `8ea270e5eedb45ada28cce69c19b40139a72b540`. It needs Rust 1.99 or later, and the build takes some minutes. `cargo install` does not read the toolchain file of jag, so check `rustc --version` first. When it is older and `rustup` is on the machine, run `rustup toolchain install 1.99.0` and use `cargo +1.99.0 install` in place of `cargo install`, after the user agrees. Do not change the default toolchain of the user:

```
cargo install --locked --git https://github.com/ai-ready-future/jag --rev 8ea270e5eedb45ada28cce69c19b40139a72b540 jag-cli
```

`sofa:setup` installs the line (it shows it first, and the user agrees). `bg-watch check` finds each session that stopped on an API error, restarts it, and sends it `retry`. The heartbeat shows on the dashboard; a heartbeat older than 15 minutes means the scheduler has not recorded a recent run. A heartbeat is not proof that the check succeeded: the cron records it even after a failed check. Read `.sofa/scheduler.log` for the result and any denied actions.

The orchestrator does not restart a session that stopped on an API error. It gives a session that Claude Code stopped a fresh restart only in the cases of the orchestrator role file ("Status check", "A fresh restart").

