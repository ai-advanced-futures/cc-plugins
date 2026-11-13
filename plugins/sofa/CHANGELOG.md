# Changelog

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
