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
- `references/planning.md` — backend selection, Plan calls and claims, board publication, backup and restore, and legacy conversion.
- `scripts/sofa-plan` — selects the configured profile, resolves installed Plan, and binds the absolute profile for commands.
- `references/assessor.md` — the assessor of decision-judge.
- `references/colours.md` — the session colour of each role. The mod sets it, and the orchestrator checks it.
- `skills/station/` — the base behavior of every session.
- `skills/readiness/`, `skills/setup/`, `skills/maturity/` — check, fix and score the repository.
- `commands/` — `/sofa:status`, `/sofa:floor`, `/sofa:request`, `/sofa:pause`, `/sofa:resume`, `/sofa:handoff`, `/sofa:stop`.
- `scripts/dispatch.sh` — starts 1 session of 1 role from the roles table.
- `scripts/sofa-state` — the state store CLI (`.sofa/state.db`).
- `hooks/register.tsx` — the mod: role colours, state store hooks, and the dashboard pane.
- `<repo>/docs/adlc.md` and `<repo>/docs/adlc/roles/<role>.md` — the team of 1 repository. The retro changes them.

A change that all repositories need goes to `ai-advanced-futures/cc-plugins` as an issue, which the retro offers.

## Step 1 — Readiness

Run `git fetch origin` in the main checkout, because the `review-contract` check reads the local `origin` ref. Then run the `sofa:readiness` skill. If it reports a `missing` or `wrong` item that blocks the start (marked `blocks start`), tell the user to run `/sofa:setup` and stop. The item `adlc-version` is the exception: go on, because step 2 migrates `docs/adlc.md`. The item `factory-machine` is such an item: it is `wrong` on a machine that is not the factory of the `Factory` row of `docs/adlc.md`, and a team must not start there, because a repository has 1 factory. Other missing items go in the `DONE` report at the end, so the user can fix them later with `/sofa:setup`.

The `review-contract` item does not block the start, but you wait for the user when it is not `ok`, because a review with no contract uses only the 2 built-in lenses and misses the rules of the repository:

- `ok`: ask nothing.
- `missing` or `wrong`: show `$ /code-review:setup` on its own line, and wait for the user to say `done` or `skip`.
  - `skip`: go on. The item stays in the report of step 3.5.
  - `done`: fetch `origin` and run the check again. If the item is `wrong` (the contract is only in the working tree), tell the user which files, and continue only after the user agrees. Land only those files on `main` with a worktree, a PR and a squash merge, as step 2 does for a migration, and leave each other change of the main folder as it is. Then fetch `origin` and run the check again. If the item is still not `ok`, go on and name it in the report of step 3.5.

Find the machine values of this start. They go in the start prompts and not in `docs/adlc.md`, because they are paths and accounts of the factory machine:

- Main folder: `git rev-parse --show-toplevel` in the main checkout, not in a worktree.
- Skill folder: the absolute path of the plugin root.
- GitHub account: `<slug>[bot]` when `<skill folder>/scripts/sofa-github settings` exits 0 (the team has a GitHub App; the name is the value of `GIT_AUTHOR_NAME` in its output, and the command does not call GitHub), else the active account of `gh auth status`. When `<skill folder>/scripts/sofa-github check` then exits 1, stop the start and show its line.
- Launcher name: your session name, on the first line of `ListAgents`.

When the state store has the GitHub App values, `dispatch.sh` gives each new session the App identity (`sofa-github settings`): each `gh` and each `git` of the session acts as `<slug>[bot]`. Only a fresh start with `dispatch.sh` gives a session these settings: a `--resume` copy does not keep the settings of its first start. So after the App setup (`sofa:setup`, step 5.5), stop the team and start it again.

Read `<skill folder>/references/planning.md` and section 1 of `docs/adlc.md`. An absent backend row or explicit `product` means legacy Product; `plan` uses the profile of the `Plan workspace` row, relative to the main checkout. Do not import, change the backend, or create a store at a start, because a conversion needs the approval of the user. A Product writer in a repository role override needs correction before Plan work.

If the `CLAUDE.md` of the repository names a different process or harness for product work, ask the user which one wins before step 2.

## Step 2 — Make `docs/adlc.md` meet the current template

The result: `docs/adlc.md` and `docs/adlc/roles/` on `main` meet the current `templates/ADLC.md` and role files, and hold the values of this repository.

- If `docs/adlc.md` does not exist: tell the user to run `/sofa:setup`, which asks the setup questions and writes it. Stop.
- If its `sofa-template-version` is lower than the template: update it with `templates/MIGRATION.md`. This preserves the selected backend; version 12 → 13 makes an absent backend explicitly `product`, not `plan`. The file already holds the setup answers; ask only for values marked `ask`. Tell the user what changes, and continue only after agreement, because the file is on `main` and each session reads it. Land it on `main` with a worktree, a PR and a squash merge. If live sessions of an older team exist (`ListAgents`), stop them before step 3. Do not run a Plan import or activation as part of this template update, because a template update preserves the selected backend.
- If it meets the template: go to step 3.

## Step 3 — Start the orchestrator

1. Pull `main` in the main folder. Read `docs/adlc.md`. Make sure `.git/info/exclude` has the line `.sofa/`. Run `<skill folder>/scripts/sofa-state init` from the main folder.
2. If `ListAgents` shows a live session with the orchestrator name, tell the user that the team runs, and how to open it (item 5). Stop, because a second orchestrator starts a second team.
3. Write this start prompt to a temporary file, with the machine values of step 1, and start the orchestrator from the main folder with `<skill folder>/scripts/dispatch.sh --adlc docs/adlc.md --role orchestrator --prompt-file <file>`:

   ```
   You are the orchestrator of the <prefix> team. Load the skill sofa:station.
   Then read docs/adlc.md on main, and your role files: <skill folder>/references/roles/orchestrator.md,
   and docs/adlc/roles/orchestrator.md if it exists. Where they differ, the repository file wins.
   Do the role "orchestrator" as written there. Start with "At start".
   Machine values: main folder <main folder>, skill folder <skill folder>, GitHub account <gh account>.
   The launcher is <launcher name>. Send it a DONE message when all always sessions of the team are ready.
   ```

4. Wait for the `DONE` message from the orchestrator. It names the live sessions: the orchestrator, each `always` role, and monitoring when section 1 `Environments` names logs or metrics. The other roles are `on demand`: the orchestrator starts each one at its first trigger.
5. Tell the user which sessions run (the names from the `DONE`), and how to work with the team:
   - `claude agents --cwd <main folder>` shows the sessions of this repository in their role colours. Open the orchestrator, hitl or requests from there, or with `claude attach <name>`.
   - `/sofa:status` opens the dashboard; `/sofa:floor` publishes the floor artifact or opens its live page; `/sofa:request <text>` gives the team new work.
   - The readiness items that are still missing, and `/sofa:setup` to fix them.

   Then this session has no more work.
