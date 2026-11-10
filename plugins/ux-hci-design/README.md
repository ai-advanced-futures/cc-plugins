# ux-hci-design

**Version:** 1.6.1
**Author:** Luis F. Amadeo (the original plugin). ai-advanced-futures ported it to this marketplace.
**License:** MIT (see `NOTICE`)

## What this plugin does

The plugin guides a person through a full UX design workflow. It uses the Design Thinking phases: Empathize, Define, Ideate, Prototype, and Test. Each phase uses the methods of known design authors: Norman, Nielsen, Cooper, Rams, and others. Accessibility (WCAG 2.2) and AI interaction guidelines (Microsoft 18 Guidelines) apply in every phase.

The output is a set of design documents for one product: research findings, personas, journey maps, design concepts, wireframes, and an evaluation report.

## Install

$ claude plugin marketplace add ai-advanced-futures/cc-plugins
$ claude plugin install ux-hci-design@cc-plugins

## Skills

The plugin has 13 skills. Start the skill `ux-design` for the full workflow. The other skills hold the method of one phase or one framework. The phase agents read them. A person can also start them alone.

| Skill | Command | Use |
|-------|---------|-----|
| `ux-design` | `/ux-hci-design:ux-design` | The full guided workflow, one phase, or a quick action |
| `empathize` | `/ux-hci-design:empathize` | Method of the research phase |
| `define` | `/ux-hci-design:define` | Method for personas, journey maps, and mental models |
| `ideate` | `/ux-hci-design:ideate` | Method for design concepts |
| `prototype` | `/ux-hci-design:prototype` | Method for wireframes and interaction patterns |
| `ux-evaluate` | `/ux-hci-design:ux-evaluate` | Method for the evaluation and the UX health score |
| `accessibility-audit` | `/ux-hci-design:accessibility-audit` | WCAG 2.2 Level AA audit |
| `ai-hci-audit` | `/ux-hci-design:ai-hci-audit` | Audit with the Microsoft 18 Guidelines |
| `jtbd-bridge` | `/ux-hci-design:jtbd-bridge` | Turns Jobs-to-be-Done data into UX artifacts |
| `prd-bridge` | `/ux-hci-design:prd-bridge` | Turns a PRD into design requirements |
| `setup` | `/ux-hci-design:setup` | Makes the UX brain, asks if git keeps it, and saves earlier results |
| `learn` | `/ux-hci-design:learn` | Confirms the pages of a run, or saves a fact that you give |
| `ask` | `/ux-hci-design:ask` | Answers a question from the UX brain |

### Arguments of the skill `ux-design`

| Command | Result |
|---------|--------|
| `/ux-hci-design:ux-design` | All 5 phases, with questions |
| `/ux-hci-design:ux-design empathize` | Research only |
| `/ux-hci-design:ux-design define` | Personas and journey maps only |
| `/ux-hci-design:ux-design ideate` | Design concepts only |
| `/ux-hci-design:ux-design prototype` | Wireframes only |
| `/ux-hci-design:ux-design test` | Evaluation only |
| `/ux-hci-design:ux-design integrate` | Imports JTBD and PRD data |
| `/ux-hci-design:ux-design evaluate-heuristics` | Quick Nielsen and AI-HCI evaluation |
| `/ux-hci-design:ux-design accessibility-audit` | Quick WCAG 2.2 check |
| `/ux-hci-design:ux-design generate-persona` | One persona from data |
| `/ux-hci-design:ux-design journey-map` | One journey map from job steps |

## Questions the skill asks

The skill `ux-design` is the only part that asks questions. It uses AskUserQuestion. It asks:

1. **Context.** The skill detects your project (platform, users, AI features) and shows it. You answer `yes` or `modify`. When the file `.ux-config.json` exists, the skill uses it and asks no context question. The skill writes the file after you confirm the context.
2. **Start of a phase.** You answer `yes`, `no`, or `learn more`.
3. **Start point of the Define phase.** You choose research from the Empathize phase, JTBD data, or existing research.
4. **Integration.** You choose JTBD only, PRD only, or both.
5. **Open questions of an agent.** An agent cannot ask. It writes its questions to `<output_dir>/open-questions.md`. The skill asks them and starts the agent again with your answers.

## Inputs

- A JTBD opportunity file (JSON), from the plugin `jtbd-market-discovery`. This input is optional.
- A PRD file (Markdown). This input is optional.
- Your own research notes. This input is optional.

## Outputs

The agents write these files to the folder `.ux-artifacts/` in your project. After each phase, the skill `ux-design` saves the files as pages of the brain `docs/ux-hci-design/` and removes the files that it read (see "Brain"). `ux_graph.py view` prints a saved file again. If you answer "No brain now", the files stay in `.ux-artifacts/`; add the folder to your `.gitignore` file.

| Phase | Files |
|-------|-------|
| Empathize | `research_findings.json` |
| Define | `personas.json`, `journey_maps.json`, `mental_models.mmd` |
| Ideate | `design_concepts.json` |
| Prototype | `wireframes.json`, `interaction_patterns.json`, `user_flows.mmd` |
| Test | `evaluation_report.json` |

The JSON schemas for these files are in `schemas/outputs/`. The folder `examples/` holds 3 example projects with a `.ux-config.json` file.

## Agents

A skill starts an agent as `ux-hci-design:<agent>`. An agent cannot ask the person a question.

| Agent | Phase | Task |
|-------|-------|------|
| `ux-researcher` | Empathize | Research and handoff decisions |
| `ux-artifact-generator` | Define | Personas, journey maps, mental models |
| `ux-concept-designer` | Ideate | Design concepts |
| `ux-prototype-builder` | Prototype | Wireframes and interaction patterns |
| `ux-evaluator` | Test | Merges the findings of the 3 reviewers and writes the report |
| `accessibility-reviewer` | Test | WCAG 2.2 Level AA |
| `usability-reviewer` | Test | Nielsen heuristics and Rams principles |
| `ai-hci-reviewer` | Test | Microsoft 18 Guidelines (only when the product has AI features) |

No agent has the tool Agent. The skill `ux-design` starts the 3 reviewers in the main conversation, waits for each of them, and then starts the agent `ux-evaluator`. Each reviewer writes `.ux-artifacts/reviews/<reviewer>/findings.json`. Claude Code ignores a type list inside `Agent(...)` in an agent file, so this is the way to limit the agents that start. The agent `ux-prototype-builder` has the tool Skill, for the optional plugin below. No agent has the tool Bash.

## Optional: tailwind-plus

The paid plugin `tailwind-plus` is not in this marketplace. When you have it and `.ux-config.json` has `"tailwind_plus": true`, the agent `ux-prototype-builder` calls `/tailwind-plus:advise` for each wireframe region. Without the plugin, the agent marks the region `[FALLBACK: raw Tailwind]` and goes on.

## Scripts

The folder `scripts/` has 8 Python scripts. Seven use only the standard library, and you need `python3` for them. `check_output.py` checks an output file against its schema, and it needs `uv` (it gets `jsonschema`). The skill `ux-design` runs it after the evaluator. Run a script from the plugin folder, for example:

$ python3 scripts/validate_schemas.py --help

## Brain

The plugin is a brain of the brain standard. It needs the plugin `knowledge` (`plugin.json` lists it as a dependency) and Claude Code 2.1.110 or later. The save code is `scripts/ux_graph.py` (it needs the Python packages `jsonschema` and `pyyaml`). It writes the pages of the brain in `docs/ux-hci-design/`:

- `ux_graph.py init --git yes|no` makes the folder and the registry entry. With `--git no`, git does not keep the folder: the entry has `"git": false`, and the folder is in `info/exclude` of the clone.
- `ux_graph.py ingest <output folder> --phase <phase>` saves the output files of one phase as pages. After the checks pass, it removes the plain files that it read.
- `ux_graph.py view <run> <file>` puts an output file together again from the pages.
- `ux_graph.py pages <type>` and `ux_graph.py behavior` list pages for other plugins.
- `ux_graph.py check` checks the brain.

The code makes no network call.

### Git and the privacy of the brain

The pages can hold facts about real people (research findings, personas). A fact that git keeps stays in the history of git, also after you delete the page. So the first save asks 1 question, with 3 answers:

- "Git keeps the UX brain (docs/ux-hci-design/)": the folder is part of your repository.
- "Keep the UX brain out of git": the registry entry has `"git": false`, and the folder is in `info/exclude` of your clone. A new clone has no brain until `/ux-hci-design:setup` runs there. The knowledge check gives a warning with the steps to fix it, not an error.
- "No brain now": nothing is saved. The files stay in `.ux-artifacts/`, and `/ux-hci-design:setup` saves them later.

A run with no person (for example `claude -p`) keeps the brain out of git and says so.

### The write flow

1. `/ux-hci-design:setup` makes the brain (or `ux-design` does it at the first save, after the question).
2. After each phase, `ux-design` runs `ux_graph.py ingest`. The pages have `status: draft`. The test phase saves the report only after `check_output.py` exits 0.
3. Before it starts the agent of the next phase, `ux-design` runs `ux_graph.py view ... --out` for each saved input file, and gives the agent that copy.
4. At the end of a run, `ux-design` asks "Learn these results?". `/ux-hci-design:learn` confirms the pages of the run.
5. `ux_graph.py behavior` lists the screens, state rules, interaction rules and user flows for the PRD. To add them to the PRD, set up `/product:setup` first.

The plugin `knowledge` must be version 1.6.0 or later. Version 1.5.x gives a `K-manifest` error for this brain.

## Schemas

| Folder | Content |
|--------|---------|
| `schemas/heuristics/` | Nielsen 10 Usability Heuristics |
| `schemas/design-principles/` | Rams 10 Principles, Norman interaction principles |
| `schemas/accessibility/` | WCAG 2.2 Level A and AA criteria |
| `schemas/ai-hci/` | Microsoft 18 Guidelines |
| `schemas/ai-paradigm/` | Patterns for AI-native interfaces |
| `schemas/outputs/` | Format of each design document |

## Documents

- [docs/AGENTS.md](./docs/AGENTS.md): the agents
- [docs/SCHEMAS.md](./docs/SCHEMAS.md) and [docs/SCHEMA-VALIDATION.md](./docs/SCHEMA-VALIDATION.md): the schemas
- [docs/TESTING.md](./docs/TESTING.md) and [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)
- [docs/adr/](./docs/adr/): the decisions on the architecture
- [docs/diagrams/ux-hci-design-c4.md](./docs/diagrams/ux-hci-design-c4.md): the C4 diagram
- [CHANGELOG.md](./CHANGELOG.md)

## Run the tests

From the plugin folder:

$ pip install -r requirements-dev.txt
$ pytest tests/ -q -rs

The suite must show 0 skipped tests.
