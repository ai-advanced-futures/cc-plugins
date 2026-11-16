---
name: readiness
description: 'Check if a repository is ready for a sofa team, and print what must be configured. It changes no file that git tracks. Use when the user says "sofa readiness", "is this repo ready for sofa", "what does sofa need", or before /sofa:setup and /sofa:start.'
allowed-tools: Bash(python3 *) Bash(${CLAUDE_SKILL_DIR}/../../scripts/readiness.py *)
metadata:
  internal: true
---

# readiness — what sofa needs in this repository

Change no file that git tracks. The 1 write is the token cache of the `github-app` item (`.sofa/github-app-token.json`, which git ignores).

1. Run the check script from the main folder of the repository:

   ```
   python3 ${CLAUDE_SKILL_DIR}/../../scripts/readiness.py --json
   ```

   It prints 1 JSON object per item: `id`, `area`, `status` (`ok`, `missing`, `wrong`, `unknown`), `blocks_start` (true or false), `detail`, and `fix` (the exact command, or the skill that fixes it).

2. Check the items that a script cannot judge, and add them to the table:
   - `claude-md-current`: read the root `CLAUDE.md` (or `AGENTS.md`). Is the build, test and run information in it still true for the repository? `wrong` if a command in it fails or names a file that does not exist.
   - `prompts-fit`: are the repository prompts (`CLAUDE.md` files, `.claude/skills`, `.claude/agents`, `.claude/rules`) short and specific? Only note it; `sofa:maturity` scores it.

3. Show the result as a table, grouped by area, `missing` and `wrong` first:

   | Area | Item | Status | Fix |
   |---|---|---|---|

   Under the table, list the items that block the start of the team. End with: run `/sofa:setup` to fix the items 1 at a time.

## The items

The script checks these items. `scripts/readiness.py` defines the checks; this list is for the reader.

- **Claude Code:** `--bg` and `--autocompact` exist; `autoCompactEnabled` is not `false`; a permission mode for unattended work is set (`/auto-mode-setup` or `bypassPermissions`); the advisor is on; the `outputStyle` names of the roles table exist.
- **Repository files:** root `CLAUDE.md` or `AGENTS.md`; a `CLAUDE.md` router in each code folder (under 30 lines); `.claude/rules/` used for scoped rules (note only); `.gitignore` has `.sofa/`, `.env`, `node_modules`-style entries for the stack; `.git/info/exclude` has `.sofa/`; project `verify` and `simplify` skills, or `CLAUDE.md` names how to verify; `review-contract`: the default branch on `origin` has `.claude/code-review/contract.md` or `.claude/pr-flow/contract.md` (`wrong` when the file is only in the working tree, `missing` when there is none; the fix is `/code-review:setup`; it does not block the start).
- **Brains and roadmap:** `.claude/knowledge.json` lists the applicable brains (`knowledge`, `adr`, `system-design`, `ddd`, `prd`); the PRD exists (blocks start); ADR folder; domain model. Read `references/planning.md`. With backend absent or `product`, the legacy `roadmap` brain and bundle must exist. With backend `plan`, the profile from `Plan workspace` resolves relative to the main checkout, and the installed Plan, the PRD source, `describe`, `check` and `list` must pass. No Product roadmap bundle is required. `roadmap-backend` is `wrong` with "the Plan profile is still shared" when the profile has a `sharing` block (the fix is `sofa-plan unshare`: `/sofa:setup`, step 2.4). An unknown backend, a missing profile, or a failed Plan command blocks the start. Readiness never imports or activates Plan.
- **Plugins and skills:** each plugin and skill that the roles table names is installed (`claude plugin list`, `~/.claude/skills`); the factory skills of `references/factory-skills.txt`: `ok` when the default branch on `origin` has `.claude/skills/<name>`, `wrong` when the skill is only in the working tree or only a personal skill, `missing` when there is no copy; the fix is `/sofa:setup` (step 2.5); it does not block the start; `factory-skills` is `wrong` when a row of the file breaks its pattern; `gh` logged in (blocks start); `github-app`: the state store has the GitHub App values of the team and `sofa-github check --no-cache` gets a token (`missing` with no App values, `wrong` when only some values are there or the token call fails; the fix is `/sofa:setup`, step 5.5; it does not block the start, because a team with no App acts as the person); `npx ctx7` runs; `jag` is on the PATH (`missing` when it is not; the fix is `/sofa:setup`, which installs it after you agree; it does not block the start, because `bg-watch` then uses its own stuck flag).
- **Tools per role:** each value of section 1 "Tools per role" is set, and its CLI is on the PATH (`semgrep`, `gitleaks`, linters).
- **Human loop:** Slack value set, and `SLACK_BOT_TOKEN` in the environment when it is not `none`; the `knowledge` brain has a person page (an `Entity` with `entity_kind: person`, or the older `people/` folder); `operator-page`: 1 person page on the default branch of `origin` has the tag `github:<login>`, where the login is the active account of `gh auth status`. It blocks the start, because the person who starts the team must have a person page. It is `missing` also when the page is only in the working tree, because each session reads the pages of `origin/main`. It is `unknown`, and it does not block, when there is no knowledge brain or `gh auth status` names no account of a person.
- **Team:** `docs/adlc.md` exists and has the current `sofa-template-version` (blocks start); `factory-machine`: `wrong` when the `Factory` row of section 1 names an App slug, and `machine.github-app.slug` of the state store of this machine is missing or is another slug (blocks start, because a repository has 1 factory; the fix is `/sofa:setup`, step 2.4); the scheduler cron line exists; `scheduler-path`: the `PATH` of that line has a folder with an executable `jag` (`wrong` when no folder has it; the fix is `/sofa:setup`; it does not block the start); the state store opens.
