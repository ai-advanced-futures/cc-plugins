# Changelog

This file records the changes of the ux-hci-design plugin. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). The version numbers follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.3.0 - 2026-11-05

This version is the port of the plugin to the cc-plugins marketplace (STORY-73).

### Changed

- Each skill name is now the name of its folder. The plugin adds the prefix, so the commands are `/ux-hci-design:<skill>`. The fields `invocation`, `invocation_legacy`, and `version` are removed from the skill files.
- The skill `evaluate` is now `ux-evaluate`. The marketplace has another plugin with a skill `evaluate`.
- The skill `ux-design` asks its questions with AskUserQuestion. It starts each agent as `ux-hci-design:<agent>` with the fields `project_context`, `inputs`, `output_dir`, and `method_file`. An agent writes its open questions to `<output_dir>/open-questions.md` and the skill asks them.
- No agent has the tool Agent, because Claude Code ignores a type list inside `Agent(...)` in an agent file. The skill `ux-design` starts the reviewers `accessibility-reviewer`, `usability-reviewer`, and `ai-hci-reviewer` in the main conversation, each with its `method_file`. Then it starts `ux-evaluator`, which merges their findings. Only `ux-prototype-builder` has the tool Skill, for the optional plugin tailwind-plus.
- Each path to a schema or a skill in an agent or a skill file starts with `${CLAUDE_PLUGIN_ROOT}/`.
- The plugin `tailwind-plus` is optional. It is a paid plugin and is not in this marketplace. Without it, the agents use the fallback `raw_tailwind_fallback`.
- The tests are in `tests/unit/` only. The tests find no silent skip. The new file `tests/unit/test_port_rules.py` pins the rules of the port. The file `requirements-dev.txt` replaces `requirements.txt`.
- All documents are in ASD-STE100 Simplified Technical English. The text of the root `SKILL.md` is now in the README.

### Removed

- The file `.claude-plugin/release.json` and each mention of the mission-control system.
- Each mention of the `firework` plugin and of `plan-execution`.
- The root `SKILL.md`, the build plan, the build report, and the design document from before the build.

### Added

- The file `NOTICE` with the MIT License of the original plugin.

## Versions before the port

The versions 1.0.0 to 1.2.0 came before the port. They are in commit `c2a329f` of a private repository, the source of this plugin. This file does not repeat them.
