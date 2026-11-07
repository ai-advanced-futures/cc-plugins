# Changelog

## 1.0.6

### Changed
- The text lists files with `find` and searches with `grep` through Bash, because Claude Code gives no Glob or Grep tool there.

## 1.0.5

### Changed
- The tests and the docs name the job `business-domain` of the CI workflow `.github/workflows/ci.yml`. One workflow replaces the workflow file of this plugin. The plugin behavior does not change.

## 1.0.4

### Fixed
- The hook runs its steps only when a Bash command runs `ddd.py`. Before, any command that held the file name, even in a quoted text, started the steps. The hook now looks for the script in command position, and it removes each quoted span first. The hook also ignores a heredoc body and a `#` comment. The time of the check grows in line with the length of the command. A quoted script path, or a script path in a variable, does not start the hook.

## 1.0.3

### Changed
- The marketplace is now `cc-plugins`, in the public repository `ai-advanced-futures/cc-plugins`. The plugin ID is `business-domain@cc-plugins`. The homepage and the repository fields point at the public repository, and the install line and the issue link name it. Install the plugins again from the new marketplace.

## 1.0.2

### Changed
- The schema `id` and prefix URLs name the public repository, `cc-plugins`.
- The NOTICE file names no private repository.

## 1.0.1

### Changed
- `/prompt:revise` revised the skill prompts. `learn` has one instruction
  fewer. `learn` and `setup` give a reason next to each prohibition. `ask` names
  the commands of Step 2 that it can run with Bash.

## 1.0.0

### Changed
- Moved to ai-advanced-futures/cc-plugins-library. Renamed from `ddd` to
  `business-domain`: the commands are now `/business-domain:...`.

## 0.2.0

### Added
- The bundle is on the brain standard of the `knowledge` plugin: a manifest,
  the registry entry `ddd`, the base schema, and the output contract.
- `ddd:learn`, and the subcommands `set`, `link`, `unlink`, `remove`, and
  `upgrade`. `ddd:setup` runs `upgrade` on an existing bundle.
- The hook runs the general check after the brain check, and also after a
  Bash command that runs `ddd.py`.

### Changed
- The page-size rule W7 moved to the general check (`K-size`).
- `ddd.py remove` on a bundle with no manifest writes the full manifest, so
  the general check finds no missing field.
- `ddd:ask` hands over to `knowledge:ask` after its shortcuts.

## 0.1.0

### Added

- The domain model as one OKF v0.2 bundle at `docs/domain/`, named by `.claude/ddd.json`.
  Seven page types, one directory for each: Context, Relationship, Term, Aggregate, Event,
  Question, and Source. Each page has a permanent `<PREFIX>-<NN>` ID.
- `schema/domain.yaml`: the LinkML source of the types, the fields, the closed lists, and the
  edge rules. `scripts/gen-schema.sh` writes `schema/domain.schema.json` and
  `schema/domain.slots.json` from it.
- `scripts/ddd.py`: `init`, `new`, `regen` (with `--check`), `check` (rules E1 to E12 and
  W1 to W9, with `--strict`), `merge`, `resolve`, and `log`.
- A `PostToolUse` hook on `Write|Edit`: after an edit of a bundle file, it runs `regen` and
  `check`, and gives an error back to the agent with exit code 2.
- `/ddd:setup`: makes the bundle and adds a router block to `CLAUDE.md`.
- `/ddd:ask`: answers a question from the bundle only, after the drift check.
- `skills/shared/bundle-schema.md`: the bundle format for the skills.

### Known limits

- `scripts/claude_md_router.py` is a byte copy of the prd copy. Its docstring says that the
  file ships in four plugins. It now ships in five. The copies must stay byte-identical, so a
  change to that line is a change to all five plugins, and it is not part of this release.
