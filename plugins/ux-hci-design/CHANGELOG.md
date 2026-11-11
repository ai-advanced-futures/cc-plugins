# Changelog

This file records the changes of the ux-hci-design plugin. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). The version numbers follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.6.3 - 2026-11-11

STORY-358.

- `ux-prototype-builder` writes only in `output_dir`, and only its output files: `wireframes.json`, `interaction_patterns.json`, `user_flows.mmd`, and the open-questions file when it needs an answer. It makes each file with the `Write` tool, because it has no tool that runs a script, so a helper script or a probe file does nothing. A write outside `.ux-artifacts/` makes no file, because the grants of the skill `ux-design` approve no write outside `.ux-artifacts/`. Before this change, the agent wrote a helper script outside the project in 2 of 55 dispatches, and each of those writes was refused.
- New test `tests/unit/test_builder_writes.py` (5 tests): the 3 sentences, the place of the paragraph, the 3 files that the save reads, the tools of the agent, and the 1 write rule of the skill.

## 1.6.2 - 2026-11-10

STORY-343.

- `ux_graph.py remove-questions <output_dir> [--reviewer <reviewer>]` removes the `open-questions.md` file of the run, or of 1 reviewer, and no other file. The skill `ux-design` runs it after it asks the questions of an agent, and before it starts the agent again. The grant of `ux_graph.py` approves it. Before this change, the skill ran `rm`, which no rule approves, so a run with no person stopped at that step: 2 of 3 test phase runs of the PR 1420 verifier stopped before the evaluator.
- The command refuses a folder outside the project, a reviewer that is not 1 of the 3 reviewers, a symbolic link, and a folder with the name of the file.

## 1.6.1 - 2026-11-10

STORY-333, STORY-336 and STORY-338 (the follow-ups of STORY-257).

- `ux_graph.py ingest` refuses a text that the general check reads as a link to a page: a text that starts with `/` and holds `.md`, a text in the form `<graph>:/<path>`, a Markdown link to a `.md` target, and a `<graph>:/<path>.md` in a longer text. It writes 1 `UX-link` line for each such text, with the file and the field, and exits 1 before the lock. It removes no file and changes no page. Before this change, the save removed the files and left a `K-link` error in the brain (STORY-333).
- Before each dispatch, the skill `ux-design` gets each input file from the brain with `view latest`, also when `pages.json` of this run does not list the file. Such a file is input only. The skill says that it can come from a draft run, and starts the agent without it when the brain does not hold it (STORY-336).
- The skill `ux-design` starts each agent in the foreground with `run_in_background: false`, and says what to do when Claude Code still starts one in the background (STORY-338).
- The skill `ux-design` lets a phase agent write its files in `.ux-artifacts/` and read its method and schema files (`Edit(/.ux-artifacts/**)`, `Read(//**/ux-hci-design/**/skills/**)`, `Read(//**/ux-hci-design/**/schemas/**)`). Before this change, a run in the default permission mode with no person refused each of these calls, so the phase saved nothing.
- The agents `ux-researcher`, `ux-artifact-generator`, `ux-concept-designer` and `ux-prototype-builder` write no such text, and the agent `ux-evaluator` gives the true reason of its rule: the save refuses a file with such a text.
- `uxlib/ingest.py` has a correct docstring for a new run, and a test of `test_ingest.py` that could not fail now checks the places of the first run.

## 1.6.0 - 2026-11-10

Part B of STORY-257: the skills and the write flow of the brain.

- Behavior change: after a save, `.ux-artifacts/` holds no output file. The save removes each file that it read, and `ux_graph.py view` prints the file again. If a save does not run ("No brain now"), the plain files stay.
- New skills `setup`, `learn` and `ask`. `setup` asks if git keeps the brain, makes the bundle, writes the router block in `CLAUDE.md`, and offers to save an earlier `.ux-artifacts/`. It needs the plugin `knowledge` 1.6.0 or later.
- The skill `ux-design` asks the git question before the first save (3 answers; a run with no person keeps the brain out of git and says so), runs `ingest` after each phase, runs `view --out` before each dispatch, asks "Learn these results?" at the end, and names `/product:setup` when the project has no PRD graph.
- New hook `hooks/brain-hook.sh` runs `ux_graph.py regen`, `ux_graph.py check` and `knowledge.py check` after a write. New router template `templates/claude-md-block.md`, and the copies `scripts/claude_md_router.py` and `scripts/probe-plugin.sh`.
- Text fixes: `user_flow.mmd` is `user_flows.mmd` in the agent `ux-prototype-builder`; ADR-002 names the real place of the Track 3 output, `implementation_handoff` of `research_findings.json`.
- The readers of `research_findings.json` (the skills `define` and `jtbd-bridge`, the agent `ux-artifact-generator`) name the research findings of the `inputs` list.
- `ux_graph.py upgrade` takes `--git yes|no`. Without it the first git answer stays. The skill `setup` passes the new answer, so "Run /ux-hci-design:setup to change this" works, and the exclude file of the clone follows the answer. The option works only for a folder that holds the `manifest.md` of this brain, because a cloned repository can set the folder in the registry (issue 1370). When the answer changes to "out of git", `setup` counts the files that git still tracks and names `git rm -r --cached`. A `setup` run with no person keeps the answer of an existing entry.
- A new run (`ingest --new-run`) makes its own Evaluation, EvalFinding, Journey and other pages, in each phase of the run, not only in the first. The later phases of the new run use only the places that an earlier phase of the same run saved, and `pages.json` holds only the places of the new run. Only the Persona, Screen, Concept and InteractionRule pages are reused across runs, found by key. `init --git no` prints the line "The UX brain is in docs/ux-hci-design/, and git does not keep it."
- `ux_graph.py ingest` joins the run of `pages.json` only while that run is a draft, and a run that a person confirmed keeps its status. The option `--new-run` starts a new Run page. The skill `ux-design` passes it on the first `ingest` of each run of the skill, so a second run is not joined to the first.
- The agent `ux-evaluator` writes no path that ends in `.md` in the report, because the brain check read such a path as a link and gave `K-link` errors in a live run.
- The live test `test_live_port.py` reads the report through `ux_graph.py view latest evaluation_report.json`.

## 1.5.0 - 2026-11-10

Part A of STORY-257: the save code and the schema of the brain. No skill calls the code yet (part B).

- `plugin.json` lists the plugin `knowledge` as a dependency. The plugin needs Claude Code 2.1.110 or later.
- New script `scripts/ux_graph.py` with the modules in `scripts/uxlib/`: `init` (with `--git yes|no`), `ingest`, `view`, `pages`, `behavior`, `check`, and the other save commands of a brain. It makes no network call.
- `init --git no` writes `"git": false` to the registry entry and adds the folder to `info/exclude` of the clone, so git does not keep it.
- `ingest` saves the output files of one phase as pages in `docs/ux-hci-design/`. After the checks pass, it removes the plain files that it read. A failed check changes no page and removes no file. A `.mmd` file is kept as the text of a Diagram page; its line ends become new lines.
- New LinkML schema `schema/ux-hci-design.yaml` for the 14 page types, with the generated `ux-hci-design.schema.json` and `ux-hci-design.slots.json`. `scripts/gen-schema.sh` makes them again.
- New schema `schemas/outputs/research-findings-schema.json` for `research_findings.json`.
- `requirements-dev.txt` needs `linkml`, `linkml-runtime` and `pyyaml` (pinned).

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
