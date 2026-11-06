# Changelog

## 1.0.0

First version in this repository. The plugin is a port of the `architecture` plugin, version 2.10.2, under a new name. Versions 1.0.0 to 2.10.2 of the `architecture` plugin came before the port, from commit `c2a329f` of a private repository.

### Changed

- The plugin name is `architecture-assess`. The `architecture` plugin of this marketplace stores decisions, so the two names must differ. The commands are `/architecture-assess:<folder>`.
- Only a skill asks the person a question. An agent never asks, because Claude Code removes the question tool from every subagent. The skill asks the business questions, then shows the domain plan and asks "Proceed?".
- The orchestrator has two phases. In `phase: plan`, it scans the codebase, writes the domain plan into `session.json`, and ends with `NEEDS-INPUT: orchestrator`. In `phase: run`, it dispatches the confirmed assessors in one message, in the foreground. Then it runs the completion sweep, the synthesizer, the executive summary with the SDLC assessor, and the SDLC challenger.
- The wave orchestrator is a completion sweep with no team. It runs one time after the assessors return, reads the `.done` files, and writes `wave-timeout.json`. The live progress path with an agent team is gone, because only the main session manages a team.
- The synthesizer writes the draft to `<temp folder>/unified-adr.md` and returns `DONE: synthesizer — adr_draft=<path>`. In design mode it also writes `design-pages.json`.
- The plugin saves each decision through `architecture:learn`, after the person agrees. It saves design pages through `system_design.py` of the `system-design` plugin. The plan, the draft, and the executive summary are plain files in `docs/architecture-assess/`.
- Each script runs with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py`. A script has a PEP 723 block, so `uv` installs its packages.
- The two schemas of the cost-class gate are in the folder `schemas/` of the plugin. No file reads a path outside the plugin.
- A skill has no `name:` key, so its name is its folder. An agent has `name:` equal to its file name, and a model alias (`opus`, `sonnet`, or `haiku`). Agents are dispatched with the `Agent` tool as `architecture-assess:<agent>`.
- The label that was the family name of a person is now "Architecture Principles". The same change gives "Architecture Principle #n", "Agentic Pipeline Principles" (AP-n), "Agentic Plugin Principles", "Architecture Constitution", and the markers `§principles-core-start` and `§principles-core-end`. The author credit stays in `NOTICE` and in five lines of `docs/frameworks.md` and `docs/adr`.
- The first principle name in a draft names the source of the set one time, so a reader does not take it for a rule of the `architecture` plugin.
- The recommendation for bounded contexts points to the `business-domain` plugin.
- The `README.md`, the ADRs, the docs, and the C4 page are new or changed, and they agree with the plugin. The counts agree in all files: 23 Architecture Principles, 12 Agentic Pipeline Principles, 8 Agentic Plugin Principles, and 18 section markers in 9 sections.

### Removed

- The hand-off file for an outside dispatcher, its step in the orchestrator, and the side file of the synthesizer that only it read.
- The release file with the keys of the outside dispatcher, and each block in an agent that detected the mode of the dispatch, with its branch for a run with no person. Each agent now does what that branch did.
- The live progress path with an agent team, and the steps that sent messages to it.
- The root `SKILL.md`. Its table of skills is now in the `README.md`.
- The table of 20 plugins of a private marketplace in `docs/sdlc-frameworks.md`, and the consulting flag that gated it.
- The name of a private client and its examples. Generic examples take their place.
- Each mention of a deck tool, and each mention of a plugin that this marketplace does not hold, except `architecture-visualizer`, `agentic`, `value-ip` and `superpowers`. These four stay as optional plugins that the skills and the README name.
- The path that read a folder of the source repository root. The Charter of the agentic pricing program is not copied; the prompts name the schema files instead.
- The test files that read files outside the plugin or need a plugin that is not ported.
- The hook function `layer_candidate` of the cost-class band, which always returned `None`.

### Added

- `scripts/session.py`: `new` makes `.architect-tmp/<id>/`, `clean --older-than 60` deletes old folders, and `remove <id>` deletes one. It deletes only folders under `.architect-tmp/`.
- `scripts/design_to_graph.py`: makes the `Component` pages and `uses` links of the `system-design` graph from `design-pages.json`.
- `scripts/probe-plugin.sh`: finds the root of the `system-design` plugin.
- `NOTICE`, with the MIT license of the source plugin.
- Tests for the rules of the port, for the scripts, for the PEP 723 blocks, and for the version.
