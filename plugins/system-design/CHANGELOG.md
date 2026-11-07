# Changelog

## 0.2.9

### Changed
- The plugin finder does not take a plugin from the `.claude/plugins/` folder of the project (STORY-202).

## 0.2.8

### Changed
- The description of the `Component` class in the schema uses the word "persistent" in place of a word that a private-name check matched. The schema files `system-design.yaml` and `system-design.schema.json` change by this one word. The plugin behavior does not change.

## 0.2.7

### Changed
- The tests and the docs name the job `system-design` of the CI workflow `.github/workflows/ci.yml`. One workflow replaces the workflow file of this plugin. The plugin behavior does not change.

## 0.2.6

### Fixed
- The hook runs its steps only when a Bash command runs `system_design.py`. Before, a quoted text that held `(system_design.py` (for example a page fact in a `knowledge.py walk` command) started the steps. The hook now removes each quoted span before it looks for the script. The hook also ignores a heredoc body and a `#` comment. The time of the check grows in line with the length of the command. A quoted script path, or a script path in a variable, does not start the hook.

## 0.2.5

### Changed
- The marketplace is now `cc-plugins`, in the public repository `ai-advanced-futures/cc-plugins`. The plugin ID is `system-design@cc-plugins`. The homepage and the repository fields point at the public repository, and the install lines and the issue link name it. Install the plugins again from the new marketplace.

## 0.2.4

### Changed
- The schema `id` and prefix URLs name the public repository, `cc-plugins`.

## 0.2.3

### Changed
- Four prohibitions now give their reasons (`/prompt:revise`, rule P7): one
  in each skill and one in the CLAUDE.md router block. The steps and the
  output formats do not change.
- A repository gets the new router block text only when the
  `system-design:setup` skill runs again.

## 0.2.2

### Fixed
- The brain hook checks the session folder (the `cwd` of the hook input), not
  `CLAUDE_PROJECT_DIR`. A session in a worktree no longer gets a false error
  from the main checkout.
- The brain hook starts only for a Bash command that runs `system_design.py`.
  A command that only names the script does nothing. A repository with no
  system-design graph does nothing.

## 0.2.1

### Changed
- The display name is now lowercase: `system-design`.

## 0.2.0

### Changed
- Moved to ai-advanced-futures/cc-plugins-library.

## 0.1.0

### Added
- The system-design brain on the brain standard of the `knowledge` plugin.
  It replaces `/prd:system-design` and its one file.
- Twelve page types: System, Area, Component, Interface, DataEntity,
  QualityScenario, Convention, TechnicalRisk, Deferred, Assumption,
  DeploymentNode, and GlossaryTerm.
- `system_design.py`: init, upgrade, migrate-file, new, set, link, unlink,
  remove, resolve, regen, check, and log.
- `system-design:setup`, `system-design:learn`, and `system-design:ask`.
  `system-design:learn` writes each ADR with `lifecycle: accepted`.
- The hook that runs regen, the brain check, and the general check.
