# competitive-intelligence

This plugin maps the competitors of a market, gathers public facts about them, and analyzes a competitor through six lenses. It writes a SWOT, recommendations, and structured JSON files that other plugins read.

## What the plugin does

- It adapts its depth and its focus to your need: a feature decision, a competitor move, strategic planning, or monitoring.
- It covers the full market: direct competitors, indirect competitors, substitutes, and technology threats.
- It uses six lenses: JTBD performance, forces, economic value, strategic positioning, technology disruption, and loss and churn. The lenses run in four layers, and each layer uses the results of the earlier layers.
- It gives each finding a confidence level, and it checks each finding against more than one source.
- It has two analysis modes: strategic planning (honest about weaknesses) and sales enablement (framed for customers).
- It classifies the pricing of a vendor into one of five archetypes.
- Its output is JSON files and Python scripts that other plugins and tools can read.

## Install

You need [`uv`](https://docs.astral.sh/uv/). The plugin runs two of its scripts with `uv run`.

```
claude plugin install competitive-intelligence@cc-plugins
```

## Skills

The plugin has 13 skills. Run a skill as `/competitive-intelligence:<skill>`. A skill asks you only the questions whose answer you did not give. A text after the skill name is the first answer.

| Skill | Use it to | Questions it asks |
|---|---|---|
| `competitive-intelligence` | Run the full analysis in 6 phases. Claude also starts it when you ask for a competitive analysis, a market assessment, a feature check against competitors, a technology disruption review, win and loss patterns, or a response to a competitive threat. | The questions of `discover`. A checkpoint after each phase: Proceed, Adjust, or Cancel. After the lens phase: Proceed, Deep dive, or Investigate contradictions. Then the deliverables you need. |
| `discover` | Map the competitive landscape in 3 phases (context, ecosystem, intelligence). Writes a result file. | `market`, `trigger`, `scope`, `analysis_mode`, `depth`, `available_data`, and `competitors`. A checkpoint after each phase. |
| `analyze` | Analyze one competitor through the lenses, and write a SWOT and recommendations. Writes a result file. | `competitor`, `offering`, `available_data`, and `analysis_purpose`. A checkpoint after the lenses. |
| `validate` | Check a feature decision against the competitive landscape. | Which customer job the feature addresses. Which outcome it improves. |
| `respond` | Plan a response to a competitor launch, a price change, or an announcement. | The type of the competitor move. The urgency. |
| `monitor` | Find what changed since the last analysis. | The monitoring focus. The time range. |
| `vendor-archetype-classify` | Classify the pricing of a vendor into one of five archetypes. | The vendor name. Its pricing page, as a URL or a pasted text. |
| `lenses-jtbd-performance` | Lens 1: compare the performance of each job step. | None. |
| `lenses-forces-analysis` | Lens 2: find the forces of switching (push, pull, anxiety, habit). | None. |
| `lenses-economic-value` | Lens 3: compare the economic value that each offering creates. | None. |
| `lenses-strategic-positioning` | Lens 4: find the business model, the moats, and the weak points. | None. |
| `lenses-technology-disruption` | Lens 5: assess the risk from AI platforms and new technology. | None. |
| `lenses-loss-churn` | Lens 6: check the other lenses against data on lost deals and lost customers. | None. |

You cannot start the six `lenses-*` skills. The lens executor and the skill `analyze` read them and follow them. A lens needs the `session_id` and the `data_dir` of a run.

### The questions

| Input | Question | Options |
|---|---|---|
| `market` | Which product, market, or feature should the analysis cover? | Free text |
| `trigger` | What led to this analysis? | A decision on whether to build a feature; a competitor move; a full review of the market; a regular update |
| `scope` | How wide should the analysis be? | The full market (default); one segment; one competitor; one feature |
| `analysis_mode` | Is the analysis for internal decisions or for sales positioning? | Internal decisions (default); sales positioning |
| `depth` | How deep should the analysis go? | Quick scan; standard (default); comprehensive |
| `available_data` | What evidence do you have, and where are the files? | Free text |
| `competitors` | Which competitors must the analysis include? | Free text. With no list, the plugin finds the competitors. |
| `competitor` | Which competitor should the analysis cover? | Free text |
| `offering` | Which product of yours should the analysis compare with this competitor? | Free text |
| `analysis_purpose` | What is the analysis for? | Planning (default); a deal against the competitor; the threat the competitor poses; the openings the competitor leaves |
| `deliverables` | Which deliverables do you need? (full run only) | JSON outputs (default); Python scripts; executive summary; battle card; full report |

When a question has no answer, the plugin uses the default, and it records the default in the result file. Five defaults are registered in `result-file.json`: `depth`, `scope`, `available_data` (two defaults, one for each result file) and `analysis_purpose`.

## The six phases

1. **Context discovery.** Find what you need, and configure the analysis.
2. **Ecosystem mapping.** Map the competitors with a classification on six dimensions.
3. **Intelligence gathering.** Collect and check the competitive data.
4. **Multi-lens analysis.** Run the lenses that fit your trigger.
5. **Synthesis.** Write the SWOT and the recommendations with confidence levels.
6. **Deliverable generation.** Write the deliverables that you chose.

You can start at a later phase when the input files of that phase exist.

## Agents

The skills start the agents with the `Agent` tool. An agent asks you nothing, because Claude Code does not let a subagent ask a question. The skill asks the questions and gives the answers to the agent.

| Agent | Model | Job |
|---|---|---|
| `context-analyst` | Sonnet | Phase 1: write the context configuration. |
| `ecosystem-mapper` | Sonnet | Phase 2: classify the competitors. |
| `intelligence-gatherer` | Sonnet | Phase 3: collect and check the data. |
| `lens-executor` | Sonnet | Phase 4: read each lens skill and follow it, one layer after the other. |
| `synthesizer` | Opus | Phase 5: write the SWOT and the recommendations. |
| `deliverable-generator` | Sonnet | Phase 6: write the deliverables. It also holds the rules of the result file. |
| `discover-runner` | Sonnet | Run `discover` for a coach with the answers of a `plugin-run` block. |
| `analyze-runner` | Sonnet | Run `analyze` for a coach with the answers of a `plugin-run` block. |
| `vendor-archetype-classifier-agent` | Sonnet | Find the pricing signals of one vendor and run the classifier. |

When an agent needs an answer in the middle of a run, it writes `open-questions.json` in the session folder and returns `QUESTIONS: <path>`. The skill asks the questions and starts the agent again.

If a phase fails two times, the skill asks you: Retry, Skip (a lens only), or Cancel. The lens executor marks a lens that fails two times as `skipped`, writes the reason in `lens_failures`, and goes on.

## Inputs

- The answers that you give to the questions.
- The evidence files that you name in `available_data`, such as battle cards, win and loss reports, and customer feedback.
- The public web, through the search and fetch tools of Claude Code.
- Optional: the output files of the `jtbd-market-discovery` plugin. The plugin uses them as job-step data. When there are none, the run goes on without them.
- Optional: the data of the `product-finance` plugin, for the economic value lens.

## Outputs

The plugin writes into `.competitive-intelligence/` under the git root of your project.

- **Session folder.** `.competitive-intelligence/<session>/` holds one run. The name is the `run_id` of a coach run, or the start time of your run. It holds `session.json`, `context-config.json`, `competitive-ecosystem.json`, `intelligence-data.json`, a summary file for each phase, the lens analysis files, and the deliverables.
- **Analysis files.** `jtbd-analysis.json`, `forces-analysis.json`, `value-analysis.json`, `strategic-analysis.json`, `technology-disruption.json`, `loss-churn-analysis.json`, `swot-analysis.json`, and `recommendations.json`.
- **Deliverables.** JSON outputs, Python scripts, an executive summary, a battle card, and a full report. You choose them in the full run. The plugin does not run the scripts that it writes.
- **Result files.** `discover` and `analyze` write one result file (`plugin-result/1`) to `.competitive-intelligence/results/` at the end of each run. A partial run and a halted run also write one. The file says which findings the research found and which findings the model inferred.
- **Vendor archetype files.** `.competitive-intelligence/vendor-archetype-handoff.json` and the classification artifact.

Earlier versions wrote to `.competitive-intel/`. The plugin never moves or deletes that folder. Each skill that reads earlier analyses reads both folders, newest file first.

Other plugins read these files. `pricing`, `gtm`, and `business-case` are the readers.

## Run for a coach

The `business-case` coach starts `competitive-intelligence:discover-runner` and `competitive-intelligence:analyze-runner` with a `plugin-run` block. The block has the fields `command`, `automated`, `answers_path`, `case`, `run_id`, and `inputs_from`. A runner asks nothing. It takes each answer from the answers file, and it uses the default in `result-file.json` for each answer that is missing. Then it writes the result file. `questions/discover.json` and `questions/analyze.json` list the inputs of each skill. ADR-004 gives the details.

## Configuration

The plugin needs no setting, no environment variable, and no MCP server. You configure each run through the questions.

- **Analysis parameters.** Phase 1 collects the trigger, the scope, the analysis mode, the depth, and the evidence. It writes them to `context-config.json`. The trigger sets the lens priority. The analysis mode changes only the framing.
- **Session files.** Each run writes to its own folder `.competitive-intelligence/<session>/`. The plugin never deletes a file in `.competitive-intelligence/`.
- **Optional MCP research server.** The intelligence gatherer uses an MCP research server when you added one. Without one, it uses `WebSearch` and `WebFetch`. The plugin starts no outside service. To add a server, run `claude mcp add`. Servers such as Klue or Crayon are options for later. See ADR-001.

## Privacy

The plugin sends search queries to the public web. A query can hold words from your market and from your product. The plugin writes only into `.competitive-intelligence/` under the git root, and into the folders that you name.

## Documentation

- [DESIGN.md](docs/DESIGN.md) - the design of the plugin
- [docs/INDEX.md](docs/INDEX.md) - the ADRs and the diagrams
- [Schemas](schemas/) - the JSON schemas of the output files
- [scripts/README.md](scripts/README.md) - the scripts

## Tests

Run the tests in the plugin folder:

```
pip install -r requirements-dev.txt
pytest tests/ -q -rs
```

## License

This repository is under the Apache-2.0 license. The code of this plugin comes from an MIT-licensed plugin. See [NOTICE](NOTICE) for the notice and the permission text.

## Credits

**Author:** Luis F. Amadeo

**Methods:**
- Jobs To Be Done (Clayton Christensen, Tony Ulwick)
- Outcome-Driven Innovation (Tony Ulwick)
- Forces of Progress (Bob Moesta)
- Economic Value to Customer
- 7 Powers (Hamilton Helmer)
- Disruption Theory (Clayton Christensen)
- JustKeenAI v2.1 vendor archetypes
