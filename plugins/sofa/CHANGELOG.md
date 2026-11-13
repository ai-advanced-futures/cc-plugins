# Changelog

## 9.1.1

STORY-504: station Rule 8 takes the new `main` with a merge, never with a rebase (FEATURE-54, D-7246, D-7247, D-7248, D-7258, D-7266, D-7271).

- `skills/station/SKILL.md`, Rule 8: after `RELOAD`, a session runs `git fetch origin main` and `git merge --no-edit origin/main` in the worktree of the branch of its item, and pushes a pushed branch with a plain `git push`. It never rebases a pushed branch and never force-pushes it. Before, the rule said "rebase your worktree on `main`", and a pushed branch then needed a forced push.
- A session with no worktree of its own, a detached worktree of a PR head that a session checks, a worktree of a branch that another role writes (a checkout of a PR for a review), and the worktree of an item whose PR is merged skip the merge. Before the merge, the session commits only the files of its item.
- A conflict that the session cannot solve, a merge that exits with no conflict, a failed fetch or `ls-remote`, and a refused push go to the orchestrator as `BLOCKED · team`. After a solved conflict or a commit of step 1 on a branch with an open PR, the session sends `REVIEW` again.
- `tests/template.test.sh`: a new case (25 checks) for the texts of Rule 8, and 2 scans of `skills/` and `references/roles/` that deny by default each text that tells a session to rebase, to `git pull` or to force-push. The private-data scan also reads `skills/station/SKILL.md`.

## 9.1.0

STORY-444: each line publishes its snapshot to a dedicated ref, and a reader gives all the lines (FEATURE-47, ADR-0012, ADR-0013, D-7187, D-7188, D-7192, D-7199).

- `sofa-state snapshot publish [--config PATH]`: pushes the scrubbed snapshot of this line to `refs/sofa-floor/<store id>` on `origin`, as 1 commit with no parent and the identity `sofa-state`. The push is the only forced push of the team: `--force-with-lease=<ref>:<explicit old id>` of the own ref (rule 24). A refused lease is read again and pushed 1 more time. A store with no App values, or a session with no App git setup, pushes nothing and exits 1.
- `sofa-state snapshot lines [--now TIME]`: prints the snapshot of each line on `origin` as JSON, with `age_seconds`, `old` and `own`. It needs no App values. A snapshot of another machine that is bad gives 1 line with an `error`, and the other lines stay.
- New exit code 3: `snapshot publish` exits 3 when the guard refuses the snapshot (nothing is pushed), so the orchestrator can tell a refusal from an error. `snapshot take` keeps exit 1.
- The snapshot has the new key `line.label` (kv `line.label`, default `line-` and 6 hex digits of the store id) and the new rule field `rules.health.snapshot_max_age_seconds`. `schema_version` stays 1. `.claude/sofa-floor.json` sets the limit to 1800 seconds.
- `snapshot take` and `snapshot publish` read `decision.store` first and write it only when it is absent, and make 1 try for the store lock: another writer gives exit 1 and the line `the store is locked by another writer`, not a wait of up to 25 tries. Each other command keeps its tries.
- `references/roles/orchestrator.md`, "Snapshot publish": the status check runs `snapshot publish`; an exit 3 goes on the route of a user step as 1 user step (sent 1 time, kept in the kv `floor.publish.refused`), and any other error goes to the troubleshooter at most 1 time each hour.

## 9.0.0

STORY-359: the merger merges the checked head and keeps the worktree of the author (FEATURE-04, D-7140 to D-7146, D-7153 to D-7156, D-7159, D-7160, D-7166).

- `references/roles/merger.md`, step 4: the merger merges with `gh pr merge <n> --squash --match-head-commit <commit>`, where `<commit>` is the head that step 1 read by REST before its gates. It no longer adds `--delete-branch`, so the worktree and the local branch of the author stay for its `wrapup`. When GitHub refuses the merge, the merger reads the head again, and starts again at step 1 when the head changed. A refusal for a branch that is not up to date goes to the author; a rate limit goes to the orchestrator.
- Step 3 is new: the merger removes its own check worktree and deletes no branch or worktree of the author. GitHub deletes the remote head branch when the repository setting "Automatically delete head branches" is on.
- New stop. Step 2 no longer rebases or pushes to the branch of the author. It fetches `main` and the PR head, finds a PR that is behind `main` with `git merge-base --is-ancestor`, and checks a local merge with `origin/main` that it does not push. A conflict that the `rebase` skill solved before now goes back to the author as `BLOCKED · team`, and so does a local merge that fails the `Build` command of section 1. To pass it, the author updates its branch with `origin/main` in its own worktree, pushes, and sends `REVIEW` again.
- `templates/ADLC.md`: the merger row has the Skills cell `station`, and the feature flow line says that the merger does not rebase. The template version does not change; the next template step carries the change to a team file.
- `tests/template.test.sh`: a new case (29 checks) for the merge command, the head pin, step 2, step 3, `--admin` and the 2 template lines.

## 8.0.0

STORY-474 and STORY-475: template version 12. Each restart of a session is a fresh start with the store name of the session, never `dispatch.sh --resume`. A resume with an option makes a copy. A copy can run in another permission mode, and a resume gives the session no App env.

`/sofa:start` on a repository with template 11 migrates `docs/adlc.md` to template 12 first (`templates/MIGRATION.md`, step 11 → 12). It starts the team only after you agree and the migration PR merges. The step changes only the restart texts of the file and the row of `RESUME`.

After the update to this version, start the team again 1 time (`/sofa:stop`, then `/sofa:start`). Why: the orchestrator that gets the reload of this update still has the old text. Do it only when hitl, requests and monitoring hold no open work, because a new start of the team loses that work. To check it, look at `/sofa:status`: it shows no open `ASK`. Then open the requests session and the monitoring session with `claude attach <name>` (`claude agents` shows the names). They must have no open request and no feature under watch. Until then, the orchestrator keeps the text of the version before.

- `references/roles/orchestrator.md`: the new subsection "A fresh restart" of "Stopped sessions". It says that the message `RESUME` and `/sofa:resume` are not `--resume`. The reload, the colour restart, "Use the sessions again", "Timer roles" step 3 and "Stopped sessions" step 3 use it. It does not restart a busy session or its own session. It does not restart a live session of hitl, requests or monitoring for the reload, the colour or a change of section 3, and such a session gets `RELOAD`, with the new skill folder when `sofa` changed. The first message of a session with an open item is a `RESUME` with the item, its branch, its PR and its worktree. A free session gets the first message of a first start of its role. A fresh restart clears the colour of the store row. The old step 4 (the id of a copy) is gone. "Status check" restarts a stopped session only in 5 cases, and restarts the free live sessions of `reload.pending`.
- `references/roles/updater.md`: "The reload" is the same fresh restart. The reload `TASK` is the last step of a run, and it gives the new plugin root.
- `references/roles/plan-auditor.md`: the time of the last audit is in `plan-auditor.last`.
- `references/roles/scheduler.md` and `commands/resume.md`: the same fresh restart.
- `commands/pause.md`: `--now` also keeps monitoring live, and sends it `PAUSE` with no `now`.
- `commands/stop.md`: the reason for no `claude rm` does not name `--resume`.
- `skills/start/SKILL.md`: only a fresh start gives a session the App settings.
- `templates/ADLC.md`: section 3 (`Tier:`) and section 8 give a stopped session a fresh restart. The row of `RESUME` in section 5 says that `RESUME` is not `--resume`. The dispatch line has no `[--resume <session id>]`. `dispatch.sh` keeps the option.
- `templates/MIGRATION.md`: the step 11 → 12, and a skip in the step 9 → 10.
- `tests/template.test.sh`: 138 new checks and 2 changed version checks, with a guard for a resume in a role file or a command file. `tests/integration/test_start_migration_live.py` accepts the step 11 → 12.

## 7.20.1

STORY-485: the place of a guard message of `snapshot take` holds only names of the script (FEATURE-47, D-7100 to D-7104).

- The place (`<where>` in `the snapshot holds <kind>; no snapshot written (in <where>)`) is a path of names of the new constant `WHERE_NAMES` (the keys that `build_snapshot` writes). Below a key that is not such a name, the place stops, so a section keyed by data of the store cannot print a key that is not a name of the script in stderr. A top-level key that is not such a name gives the place `the snapshot`.
- The snapshot, the text of the message, the exit codes and the refusals do not change. `schema_version` stays `1`.
- `tests/sofa-state.test.sh`: the new case `snapwhere` (17 checks), and the 3 place checks of the case `snapkeys` now expect `the snapshot`.

## 7.20.0

STORY-401: the dashboard names the instance and the bot of the state store (FEATURE-46, D-7028 to D-7031, D-7053, D-7054, D-7066).

- `sofa-state report` prints 1 header line first: `instance <instance> · bot <slug>[bot]`, then 1 empty line, then the sessions table as before. The pane of `/sofa-dashboard` and `/sofa:status` show it. No new column.
- `sofa-state report --json` has 2 new top-level keys, `instance` and `bot`, before the 5 keys of before. Each is a string, or `null`.
- The instance is the value of the key `machine.instance` (a GitHub login). The bot is `<slug>[bot]` from the key `machine.github-app.slug`. The report reads no other `machine.` key, so it never shows the key path of the App. A missing key, or a value that does not match its pattern, shows `?` in the text and `null` in the JSON.
- `/sofa:start`, step 3, writes `machine.instance` from the GitHub person: item 1 writes it when the key is missing (also when the team runs), item 3 writes over a value that is not the GitHub person before the orchestrator starts, and item 5 names the old and the new value. A live team (item 2) changes no value.
- To set the instance on a running team: run `/sofa:start` (item 1 writes a missing key), or run `<skill folder>/scripts/sofa-state kv set machine.instance <login>` from the main folder.
- The report names this store only. The claimed items of the other team are not in it (STORY-444 shares the snapshot of each line).
- `tests/sofa-state.test.sh`: the `owner*` cases and the 7-part JSON check. `tests/template.test.sh`: 7 checks of `/sofa:start`, step 3.

## 7.19.0

STORY-443: `sofa-state snapshot take` gives 1 versioned, scrubbed snapshot of a line (FEATURE-47, D-7032, D-7023 to D-7026).

- New command `sofa-state snapshot take [--config PATH] [--out PATH]`. It writes 1 JSON object (version 1) with the keys `schema_version`, `taken_at`, `line` (the store id), `rules`, `rules_digest`, `nulled`, and the 5 sections of `report`: `sessions`, `items`, `open_asks`, `queue`, `decisions_24h`. The text has sorted keys and no space, so the same state gives the same text. `--out` writes through a temporary file in the folder of the target and `os.replace`, so a reader sees all of the file or none.
- The scrub is a list of allowed fields (never a list of removed fields): a field that is not in the list goes nowhere. Each text value must match the form of its field, else it is `null` and `nulled` counts it. The snapshot never holds a session id, a branch, a worktree path, `waits_for`, `decided_by`, a decision summary, or a row of `messages`, `trips`, `interactions`, `usage`, `heartbeats` or `kv`.
- A guard runs on each key, string and number of the snapshot, and of the rule sets of the file (the full JSON text; a boolean and null have no text of a value), before any output. It looks (in any letter case) for each session id, each worktree, `HOME`, the main folder, the folder of the store, each person login of the form `human:<login>`, and each `machine.*` value. A session id that is its own name is no secret and is not searched, unless it has the form of a UUID. A hit exits 1 with `the snapshot holds <kind>; no snapshot written (in <where>)` (the section and the field, for example `items.id`, never the value), no output and no file. A value of fewer than 4 characters is not searched.
- The sections and the guard read the store in 1 read transaction, after the `INSERT OR IGNORE` of the store id commits, so 1 snapshot shows 1 state of the store.
- New file `.claude/sofa-floor.json` (the floor rules, in git): `schema_version` 1 and the 3 rule sets `health`, `streams` and `prices`, each `{}`. Only `snapshot take` reads it. The command exits 1 with 1 line when the file is missing, is over 262144 bytes, is not JSON, or has a wrong key. The rule sets are empty in version 1; a value of a rule set goes into `rules` only through a field with a form.
- Rule of change: a new key, section or field keeps `schema_version` 1. A removed or renamed key, or a changed type, adds 1. A reader ignores a key that it does not know, and a reader that gets a higher number shows `unknown schema <n>`.
- `tests/sofa-state.test.sh`: the `snap*` cases.

## 7.18.1

Test only, no change in a skill or a script (STORY-466). A live test of the migration of `docs/adlc.md` from template version 10 to 11, run by `/sofa:start`.

- `tests/integration/test_start_migration_live.py`, tier `start`: a fixture repository with a local bare `origin` and a template 10 `docs/adlc.md` (`tests/fixtures/adlc-v10.md`: no `GitHub person` bullet, a custom `GitHub account` text, no GitHub person in `Machine values:`). Turn 1 must tell about the migration and change nothing. Turn 2 (`yes`) must leave the migrated file on `origin`: version 11, the rules "Mention the operator" and "The App identity for git and gh" as rules 4 and 5, the bot sentence on the custom account text, the person bullet after it, the GitHub person in `Machine values:`, the fresh restart paragraph, 1 section 9 row, and no other line of the repository removed. A `gh` stub logs each call and answers `gh auth`, so no call reaches GitHub.
- `tests/integration/test_review_contract.py`: `Start` takes the text of `docs/adlc.md` (`adlc=`). Each `claude -p` turn runs in its own process group, and at the time limit the whole group stops (adlc rule 16). The turn does not inherit the team env of the session that runs the test (`SOFA_*`, `GIT_CONFIG_*`, `GIT_AUTHOR_*`, `GIT_COMMITTER_*`, `GH_CONFIG_DIR`, `GH_TOKEN`, `GITHUB_TOKEN`): a `/sofa:start` in the fixture read the real state store of the team before this change.

## 7.18.0

STORY-466: template version 11. A new team gets 3 rules that a team tried first.

- Section 2, rule "Mention the operator": each card, issue, PR comment and Slack message for a human mentions the operator, the person whose page has the tag `github:<GitHub person>` of the machine values. Also the owner of the decision when the operator does not own its area. With no GitHub person or no page, the session sends `BLOCKED · team` and posts no mention.
- Section 2, rule "The App identity for git and gh": with a team App account, no session injects the App identity for 1 command; 3 checks before each push (the credential helper trace, `GIT_AUTHOR_IDENT`, `GIT_COMMITTER_IDENT`); each `gh` write runs as `sofa-github gh`; a plain `gh` write needs the 2 checks of station step 3b. A failed check is `BLOCKED · team`, and the orchestrator starts the session again fresh.
- Section 8: a fresh restart, and the new session after a failed resume, keep the store name of the stopped session, and the fresh session writes its new id on that store row.
- `MIGRATION.md`, step 10 → 11. It keeps a rule or a paragraph that a repository already has, and it adds the GitHub person bullet, the App text of the GitHub account bullet and the GitHub person of the start prompt when they are missing.
- Section 9 names the template version of the marker.
- `tests/template.test.sh`: 1 case for each phrase, and 1 case that the template and `MIGRATION.md` hold no D-id, no Slack ID, no GitHub mention and no name of a person page.

## 7.17.2

Text fix and 1 new check, no change in `sofa-state` (STORY-350, D-5239). `decision block` with no `--reserve` and no `--check` makes no call to origin. With `--db` it makes no git call at all. With no `--db` and no `SOFA_STATE_DB`, the main folder comes from 1 or 2 local `git rev-parse` calls, so it is not true that it makes no git call. `scripts/CLAUDE.md` and the name of the check `blkcmd` now say so. The new check `blkcmd: block makes no git call` runs the command with `--db` and `GIT_TRACE`, and fails when the trace file holds a line, so a call to origin that ignores its result turns it red. The check that sets `origin` to a missing path keeps its assertion and is now named `blkcmd: block with a missing origin exits 0 and prints the same`, because it cannot see a call. Two more names now say what they measure: `blkcmd: --reserve on a block with a free id pushes no second tag` (it counts the tags on origin) and `blknet: a store with a free id gives ids with a missing origin`.

## 7.17.1

STORY-425: the git calls of `sofa-state` drop the repository env keys, and a refused push names its reason (issues 1845 and 1865).

- Each git call of a block reservation, and the check of the store folder, runs with no key of `REPO_ENV_KEYS` (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_CONFIG`, `GIT_NAMESPACE` and 10 more). A `GIT_DIR` of another repository no longer sends the block tag to the `origin` of that repository. The `GIT_CONFIG_*` entries of the session stay.
- Each git call has an empty `GIT_ASKPASS` with `GIT_TERMINAL_PROMPT=0`, so no askpass program runs. A reservation that needed one for a store with no App values now fails at once.
- A failed git step gives its reason: the first `! ` line of stderr, then the first `remote:` line, not `To <url>`.

## 7.17.0

STORY-390: `/sofa:setup` installs the factory skills at project level.

- New file `references/factory-skills.txt`: 6 skills (`wrapup`, `rebase`, `bg-watch`, `osaat`, `find-docs`, `systematic-debugging`). Each row has the skill, its source, its license, and the full commit ID of the source. A skill name and a source start with a letter or a digit, so the CLI never reads a word as an option or a path.
- New step 2.5 of `/sofa:setup`. It runs the audit of each source and shows only the risk value of each partner (not proof of safety), asks 1 time, compares the integrity value of `skills@1.8.1`, then runs `DISABLE_TELEMETRY=1 npx --yes skills@1.8.1 add '<source>#<commit>' ... -a claude-code -a codex -y` in a worktree. It checks the files and the lock, lists the third-party text (files, `allowed-tools`, `hooks`, `scripts/`, execute bits, symbolic links, package runner lines) into a file with the list commands, puts that file in the commit message and the PR body, and opens a PR. The last message gives the PR link and tells the user to read the list there before the merge (D-1199). A second run changes nothing.
- `/sofa:readiness` has 1 item for each factory skill (`skill-<name>`): `ok` when the default branch on `origin` has the skill, `wrong` when it is only in the working tree or only a personal skill, `missing` when there is no copy. It does not block the start. The item `factory-skills` is `wrong` when a row of the file breaks its pattern.
- `references/roles/scheduler.md`: `bg-watch` is a factory skill that setup installs at project level.
- New live test tier `skillslive` (`make itest TIER=skillslive`).

Pinned copy of `find-docs` (issue 1726, D-1190, D-1196): the upstream skill runs `npx ctx7@latest` for each lookup, and a pin of its commit does not pin that code. So `find-docs` now comes from our own copy `skills/find-docs/` in `ai-advanced-futures/cc-plugins`, at commit `b989b8f53e50df69a2d82273720ccf098987fadd`. The copy is the `upstash/context7` skill at `681554c5d3a688c67879d02d4f01d79ffd15df13` (MIT) with 3 changes: each run is `npx ctx7@0.8.2 <command>` (`dist.integrity` `sha512-PxgcHtW8nlHDozHmSPeV4lIcRyXCBZIiO34Rrxqfx8qrle+tIazJ8f9S5YsmEMtNDPh4uUBkKz8BPoX5kI3GdA==`), the optional global install is removed, and a note and a NOTICE file name the source. The 5 skills of `ai-advanced-futures/cc-plugins` use the same commit; the `computedHash` of `wrapup`, `rebase`, `bg-watch` and `osaat` did not change. Setup still lists each package runner line of a skill, in the commit message and the PR body, before the merge, and the security read of each new commit still looks for runs with no pin (D-1179).

A personal skill runs before a project skill of the same name. A user who has `~/.claude/skills/find-docs` must move it away to use the pinned copy: `mkdir -p ~/s390-find-docs-personal && mv ~/.claude/skills/find-docs ~/s390-find-docs-personal/`. Delete the personal copy only after you read `diff -r ~/s390-find-docs-personal/find-docs .agents/skills/find-docs`.

Not in this release: a lock for the dependencies of the CLI `skills` (issue 1715), and a run of the CLI from a file that `npm pack` fetched (optional item 3 of issue 1727).
