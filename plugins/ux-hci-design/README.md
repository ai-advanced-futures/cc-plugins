# ux-hci-design

**Version:** 1.3.0
**Author:** Luis F. Amadeo (the original plugin). ai-advanced-futures ported it to this marketplace.
**License:** MIT (see `NOTICE`)

## What this plugin does

The plugin guides a person through a full UX design workflow. It uses the Design Thinking phases: Empathize, Define, Ideate, Prototype, and Test. Each phase uses the methods of known design authors: Norman, Nielsen, Cooper, Rams, and others. Accessibility (WCAG 2.2) and AI interaction guidelines (Microsoft 18 Guidelines) apply in every phase.

The output is a set of design documents for one product: research findings, personas, journey maps, design concepts, wireframes, and an evaluation report.

## Install

$ claude plugin marketplace add ai-advanced-futures/cc-plugins
$ claude plugin install ux-hci-design@cc-plugins

## Skills

The plugin has 10 skills. Start the skill `ux-design` for the full workflow. The other skills hold the method of one phase or one framework. The phase agents read them. A person can also start them alone.

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

The skill writes these files to the folder `.ux-artifacts/` in your project. Add the folder to your `.gitignore` file.

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

No agent has the tool Agent. The skill `ux-design` starts the 3 reviewers in the main conversation, and then the agent `ux-evaluator`. Claude Code ignores a type list inside `Agent(...)` in an agent file, so this is the way to limit the agents that start. The agent `ux-prototype-builder` has the tool Skill, for the optional plugin below. No agent has the tool Bash.

## Optional: tailwind-plus

The paid plugin `tailwind-plus` is not in this marketplace. When you have it and `.ux-config.json` has `"tailwind_plus": true`, the agent `ux-prototype-builder` calls `/tailwind-plus:advise` for each wireframe region. Without the plugin, the agent marks the region `[FALLBACK: raw Tailwind]` and goes on.

## Scripts

The folder `scripts/` has 7 Python scripts that use only the standard library. You need `python3`. Run a script from the plugin folder, for example:

$ python3 scripts/validate_schemas.py --help

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
