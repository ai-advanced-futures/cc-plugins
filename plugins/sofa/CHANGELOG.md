# Changelog

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
