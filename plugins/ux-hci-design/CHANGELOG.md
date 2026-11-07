# Changelog

This file records the changes of the ux-hci-design plugin. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). The version numbers follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.4.0 - 2026-11-06

- `ux-evaluator` and the skill `ux-evaluate` name the schema `schemas/outputs/evaluation-report-schema.json` and tell the agent to read it before it writes the report. The dispatch of the evaluator has the field `schema_file`.
- The report examples of the 2 files, and the 3 example reports in `examples/`, agree with the schema. The evaluator writes `severity` as `critical`, `major`, `moderate` or `minor`, `priority` as the normalized level, and the tag `provisional` for a finding that rests on an assumption.
- New script `scripts/check_output.py FILE --schema NAME`: it prints 1 line for each schema error. The skill `ux-design` runs it after the evaluator (Step 3) and starts the evaluator 1 more time with the error lines; the skill `ux-evaluate` runs it after a report that it writes itself. A report with errors is not called complete. The check needs `uv`.
- `requirements-dev.txt` needs `jsonschema>=4.17.0`.

## 1.3.2 - 2026-11-06

This version closes the 7 follow-up items of the port review (STORY-136).

- The skill `ux-design` and the skill `prd-bridge` name 1 PRD format, a PRD Markdown file. The skill `prd-bridge` maps it to its JSON structure.
- The skill `ux-design` deletes `<output_dir>/open-questions.md` (also the file of a reviewer) after it asks the questions, so an old file does not start the same questions again. The delete is 1 `rm -f --` command with 1 path, and the person approves it.
- The script `detect_context.py` writes `project_context.has_ai_features` (true when `ai_intensity` is not `none`), and the schema `project-context-schema.json` has this optional key. The skill `ux-design` and the agent `ux-evaluator` say where the key is. Before this version a saved config had no `has_ai_features`, so the skill did not start `ai-hci-reviewer`. To fix a config that version 1.3.1 or earlier saved, run `scripts/detect_context.py --save` again, or add `has_ai_features: true` to it.
- `docs/AGENTS.md` names the file `mental_models.mmd` (it was `mental_model.json`).
- The script `detect_context.py` prints `/ux-hci-design:ux-design` (it printed `/ux-design`).
- `docs/SCHEMAS.md` says 31 Level A criteria (it said 32).
- When a config has no `has_ai_features` key, the skill `ux-design` does not start `ai-hci-reviewer` and tells the person in 1 line.
- The skill `accessibility-audit` and the agent `accessibility-reviewer` say 31 Level A criteria and 55 total at AA, the counts of the schema (they said 25 and 49).
- 3 tests no longer pass when their file scan is empty: `test_no_text_of_the_source_repository_stack_remains`, `test_schema_and_skill_paths_start_with_the_plugin_root_variable` and `test_actual_schemas`.

## 1.3.1 - 2026-11-06

- The skill `ux-design` runs the reviewers in the foreground, waits for each of them, and checks each findings file before it starts `ux-evaluator`.
- Each reviewer writes `<output_dir>/reviews/<reviewer>/findings.json` with the list under the key `findings` (the usability reviewer used another key before).
- `ux-evaluator` stops with `MISSING_REVIEW: <reviewer> <path>` and writes no report when a findings file is missing. The skill shows the line and stops.

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
