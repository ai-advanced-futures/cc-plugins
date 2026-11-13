---
name: start
description: 'Start a software factory: a team of Claude Code background sessions (orchestrator, hitl, requests, decision-judge, scribe, planner, specifier, implementers, reviewers, verifiers, merger, monitoring and more) that build a product from the PRD and roadmap in a repo. Use when the user says "sofa", "sofa start", "start the team", "spawn the team" or "software factory".'
disable-model-invocation: true
metadata:
  internal: true
---

# sofa:start — start the software factory

This session is the launcher. It checks that the repository is ready, makes sure that `docs/adlc.md` meets the current template, and starts the orchestrator as a background session. The orchestrator starts the other roles.

## Files of the plugin

The skill folder is the root of the `sofa` plugin: two folders up from this file (`${CLAUDE_SKILL_DIR}/../..`). Find its absolute path once and use it as `<skill folder>`.

- `templates/ADLC.md` — the current team definition. Each repository has its own copy in `docs/adlc.md`.
- `templates/MIGRATION.md` — how an older `docs/adlc.md` maps to the current template.
- `references/roles/<role>.md` — the work of each role. Sessions read these files from the installed plugin, so a fix here reaches each repository.
- `references/assessor.md` — the assessor of decision-judge.
- `references/colours.md` — the session colour of each role. The mod sets it, and the orchestrator checks it.
- `skills/station/` — the base behavior of every session.
- `skills/readiness/`, `skills/setup/`, `skills/maturity/` — check, fix and score the repository.
- `commands/` — `/sofa:status`, `/sofa:request`, `/sofa:pause`, `/sofa:resume`, `/sofa:handoff`, `/sofa:stop`.
- `scripts/dispatch.sh` — starts 1 session of 1 role from the roles table.
- `scripts/sofa-state` — the state store CLI (`.sofa/state.db`).
- `hooks/register.tsx` — the mod: role colours, state store hooks, and the dashboard pane.
- `<repo>/docs/adlc.md` and `<repo>/docs/adlc/roles/<role>.md` — the team of 1 repository. The retro changes them.

A change that all repositories need goes to `ai-advanced-futures/cc-plugins` as an issue, which the retro offers.

## Step 1 — Readiness

Run `git fetch origin` in the main checkout, because the `review-contract` check reads the local `origin` ref. Then run the `sofa:readiness` skill. If it reports a `missing` item that blocks the start (marked `blocks start`), tell the user to run `/sofa:setup` and stop. Other missing items go in the `DONE` report at the end, so the user can fix them later with `/sofa:setup`.

The `review-contract` item does not block the start, but you wait for the user when it is not `ok`, because a review with no contract uses only the 2 built-in lenses and misses the rules of the repository:

- `ok`: ask nothing.
- `missing` or `wrong`: show `$ /code-review:setup` on its own line, and wait for the user to say `done` or `skip`.
  - `skip`: go on. The item stays in the report of step 3.5.
  - `done`: fetch `origin` and run the check again. If the item is `wrong` (the contract is only in the working tree), tell the user which files, and continue only after the user agrees. Land only those files on `main` with a worktree, a PR and a squash merge, as step 2 does for a migration, and leave each other change of the main folder as it is. Then fetch `origin` and run the check again. If the item is still not `ok`, go on and name it in the report of step 3.5.

Find the machine values of this start. They go in the start prompts and not in `docs/adlc.md`, because they differ on each machine that shares `docs/adlc.md`. Step 3 also records the GitHub person in the state store as `machine.instance`:

- Main folder: `git rev-parse --show-toplevel` in the main checkout, not in a worktree.
- Skill folder: the absolute path of the plugin root.
- GitHub account: `<slug>[bot]` when `<skill folder>/scripts/sofa-github settings` exits 0 (the team has a GitHub App; the name is the value of `GIT_AUTHOR_NAME` in its output, and the command does not call GitHub), else the active account of `gh auth status`. When `<skill folder>/scripts/sofa-github check` then exits 1, stop the start and show its line.
- GitHub person: the active account of `gh auth status` in this session.
- Launcher name: your session name, on the first line of `ListAgents`.

When the state store has the GitHub App values, `dispatch.sh` gives each new session the App identity (`sofa-github settings`): each `gh` and each `git` of the session acts as `<slug>[bot]`. Only a fresh start with `dispatch.sh` gives a session these settings: a `--resume` copy does not keep the settings of its first start. So after the App setup (`sofa:setup`, step 5.5), stop the team and start it again.

If the `CLAUDE.md` of the repository names a different process or harness for product work, ask the user which one wins before step 2.

## Step 2 — Make `docs/adlc.md` meet the current template

The result: `docs/adlc.md` and `docs/adlc/roles/` on `main` meet the current `templates/ADLC.md` and role files, and hold the values of this repository.

- If `docs/adlc.md` does not exist: tell the user to run `/sofa:setup`, which asks the setup questions and writes it. Stop.
- If its `sofa-template-version` is lower than the template: migrate it with `templates/MIGRATION.md`. The file already holds the answers of the setup questions; ask only for the new values that the migration lists (for example, risk appetite and tools per role). Before you land the migration, tell the user what it changes, and continue only after the user agrees, because each machine that runs the team shares this file. Land it on `main` with a worktree, a PR and a squash merge. If live sessions of an older team exist (`ListAgents`), stop them before step 3.
- If it meets the template: go to step 3.

## Step 3 — Start the orchestrator

1. Pull `main` in the main folder. Read `docs/adlc.md`. Make sure `.git/info/exclude` has the line `.sofa/`. Run `<skill folder>/scripts/sofa-state init` from the main folder. Then run `<skill folder>/scripts/sofa-state kv get machine.instance` from the main folder. When it exits 1 with `no key machine.instance`, run `<skill folder>/scripts/sofa-state kv set machine.instance <GitHub person>`. When it fails with another error, keep its last line for the message of item 2 or item 5, and go on. `sofa-state report` and `/sofa-dashboard` show this value after the word `instance`.
2. If `ListAgents` shows a live session with the orchestrator name, tell the user that the team runs, and how to open it (item 5). Also tell the user the write or the error of item 1. When `kv get` of item 1 printed a value that is not the GitHub person of step 1, tell the user that the live team runs for the operator with that login, and do not change the key. Stop, because a second orchestrator starts a second team.
3. When `kv get` of item 1 printed a value that is not the GitHub person of step 1, run `<skill folder>/scripts/sofa-state kv set machine.instance <GitHub person>`, because this start starts the team of that person. Then write this start prompt to a temporary file, with the machine values of step 1, and start the orchestrator from the main folder with `<skill folder>/scripts/dispatch.sh --adlc docs/adlc.md --role orchestrator --prompt-file <file>`:

   ```
   You are the orchestrator of the <prefix> team. Load the skill sofa:station.
   Then read docs/adlc.md on main, and your role files: <skill folder>/references/roles/orchestrator.md,
   and docs/adlc/roles/orchestrator.md if it exists. Where they differ, the repository file wins.
   Do the role "orchestrator" as written there. Start with "At start".
   Machine values: main folder <main folder>, skill folder <skill folder>, GitHub account <gh account>, GitHub person <gh person>.
   The launcher is <launcher name>. Send it a DONE message when all always sessions of the team are ready.
   ```

4. Wait for the `DONE` message from the orchestrator. It names the live sessions: the orchestrator, each `always` role, and monitoring when section 1 `Environments` names logs or metrics. The other roles are `on demand`: the orchestrator starts each one at its first trigger.
5. Tell the user which sessions run (the names from the `DONE`), and how to work with the team:
   - `claude agents --cwd <main folder>` shows the sessions of this repository in their role colours. Open the orchestrator, hitl or requests from there, or with `claude attach <name>`.
   - `/sofa:status` opens the dashboard; `/sofa:request <text>` gives the team new work.
   - The readiness items that are still missing, and `/sofa:setup` to fix them.
   - The old and the new value of the instance, when item 1 or item 3 wrote it (the old value is `none` for a missing key), or the error of item 1.

   Then this session has no more work.
