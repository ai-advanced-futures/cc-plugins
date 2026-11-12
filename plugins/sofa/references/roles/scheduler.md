# scheduler

Section numbers are the sections of `docs/adlc.md`. The scheduler is not a session. It is a line in the crontab of the machine, so it fires even when a Claude call of the last run failed on an API error:

```
*/5 * * * * PATH=<claude folder>:/usr/local/bin:/usr/bin:/bin:<jag folder>; cd <main folder> && claude -p --model claude-haiku-5-5 --permission-mode bypassPermissions "/bg-watch check" >> <main folder>/.sofa/scheduler.log 2>&1; <plugin root>/scripts/sofa-state --db <main folder>/.sofa/state.db session heartbeat --name <prefix>-scheduler
```

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

`sofa:setup` installs the line (it shows it first, and the user agrees). `bg-watch check` finds each session that stopped on an API error, restarts it, and sends it `retry`. The heartbeat shows on the dashboard; a heartbeat older than 15 minutes means the cron does not run. Read `.sofa/scheduler.log` to find the cause.

The orchestrator does not restart a session that stopped on an API error. It resumes a session that Claude Code stopped when it was free (orchestrator role file, "Stopped sessions").
