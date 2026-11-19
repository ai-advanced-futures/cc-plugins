# Auto mode rules of a factory

This file is the inventory of the operations of the team, and it says how the auto mode classifier of Claude Code must judge each one. The rule text is in `auto-mode.json`, next to this file. The command `<skill folder>/scripts/sofa-automode` writes it into the settings. `/sofa:setup`, step 4.5, runs that command.

## What the rules change, and what they do not change

- Auto mode sends each action that is not a read and not an edit in the working folder to a classifier. The classifier reads 4 lists of text rules: `environment`, `allow`, `soft_deny` and `hard_deny`.
- The classifier reads these lists only from the user settings (`~/.claude/settings.json`), the managed settings, and an inline `--settings` value. It does not read the settings files of a repository. So the rules are a value of the machine, not of the repository, and they apply to each auto mode session of the user.
- A session of the team gets its work as a `TASK` message of the orchestrator. The classifier does not count a message of a session as the agreement of a person. So only an `allow` entry lets a session of the team do an operation that a built-in rule blocks.
- Each list that the command writes holds `"$defaults"`, so each built-in rule stays.
- The rules apply only to a session that runs in the permission mode `auto`. A session that `dispatch.sh` starts with another permission mode does not use the classifier. The rules also apply to a session that a `--resume` started in `auto`, and to the scheduler when its launcher uses auto mode.
- An allow rule of `permissions.allow` (for example `Bash(git:*)` or `Bash(gh api:*)`) answers before the classifier. Then the classifier does not see the command. `autoMode.classifyAllShell: true` sends each shell command to the classifier. `sofa-automode check` lists the allow rules that answer first.
- The classifier is a model, so its answer for the same command can change between 2 runs. Claude Code also has a server-side review with rules that no command prints. In the live probes of this file, the same PR comment and the same `dispatch.sh` command were permitted in some runs and blocked in other runs. So the rules make a block less frequent, and they do not make a result sure. For an operation that must never run, use a `permissions.deny` rule in the `--settings` value of the session: it answers before the classifier, in each permission mode.
- The `allow` entries name the role that does the operation (the merge: `<prefix>-merger`; a `VERDICT:` comment: the review roles; `dispatch.sh`: `<prefix>-orchestrator` and `<prefix>-updater`). The classifier cannot prove that a session has that role: it reads the session name and the command as text. So a role scope makes a wrong permit less likely, and it is no security boundary. A rule that must hold for each session is a `permissions.deny` rule (see above), not an entry of this file. `hard_deny` stays empty, because a `hard_deny` entry also blocks the work of the roles that must do the operation.
- After 3 blocks in a row, or 20 blocks in a session, auto mode asks a person again. A session with no person then stops at that prompt. So a block must be rare in normal work: when a role gets a block for a normal operation, add the operation to the inventory in this file and to `auto-mode.json` in a pull request.

## Inventory: operations that the team does

`All` means each role. The column "Built-in rule" names the default rule that blocks the operation with no added rule. `none` means that the defaults permit it.

| Operation | Roles | Built-in rule | Added rule |
|---|---|---|---|
| Read files, `git status`, `git fetch`, `git ls-remote`, REST reads with `gh api` | All | none | none |
| Edit files and commit in a worktree of the repository | All that write | none | none |
| `git worktree add`, `remove`, `prune`; `git merge --no-edit origin/main`; delete of the own local branch (`wrapup`) | All that write | none | none |
| `git push origin <branch>` of a team branch, with no force | All that write | none | none |
| Edit a skill, a command, a role file, `docs/adlc.md`, a `CLAUDE.md` file, `.claude/rules`, `.claude/skills` | retro, designer, implementer, specifier | Self-Modification, Instruction Poisoning | allow: Instruction files are the product |
| Open a pull request, comment (also a `VERDICT:` comment of a review role), edit a body, open an issue, set a label, close a fixed issue | All | External System Writes, Self-Approval | allow: Team GitHub writes |
| Write the GitHub Project (`sofa-publish`, `github apply`) | tracker | External System Writes | allow: Team GitHub writes |
| Squash merge of a pull request (`gh pr merge --squash --match-head-commit`, or the REST merge) | merger | Merge Without Review | allow: Team merge |
| Post and read in the Slack channel with `sofa-slack` | hitl, requests | External System Writes | allow: Team Slack posts |
| Start a session with `dispatch.sh --role <role> --prompt-file <file>` (never `--prompt` and never `--resume`, because the script starts the session with `--permission-mode bypassPermissions`); `claude agents`; `claude stop <job id>` of a team session | orchestrator, updater | Create Unsafe Agents, Interfere With Workloads | allow: Team sessions |
| `SendMessage`, `CronCreate`, `CronDelete`, `CronList`, `Monitor` | All | none (Multi-Agent Coordination, Claude Code Scheduling) | none |
| Live check: `claude -p --plugin-dir` in a fixture folder; `tmux -L <own name>`; stop of the own process group | verifier, tester, implementer, specifier, security, researcher | Create Unsafe Agents, Interfere With Workloads, Tmux Self Drive | allow: Live checks of a plugin |
| Tests and gates: `python3 -m pytest`, `bash <file>.test.sh`, the check scripts, `uv pip install -r requirements-dev.txt` | All that build or review | none (Declared Dependencies) | none |
| `uvx mypy`, `uv run` of a repository script, `npx` of `skills` or `ctx7` at the version that a tracked file of the repository names (`skills-lock.json`, the find-docs skill), `npx skills list` and `update`, `uv pip install` into a virtual environment of the session, `claude plugin update` | implementer, researcher, updater, chores, setup | Code from External, Untrusted Code Integration | allow: Pinned tool runs |
| The state store and Plan: `sofa-state`, `sofa-plan`, `sofa-publish`, `sofa-people` | All | none | none |
| The Plan backup push of `refs/dolt/data` | Plan, `/sofa:stop` | Git Destructive (a ref that is not a branch) | allow: Plan backup |
| The brain scripts through their skills (`knowledge`, `ddd`, `prd`, `system-design`, `adr`) | scribe, business-domain, planner, designer, architect | none | none |
| Web search and page reads | researcher | none (Read-Only Operations) | none |

## Inventory: operations that stay blocked

The rules of `docs/adlc.md` and of the station skill forbid these operations. The defaults permit some of them (a push to the default branch, a forced push of the own branch), so `soft_deny` adds them.

| Operation | Built-in rule | Added rule |
|---|---|---|
| A forced push, a `+` refspec, a delete of a remote ref, a rebase of a pushed branch, a direct push to the default branch | Git Destructive (only for the work of other people) | soft_deny: Team push rules |
| `git -c user...`, a `GIT_AUTHOR_` prefix, `git config user.name`, the real `gh` by its full path, `gh auth login` or `token` | none | soft_deny: Team identity rules |
| `env`, `printenv` with no name, a read of the App key file, of the token cache or of the `env` values of the local settings | Credential Materialization (in part) | soft_deny: Team secret rules |
| A `sqlite3` write to the state store, a raw `bd` command | none | soft_deny: Team store rules |
| `claude rm`, `claude respawn --all`, `pkill -f`, `tmux kill-server` with no `-L`, a stop of a session that is not of the team | Interfere With Workloads (in part) | soft_deny: Team session rules |
| `gh pr merge --admin`, `--auto`, `--delete-branch`; `gh pr review --approve` | Merge Without Review, Self-Approval | none (the allow rules do not cover them) |
| A delete of a comment, an issue, a branch, a tag or a release; a change of repository settings, secrets or collaborators | External System Writes, Permission Grant | none (the allow rules do not cover them) |

## Inventory: operations that need a person

A session sends each of these as `BLOCKED · user step` or as a card (`docs/adlc.md`, section 2, rule 4). The classifier blocks them for a session, and that is correct. The crontab row has no narrow allow rule on purpose: in a live probe, an allow rule for the change of 1 crontab line also permitted the install of a new crontab file, because the classifier reads the command and not the lines that it writes.

The entry Team merge also excludes a pull request that changes `.github/workflows/`, because an `allow` entry wins over a `soft_deny` entry.

| Operation | Built-in rule | Added rule |
|---|---|---|
| Each write of the crontab: the install of the scheduler line, and the change of its plugin root path after an update of the plugin (`roles/updater.md`, step 4) | Unauthorized Persistence | soft_deny: Team machine rules |
| An install of a program (`cargo install` of jag, `brew install`), `claude plugin marketplace add` or `remove` | Code from External | soft_deny: Team machine rules |
| A change of a settings file, a permission mode, an allow rule, or these rules | Self-Modification | soft_deny: Team machine rules |
| The merge of a pull request that changes `.github/workflows/` | none | soft_deny: Team workflow rule |
| A login, a token, a key rotation, a payment | Credential and account rules | none |
| A delete of data, a revert on the default branch, a new form of ref on `origin` | Git Destructive, Irreversible Deletion | none |

## The command

`<skill folder>/scripts/sofa-automode --repo <main folder> COMMAND`:

- `render`: prints the `autoMode` block of this factory. It reads `Repository`, `Team prefix` and `Slack` of `docs/adlc.md`, section 1, and 2 keys of the state store: `machine.github-app.slug` (the App) and `automode.repo-alias` (a second name of the same repository on GitHub, after a rename). A team with no Slack channel gets no Slack rule. `--repo-alias <owner>/<name>` gives the second name for 1 run, and `--repo-alias none` gives none.
- `check`: compares the user settings with the rendered rules, and prints 1 line for each list, the value of `classifyAllShell`, the allow rules that answer before the classifier, and `permissions.defaultMode`. Exit 0 only when each entry is there and current.
- `apply`: copies the settings file to `<file>.sofa-copy-<time>` (mode 600), then writes the entries. It keeps each other key and each other entry of the file, and it adds `"$defaults"` to each list that it writes, so each built-in rule stays. When it drops a value that is not a list or an `autoMode` value that is not an object, it prints a line. When the settings file is a symbolic link, it writes the file that the link names. `--classify-all-shell` also sets `autoMode.classifyAllShell` to `true`.
- `remove`: copies the file, then takes the entries of this factory out. It also takes out a list that holds only `"$defaults"` and an `autoMode` block that is then empty, so a file that `apply` made comes back to its first form. It keeps `"$defaults"` in a list that still holds an entry of the person, because it cannot know whether `apply` or the person added it, and it keeps `autoMode.classifyAllShell`: that value is a choice of the person, and `remove` prints a line when it stays.

Each written entry starts with the mark `[sofa <owner>/<name>]`. A second `apply` replaces only the entries with that mark, so a machine can hold the rules of 2 factories and the personal rules of the user.

## After a change of the rules

1. Run `claude auto-mode config`. The output must hold each entry with the mark and each built-in rule.
2. Run `claude auto-mode critique`. It reads the added rules and reports a rule that is not clear or that repeats a default.
3. Only a restart makes sure that a session uses the new rules. The orchestrator gives each session a fresh restart when it has no work (`roles/orchestrator.md`, "A fresh restart").
