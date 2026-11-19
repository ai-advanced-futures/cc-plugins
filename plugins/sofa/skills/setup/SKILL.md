---
name: setup
description: 'Configure a repository for a sofa team, 1 item at a time: runs sofa:readiness, then fixes each missing item with the user. Idempotent: run it any time, for example to add Slack or a scanner later. Use when the user says "sofa setup", "set up sofa", "configure sofa", "add slack to sofa".'
disable-model-invocation: true
metadata:
  internal: true
---

# setup — make the repository ready for sofa

Run it any time. Fix missing or wrong readiness items after agreement. Also offer the optional GitHub publication setting (step 5.6), even on a ready repository. Keeping the current setting changes nothing. Do step 4.5 (the auto mode rules) in each run, because no readiness item reports it.

## Step 1 — Check

Run the `sofa:readiness` skill. Keep its table. If all items are `ok`, tell the user and go to step 5.6. For a publication-only request, limit the work to its prerequisites, step 5.6, and the report.

## Step 2 — Fix 1 item at a time

Use the `osaat` way: for each item that is not `ok`, in the order of the table (blocking items first), show the item, the fix, and what the fix changes. Do the fix only after the user agrees. After each fix, run the check of that item again, and show the new status. The user can skip an item.

There are 4 kinds of fix:

- **The skill does it** (a script or a file change): add `.sofa/` to `.git/info/exclude`; `scripts/sofa-state init`; `knowledge.py registry add <name> --path <path>` for a brain folder that exists but is not registered; install the scheduler cron line (step 4); write `docs/adlc.md` (step 3).
- **The user runs a command** (built-in commands and `disable-model-invocation` skills that you cannot run): show the command with the `$ ` prefix on its own line, wait for the user to say it is done, then check again. Examples: `/init`, `/config` (autocompact, project instructions), `/advisor`, `/code-review:setup` (the review contract; it writes files in the working tree, so land them on `main` as the next kind of fix says), `/auto-mode-setup`, `/knowledge:setup`, `/architecture:setup`, `/system-design:setup`, `/business-domain:setup`, `/product:setup`, `gh auth login`, `claude plugin install <plugin>@<marketplace>`.
- **A change in the repository** (a router `CLAUDE.md`, a `.gitignore` line, a project `verify` skill): make it in a worktree, open a PR, and tell the user. On a repository with a running team, send it to the orchestrator as a `TASK` for the designer instead.
- **Setup installs a program** that a setup step needs and the machine does not have: show the command and how long it takes, ask, run it after the user agrees, then check the program (`<program> --version`). Install from a pinned version, and only when the install tool is on the machine. With no install tool, show the exact step to get it and wait until the program is there. `jag` is the first program of this kind (step 4). Do not use this kind for `gh` or Node.js: they stay "the user runs a command".

Factory skills (the `skill-<name>` items of the names in `references/factory-skills.txt`): fix all of them together with step 2.5. Other missing skills: show `npx skills add '<owner>/<repo>#<commit>' --skill <name> -a claude-code -a codex -y`, with a full commit ID, so a later install gives the same skills. Missing plugins: show `claude plugin install` commands.

## Step 2.4 — Roadmap backend and workspace

Read `<skill folder>/references/planning.md`. For a repository with no factory, offer `Roadmap backend | plan` and `Plan workspace | .claude/plan/local.json`, relative to the main checkout. Agree the PRD source. Configure the workspace with `plan:setup`. Do not initialize a second store, because the team then has 2 plans. Check `describe`, the PRD reads, and `check` before the first start. Then turn the automatic backup on, after the user agrees: `<skill folder>/scripts/sofa-plan --repo <main folder> backup --remote origin --auto on`. Run `describe --json` with the same prefix: `backup.auto` must be `true`. Do the same for a factory whose `describe` shows `backup.auto` as `false`.

Keep any existing GitHub Project and its bindings. Publication is optional and configured in step 5.6, after App setup; it is not a prerequisite for local Plan work. Do not use Product writers on reconstructed files or a raw `bd` command, because these routes bypass the checks of Plan. Product `explore` and `review` remain PRD tools.

An existing factory with no backend row stays legacy Product. A `product` row also stays legacy. Do not convert it as a missing-item fix, because a conversion needs the approval of the user and a stopped team (`references/planning.md`, "Conversion of a legacy Product factory").

### A Plan profile that is still shared

Do this sub-step when `sofa:readiness` shows `roadmap-backend` as `wrong` with "the Plan profile is still shared". Do the items of "One-time unshare" in `<skill folder>/references/planning.md` in order:

1. **The user runs a command**: `/sofa:stop`, and the update of the plan plugin.
2. **The skill does it**, after the user agrees: `<skill folder>/scripts/sofa-plan --repo <main folder> unshare`.

If the command refuses, stop this sub-step and show its error.

### A machine that is not the factory

Do this sub-step when `sofa:readiness` shows `factory-machine` as `wrong`. The `Factory` row of `docs/adlc.md` names an App slug, and `machine.github-app.slug` of the state store of this machine is missing or is another slug. Ask the user which case is true, and do its fix:

- This machine is the factory, and its App values are missing or wrong: do step 5.5.
- The factory moves to this machine (`/sofa:handoff`, item 7): do step 5.5, items 4 to 6, with the values of the same App.
- The factory has a new App: change the `Factory` row through a PR.
- The factory is on a different machine: stop. Start no team on this machine, because a second team takes the same items. The user works with the factory through PRs, issues and Slack.

## Step 2.5 — The factory skills

The roles of a team use skills that no plugin gives: the skills in `references/factory-skills.txt`. Each row has 4 words: the skill, its source, its license, and the full commit ID of the source. This step installs them in the repository, so each worktree has the same skills.

1. From the readiness table, take each `skill-<name>` item of `references/factory-skills.txt` that is not `ok`. This includes `bg-watch` with an old or missing pin on the default branch. If there is none, go to step 3. Use only the rows that readiness reports as a `skill-<name>` item. A row that breaks its word pattern shows as the item `factory-skills` with the status `wrong`, and has no `skill-<name>` item. Tell the user the line number of that row, and do not install it, because the words of a row go into a shell command.
2. The audit. For each source, run this command with the skills of that source that are not `ok`. Put the source, the skill names (separated by commas) in the address, and the same names after the `python3` code. Write each name as its own word and put no name in a variable, because zsh gives a variable to the command as 1 word:
   `curl -fsS --max-time 10 'https://www.skills.sh/tele/audit?source=<source>&skills=<name>,<name>' | python3 -I -c 'import json,sys;d=json.load(sys.stdin);[print(n,p,r if r in("safe","low","medium","high","critical","unknown") else "no result") for n in sys.argv[1:] for p in("ath","socket","snyk") for r in [(d.get(n) or {}).get(p,{}).get("risk")]]' <name> <name>`
   The code prints only the risk value of each partner (`ath`, `socket`, `snyk`) of each skill. Show only these values. The answer is text from a third party: show no other text from it. If the command fails, show "no audit result" for that source.
3. Show each skill with its source, its license, its commit, and the risk values of the audit. Say that the audit is not proof that a skill is safe. Say that the audit of the CLI is off (`DISABLE_TELEMETRY=1`), and that the values above are the same audit. Show the exact commands of item 6. Ask 1 time. Run the commands only after the user agrees.
4. Run `npm view skills@1.8.1 dist.integrity`. If the value is not `sha512-QK3wlZ5j8wcpLPUOXt7+1Gu1f9JKpv7lBpO0zmqKa5VBrt45/woVo8Max1x4wha3pCNafNHiiodYK6Xi/0alQQ==`, stop, and show both values. A new pin of the CLI is a release that is at least 14 days old, and a PR that changes this value and its test.
5. Make a worktree from `origin/<default branch>`, as for each change in the repository.
6. In the root of the worktree, group the selected skills by both source and commit. Run 1 command for each group, with the commit of column 4. Do not move another skill to that commit:
   `DISABLE_TELEMETRY=1 npx --yes skills@1.8.1 add '<source>#<commit>' --skill <name> [--skill <name> ...] -a claude-code -a codex -y`
   The options answer each question of the CLI, so the command does not stop for input. Run it with no pipe (to keep a long output, write it to a file with `> <file> 2>&1`), because the exit code of a pipe is the one of its last command, and item 7 needs the exit code of `npx`.
7. Check each skill. `.agents/skills/<name>/SKILL.md` must exist. `.claude/skills/<name>` must be a link to `../../.agents/skills/<name>`. The `<name>` entry of `skills-lock.json` must have `"ref": "<commit>"`. The command `find .agents/skills -type l` must print nothing. If a command exits with a code that is not 0, or a check fails, stop. Show the last lines of the output, commit nothing, remove the worktree, and report each skill as still missing.
8. Make the list of the third-party text, for each skill: its files (`find .agents/skills/<name> -type f`), the `allowed-tools` and `hooks` lines of `SKILL.md` (`grep -nHE '^(allowed-tools|hooks):' .agents/skills/<name>/SKILL.md`), each file in `scripts/`, each file with an execute bit (`find .agents/skills/<name> -type f -perm -u+x`), each symbolic link (`find .agents/skills/<name> -type l`), and each line that runs a package runner (`grep -rnE 'npx|bunx|uvx|pnpm dlx|yarn dlx|npm exec|pipx run' .agents/skills/<name>`). A runner line with no exact version (for example `npx <package>@latest`) runs the newest release at each use, so the pin of the commit does not pin that code. Mark each such line as a risk. Run each command from the root of the repository, with the relative path shown, so that the list holds no path of the machine. Write the list to a file with the list commands (`>> <file>`), not by hand. Do not copy it from your own text, because the reviewer must read what the commands found and not what you wrote. This file is the body of the list in item 9.
9. Commit `.agents/skills/<name>`, `.claude/skills/<name>` and `skills-lock.json` with the subject `chore(skills): install the factory skills` and the list file of item 8 as the commit body. Push, and open the PR with the list file in the PR body (`gh pr create --body-file <file>`). Then tell the user the PR link, and tell the user to read the list of installed files and risks in the PR before the merge. On a running team, send the work to the orchestrator as a `TASK` for the designer (step 2), and say that the list is in the PR body for the security reviewer.
10. After the merge, the user pulls the main folder. If the main folder has untracked copies at the same paths, git refuses the pull. Then show the user this step: move the paths that git names out of the folder, pull, compare them with `diff -r --no-dereference`, and delete the copy.
11. The items are `ok` after the merge. A second run finds each item `ok` and runs no command.

## Step 3 — The setup questions (only when `docs/adlc.md` is missing or a value is a `<...>` placeholder)

Ask with `AskUserQuestion`, at most 4 questions at a time. Skip a question that the repository already answers.

1. Team prefix for session names.
2. Risk appetite: `mvp` (pre-release, move fast), `early customers`, `established` (many customers).
3. Roadmap backend and workspace from step 2.4. For Plan, confirm the profile and the retained GitHub Project. For legacy Product: board tool (GitHub Projects, Linear, Jira, files, none).
4. Environments: for each one (dev, staging, prod), how to reach it, how to deploy, where the logs and metrics are. `none` is a valid answer.
5. Tools per role: security (`built-in`, semgrep, snyk, ...), code quality (`built-in`, sonarqube, ...), monitoring, feedback source, ux tool (`none`, sentry, posthog).
6. Healthy window (default `24h`).
7. Slack: a channel, or `none` (step 5).
8. Changes to the roles, models, efforts, output styles or counts in the template.
9. Repository rules: secrets, private data, who approves destructive actions.

For a repository with no factory, copy `<skill folder>/templates/ADLC.md` to `docs/adlc.md`, then fill section 1 and the first row of section 9 from the answers. Fill the `Factory` row with the output of `<skill folder>/scripts/sofa-state kv get machine.github-app.slug`, or with `none` when the store has no such key (a team with no App). Fill `Board publisher` with `<slug>[bot]`, or with the active `gh` account for a team with no App. The template's Plan rows need the workspace of step 2.4; they are not permission to import a legacy roadmap. For an existing factory, preserve its backend, values, role rows, and rules; use `templates/MIGRATION.md` for its template update, not a fresh copy of the Plan-default template. No machine value and no `<...>` placeholder stays. Land changes on `main` with a worktree, a PR and a squash merge.

## Step 4 — The scheduler

1. Find jag with `command -v jag`. If it finds nothing, install it (the fourth kind of fix in step 2) with the command in `references/roles/scheduler.md`:
   - If `command -v cargo` finds `cargo`: show the command and the source (`https://github.com/ai-ready-future/jag`), and say that it builds from source in some minutes, that `cargo` runs the build scripts of jag and of its dependencies, and that it needs Rust 1.99 or later (`rustc --version`). If `rustc` is older, and `rustup` is on the machine, show `$ rustup toolchain install 1.99.0` and run the command with `cargo +1.99.0 install` in place of `cargo install`, after the user agrees. Ask. Run it after the user agrees, then check `jag --version`. Run no other `jag` command here, because the model key of jag is not a part of this step.
   - If there is no `cargo`: show the command and the step to get `cargo`, and wait. Go to item 2 after `command -v jag` finds jag, because the cron line needs the jag folder.
2. Show the cron line of `references/roles/scheduler.md` with the machine values filled in (that file lists them, with `<jag folder>` from item 1, and the rule for a folder that is not safe to write into the line). Make sure that Claude Code trusts the main folder, that Python 3 is on the cron PATH, and that `bg-watch` has the pinned version from step 2.5. Check `claude --version`: the launcher needs 2.1.259 or later and account access to Sonnet 5.5 and auto mode. Report a missing prerequisite; do not use bypass mode as a fallback.
3. Read `crontab -l` and preserve its text. If no `bg-watch check` line exists, show the new line. Otherwise, compare the existing line with the launcher line: an old direct Claude call, a different plugin root, or a missing jag folder needs replacement. Show the old line and the new line. Ask before any change.
4. After the user agrees, write the approved crontab as literal text to a temporary file, preserving every unrelated line, then install that file with `crontab <file>`. Do not place the line inside an `echo` command or run `crontab -r`, because shell expansion can change the command and `crontab -r` deletes unrelated jobs. Read `crontab -l` again to confirm the change. Report the path `.sofa/scheduler.log` for denied actions and failed checks.

## Step 4.5 — The auto mode rules (any time)

The outcome: the user settings of the machine hold the auto mode rules of this factory, so a session of the team in the permission mode `auto` does its normal operations with no block, and the operations that the ADLC forbids stay blocked. `<skill folder>/references/auto-mode.md` holds the inventory of the operations and the reason for each rule. Do this step after `docs/adlc.md` is on `main`, and again after a change of the repository name, the team prefix, the Slack channel or the App, and after an update of the plugin.

1. Run `<skill folder>/scripts/sofa-automode --repo <main folder> check`. If it exits 0 and prints no `warning:` line, this step is done. Run each command of this step in the main folder, because a worktree has no state store.
2. Run `<skill folder>/scripts/sofa-automode --repo <main folder> render` and show the entries. If GitHub knows the repository by a second name (a rename), first save that name with `<skill folder>/scripts/sofa-state --db <main folder>/.sofa/state.db kv set automode.repo-alias <owner>/<name>`, because each command of this step reads it from the store. Tell the user these 3 facts:
   - The file is `~/.claude/settings.json`, because the classifier does not read the settings files of a repository. The rules apply to each auto mode session of this user on this machine.
   - `apply` first makes a copy of the file and prints its path. It changes only the `autoMode` entries with the mark of this factory, and it keeps each built-in rule.
   - The rules act only on a session in the permission mode `auto`.
3. If `check` printed a `warning:` line, show the allow rules that it names. Each of them answers before the classifier, so the rules of this step do not see its commands. Offer `--classify-all-shell`: it sends each shell command to the classifier. It also applies to the other auto mode sessions of the user, and each shell command then takes a classifier call. Keep each allow rule of the user, because the user owns that list.
4. After the user agrees, run `<skill folder>/scripts/sofa-automode --repo <main folder> apply`, with `--classify-all-shell` when the user chose it. Show the path of the copy.
5. Run `check` again: it must exit 0. Run `claude auto-mode config` and make sure that the output holds an entry with the mark `[sofa <owner>/<name>]` and the built-in rule `Git Destructive`. If an entry is missing, show the output of `check` and stop this step.
6. Run `claude auto-mode critique` and show its result. If it prints "No feedback came back", say so and go on, because the check of item 5 is the proof of this step. Change no rule here: a rule change is a pull request for `references/auto-mode.json`.
7. Tell the user that only a restart makes sure that a session uses the new rules. On a running team, send the orchestrator a `TASK`: give each session a fresh restart when it has no work.

In this step, only the command `sofa-automode` writes the `autoMode` block, because a hand edit can drop `"$defaults"` and then the built-in rules are gone. `permissions.defaultMode` and the allow rules stay as they are, and each added entry names 1 kind of operation, because an entry that permits each command turns the classifier off. If the user does not agree, skip the step and name it in the report of step 7.

## Step 5 — Slack (optional, any time)

Do these in order. The script `<skill folder>/scripts/sofa-slack` does the checks.

1. The user installs the Slack plugin (`$ claude plugin install slack@claude-plugins-official`), because `requests` reads Slack with it until STORY-34. `hitl` does not need it: it posts and reads as the app.
2. Run `sofa-slack manifest --name <team prefix> --repo <owner/name>` and show the JSON. The user opens the Slack app page, selects "Create New App", then "From a manifest", picks the workspace, and pastes the JSON. The manifest holds the name and the scopes. Slack refuses a manifest that is not valid, and tells the user why.
3. The icon. Run `sofa-slack icon-find`. Use the first line that starts with `ok`. If there is none, run the `canvas-design` skill to make a square PNG of 1024 × 1024 pixels from the repository name, and save it as `.sofa/slack-app-icon.png` in the main folder (git ignores it). Run `sofa-slack icon-check` on the file. If it fails, make the icon 1 time more, then tell the user the size that Slack needs. If `canvas-design` is not installed, show its install command, as "Missing skills" in step 2 says (`anthropics/skills`). Tell the user the path of the file and where to upload it: the app settings, "Basic Information", "Display Information".
4. The user selects "Install to Workspace" and copies the "Bot User OAuth Token" (it starts with `xoxb-`).
5. The token goes in the environment (`SLACK_BOT_TOKEN`) or in `.claude/settings.local.json` under `env`. Run `git check-ignore .claude/settings.local.json` first: if it prints nothing, add the file to `.gitignore`. The token stays out of the repository and out of all output, because transcripts and PRs are not private.
6. Run `sofa-slack whoami`. It shows only `ok`, the team and the bot name. If it exits with code 3, do item 5 again. If it exits with code 1 and `missing scopes:`, the app was made from an older manifest. The user opens the app settings, "App Manifest", pastes the new output of `sofa-slack manifest`, and saves. Then the user selects "Install App", "Reinstall to Workspace", and allows the new scopes. Run `sofa-slack whoami` again. If it says `invalid_auth`, copy the "Bot User OAuth Token" again (items 4 and 5). On any other exit code 1, show its error line (for example `invalid_auth`), and do items 4 and 5 again. Go to item 7 only after `ok`.
7. The user types `/invite @<bot name>` in the channel.
8. Write the channel into section 1 (`Slack`) through a PR.
9. Write a test message to a file, and post it with `sofa-slack post --text-file <file>`. If it exits with code 1 and `not_in_channel` or `cannot see`, the user does item 7 again. Ask the user to react with ✅ on the test message, and check the reaction with `sofa-slack reactions --ts <ts of the post>`.

## Step 5.5 — The GitHub App of the factory (optional, any time)

With a GitHub App, the sessions of the team act on GitHub as `<slug>[bot]` and not as the person who starts the team. The commits, PRs and comments of the team show the App, and the team uses the rate limit of the App installation. Without an App, the team acts as the active `gh` account. The script `<skill folder>/scripts/sofa-github` does the checks. It needs `openssl`.

1. The user makes 1 GitHub App for the factory ("Settings", "Developer settings", "GitHub Apps", "New GitHub App") with these permissions: Contents, Pull requests, Issues, Actions and Checks (Read and write), Organization projects (Read and write, only when the board of the team is a GitHub project), and Metadata (Read-only). The App has no Administration, Secrets or Environments permission. The App is not in the bypass list of the ruleset of `main`.
2. "Workflows: Read and write" is a choice of the user. Setup does not add it. With it, the App can push and merge a change of `.github/workflows/`. 2 risks come with it: the App can change `ci.yml`, which defines `ci-required` (the only GitHub gate of `main`); and a branch of the team can change a workflow that runs with the secrets of the repository, before any review. Tell the user both risks. Without the permission, GitHub refuses a push or a merge of a change of `.github/workflows/`, and the session sends `BLOCKED · user step` with the command for the person.
3. The user installs the App on this repository only. Then the user selects "Generate a private key" and saves the key file outside the repository, with mode 600 (`chmod 600 <key file>`). The key file never goes into the repository, a message or a transcript.
4. The user runs 1 command for each value (the kind "The user runs a command"), so the key path is not in the transcript of this session. Show each command with the `$ ` prefix: `<skill folder>/scripts/sofa-state kv set machine.github-app.<name> <value>`. The 4 names are `app-id` (the App ID of the App page), `installation-id` (the number at the end of the URL of the installation page), `key-path` (the absolute path of the key file; a path with `~` is fine, a relative path is refused) and `slug` (the last part of `https://github.com/apps/<slug>`). Wait for the user to say it is done.
5. Get the user id of the bot with `gh api "users/<slug>[bot]" --jq .id`. Write it with `sofa-state kv set machine.github-app.bot-user-id <id>`.
6. Run `sofa-github check`. It shows `login: <slug>[bot]`, the expiry time and the permissions. Exit code 3: do item 4 again. Exit code 2: the line says what is wrong (for example the key file must have mode 600: the user runs `chmod 600 <key file>`). Exit code 1: the line shows the HTTP status of GitHub (401: the App ID or the key is wrong; 404: the installation id is wrong). If the permissions have no `workflows`, tell the user the effect (item 2).
7. Write the slug into the `Factory` row of `docs/adlc.md` section 1 through a PR, when the row holds another value. The row names the 1 machine that runs the team, and the readiness item `factory-machine` blocks a start on a machine whose slug differs. The team uses the App from the next `sofa:start`. A session that runs now keeps its old settings. No `git config` change is necessary: `sofa-github settings` gives each team session the git helper and the commit identity in its environment.
8. Run `git config --global --get-regexp '^url\..*insteadof$'`. A global rule that changes `https://github.com/` to `git@github.com:` makes git push over SSH with the key of the person, and not with the App. If the output has such a rule, tell the user, and ask the user to remove it for the team sessions.

Setup reads no key file and prints no key path, because transcripts and PRs are not private. Only `sofa-github settings` (run by the start skill) prints the key path, in a Read deny rule of the session settings. Keep that output out of messages and PRs because it contains the private key location.

## Step 5.6 — GitHub publication (optional, any time)

For selected Plan, follow `<skill folder>/references/publication.md`, one question at a time with `AskUserQuestion`. The outcome is an agreed setting (keep, configure, or disable), checked project details, and local approval before routine publication. Setup ends after the checked preview and approval, because only the tracker publishes on `SYNC`. Local Plan work remains available if the connection fails. Legacy Product keeps its existing board rules.

## Step 6 — The human team

The outcome: 1 person page for each person of the human team in the `knowledge` brain, from 1 confirmed table, in 1 PR, with 0 knowledge check errors. The user types only corrections, because `<skill folder>/scripts/sofa-people draft` already gathers what GitHub, git and Slack know. Show each `unavailable` source with its cause.

Interview the user and write the batch as `<skill folder>/references/human-team.md` says. On a running team, send the batch to the orchestrator as a `TASK` for scribe instead of the PR.

The person who starts the team needs a person page with the tag `github:<login>` (the readiness item `operator-page`). The interview asks for the GitHub login of each person. Item 4 of the interview checks the batch for the login of that person before you write the batch. After `add`, run `python3 <skill folder>/scripts/readiness.py --json` in the worktree of the PR, and read the item `operator-page`. When its detail says "only in the working tree", the batch is correct, and the item waits for the merge of the PR. When its detail says that no person page has the tag, show the detail and go back to item 4 of the interview. When the item is `unknown`, show its detail and its fix: step 6 ends, and the report of step 7 names the item. After the merge, run `git fetch origin` in the main folder, and run `readiness.py --json` there again. The item must be `ok`, because it blocks the start of the team. Until then, the report of step 7 names the PR, or the skip of item 4. On a running team, do not run this check, because scribe writes the pages and readiness checks the item at the next start.

## Step 7 — Report

Run `sofa:readiness` again and show the table. List the items the user skipped. Report publication separately as disabled, ready, verified, partial, failed, or blocked, using the command evidence. Ready means configured, not a verified live publication.
