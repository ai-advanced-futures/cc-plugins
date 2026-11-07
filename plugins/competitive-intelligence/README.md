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

You need [`uv`](https://docs.astral.sh/uv/). The plugin runs its scripts with `uv run`.

The plugin is a brain of the brain standard. It needs the plugin `knowledge` (`plugin.json` lists it as a dependency) and Claude Code 2.1.110 or later. Run `/competitive-intelligence:setup` once in each project.

```
claude plugin install competitive-intelligence@cc-plugins
```

## Skills

The plugin has 16 skills. Run a skill as `/competitive-intelligence:<skill>`. A skill asks you only the questions whose answer you did not give. A text after the skill name is the first answer.

| Skill | Use it to | Questions it asks |
|---|---|---|
| `competitive-intelligence` | Run the full analysis in 6 phases. Claude also starts it when you ask for a competitive analysis, a market assessment, a feature check against competitors, a technology disruption review, win and loss patterns, or a response to a competitive threat. | The questions of `discover`. A checkpoint after each phase: Proceed, Adjust, or Cancel. After the lens phase: Proceed, Deep dive, or Investigate contradictions. Then the deliverables you need. |
| `discover` | Map the competitive landscape in 3 phases (context, ecosystem, intelligence). Writes a result file. | `market`, `trigger`, `scope`, `analysis_mode`, `depth`, `available_data`, and `competitors`. A checkpoint after each phase. |
| `analyze` | Analyze one competitor through the lenses, and write a SWOT and recommendations. Writes a result file. | `competitor`, `offering`, `available_data`, and `analysis_purpose`. A checkpoint after the lenses. |
| `validate` | Check a feature decision against the competitive landscape. | Which customer job the feature addresses. Which outcome it improves. |
| `respond` | Plan a response to a competitor launch, a price change, or an announcement. | The type of the competitor move. The urgency. |
| `monitor` | Find what changed since the last analysis. | The monitoring focus. The time range. |
| `vendor-archetype-classify` | Classify the pricing of a vendor into one of five archetypes. | The vendor name. Its pricing page, as a URL or a pasted text. |
| `setup` | Make the graph of this project: the folder `docs/competitive-intelligence/`, the entry in `.claude/knowledge.json`, and the router block in `CLAUDE.md`. It then offers to ingest each earlier session folder. | None. |
| `learn` | Confirm the pages of a run (`status: stable`, with your name), or save one fact that you give. | The fact, when you give none. |
| `ask` | Answer a question from the graph, for example "which competitors does market X have". It names the page of each fact. | None. |
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
| `vendor-archetype-classifier-agent` | Sonnet | Find the pricing signals of one vendor and write the input file. The skill runs the classifier. |

Each agent has a short list of tools. No agent has `Bash` or `Agent`: a skill runs each program and starts each agent. The intelligence gatherer has only `Read`, `Write`, `Grep`, `Glob`, `WebSearch` and `WebFetch`.

When an agent needs an answer in the middle of a run, it writes `open-questions.json` in the session folder and returns `QUESTIONS: <path>`. The skill asks the questions and starts the agent again.

If a phase fails two times, the skill asks you: Retry, Skip (a lens only), or Cancel. The lens executor marks a lens that fails two times as `skipped`, writes the reason in `lens_failures`, and goes on.

## Inputs

- The answers that you give to the questions.
- The evidence files that you name in `available_data`, such as battle cards, win and loss reports, and customer feedback.
- The public web, through the search and fetch tools of Claude Code.
- Optional: the output files of the `jtbd-market-discovery` plugin, when you name them in `available_data`. When there are none, the run goes on without them.

## Outputs

The plugin writes into `.competitive-intelligence/` under the git root of your project.

- **Session folder.** `.competitive-intelligence/<session>/` holds one run. The name is the `run_id` of a coach run, or the start time of your run. It holds `session.json`, `context-config.json`, `competitive-ecosystem.json`, `intelligence-data.json`, a summary file for each phase, the lens analysis files, and the deliverables.
- **Analysis files.** `jtbd-analysis.json`, `forces-analysis.json`, `value-analysis.json`, `strategic-analysis.json`, `technology-disruption.json`, `loss-churn-analysis.json`, `swot-analysis.json`, and `recommendations.json`.
- **Deliverables.** JSON outputs, Python scripts, an executive summary, a battle card, and a full report. You choose them in the full run. The plugin does not run the scripts that it writes.
- **Result files.** `discover` and `analyze` write one result file (`plugin-result/1`) to `.competitive-intelligence/results/` at the end of each run. A partial run and a halted run also write one. The file says which findings the research found and which findings the model inferred.
- **The graph.** At the end of a run, the skill runs `ingest`, and the files of the run become pages in `docs/competitive-intelligence/` (see "The graph"). Git keeps this folder, so the pages hold the market, the offering, and the competitor names of your project. To keep them out of git, add the folder to `.gitignore`.
- **Vendor archetype files.** `.competitive-intelligence/vendor-archetype-handoff.json` and the classification artifact.

Earlier versions wrote to `.competitive-intel/`. The plugin never moves or deletes that folder. Each skill that reads earlier analyses reads both folders, newest file first.

Other plugins read these files. `pricing`, `gtm`, and `business-case` are the readers.

## The graph

The plugin keeps what it learns in a knowledge graph: `docs/competitive-intelligence/`. The graph has 19 page types: Run, Market, Competitor, Offer, Source, Finding, Gap, LensResult, Moat, SwotItem, Recommendation, Change, Threat, Response, Validation, Archetype, Summary, BattleCard, and Result. The schema is in `schema/`.

Only `scripts/ci_graph.py` writes the graph. Do not edit a page by hand. The commands are `init`, `upgrade`, `new`, `set`, `body`, `link`, `unlink`, `remove`, `resolve`, `regen`, `check`, `log`, `ingest`, `view`, `results`, `pages`, `verify`, and `verify-run`.

- `ingest <session folder> [--result FILE]` writes the pages of a run. It works on a copy of the graph, and it changes the graph only when the check passes. When the check fails, no page changes and no file is removed. When the project has no graph, it makes one and prints `INIT: docs/competitive-intelligence/`. After a good run it removes each file that a page holds: an item page, or the Run page for the files of `RUN_PAGE_HANDLERS` in `scripts/cilib/ingest.py`. A file that gave no page stays, and the output names it in a `NO PAGE:` line. It keeps the files that another plugin still reads (`READER_FILES` in `scripts/cilib/ingest.py`), the state files, and the result files. It writes `pages.json` into the session folder. The file names each removed file and lists the page of each item.
- `verify KEY --by human:<login>` and `verify-run RUN --by human:<login>` confirm one page, or a run and each page of it. Each page gets `status: stable` and one more `verified` entry, so a second confirmation keeps the first. `resolve` and `verify-run` take a session id (the `run_id` of the Run page).
- `view RUN FILE` builds a session file again from the pages. The new file has the same content as the file that `ingest` read.
- `results` prints the result file (`plugin-result/1`) of a run from the Result pages. `pages TYPE [--run KEY]` prints the pages of one type as JSON. Neither command writes a file.
- A page of the type Market, Competitor, Offer, or Source belongs to all runs. It keeps the item of each run under the name of the run, so `view` of an older run shows the data of that run. Each field of the page itself (for example the threat level) holds the value of the newest run that gives the field. The newest run has the latest `started_at`; a run with no `started_at` is the oldest, and `run_id` decides a tie. The field `field_runs` names the run of each value. So the order of 2 ingests does not change the graph. A run gives only the fields that its files give: a run that names no market joins the one market of the graph and changes none of its fields. A run from one archetype file has no `started_at`, so it is the oldest, and `run_id` (a hash of the file) orders two such runs. A start time that is not ISO 8601 also ranks the run oldest, and `ingest` prints one `note:` line. A field that a person gives with `ci_graph.py new` (the title and the description too) or sets with `ci_graph.py set` is kept: `field_runs` names `(person)` for it, and no run replaces it.

## The write flow

1. Each skill writes its files into the session folder, as before.
2. The last step of the skill runs `ci_graph.py ingest`. The pages have `status: draft`.
3. In a run with a person, the skill asks one question: "Learn these results?" On yes, `learn` sets `status: stable` on each page of the run.
4. In a plugin run, the skill asks nothing, and the pages stay `draft`. A halted plugin run has no session folder of its own, so it runs `ingest --result <result file>` with no path.
5. A skill that reads a file of an earlier run runs `view`, because `ingest` moved the file into the graph.

A PostToolUse hook (`hooks/brain-hook.sh`) runs `regen` and both checks after each write to the bundle and each call of `ci_graph.py`.

`bash scripts/gen-schema.sh` makes the schema files again after you change `schema/competitive-intelligence.yaml`. It needs the packages in `requirements-dev.txt`.

## Run for a coach

The `business-case` coach calls the skill `competitive-intelligence:discover` or `competitive-intelligence:analyze` with the `Skill` tool. The arguments are a `plugin-run` block, or 1 line that is the path of a file that holds the block. The block has the fields `command`, `automated`, `answers_path`, `case`, `run_id`, and `inputs_from`. In a plugin run, the skill asks nothing and shows no checkpoint. It takes each answer from the answers file, and it uses the default in `result-file.json` for each answer that is missing. It starts the phase agents itself. Then it writes the result file. The run happens in the conversation of the coach, so it has each tool of that session. `questions/discover.json` and `questions/analyze.json` list the inputs of each skill. ADR-004 gives the details.

## Configuration

The plugin needs no setting, no environment variable, and no MCP server. You configure each run through the questions.

- **Analysis parameters.** Phase 1 collects the trigger, the scope, the analysis mode, the depth, and the evidence. It writes them to `context-config.json`. The trigger sets the lens priority. The analysis mode changes only the framing.
- **Session files.** Each run writes to its own folder `.competitive-intelligence/<session>/`. The plugin deletes a file in `.competitive-intelligence/` only when `ci_graph.py ingest` has written the file into pages.
- **Optional MCP research server.** When you added an MCP research server, the skill `discover` or `competitive-intelligence` calls it for each Tier 1 and Tier 2 competitor before phase 3, and writes the results to `research-notes.json` in the session folder. The intelligence gatherer reads that file. The gatherer has no MCP tool of its own. Without a server, it uses `WebSearch` and `WebFetch`. The plugin starts no outside service. To add a server, run `claude mcp add`. Servers such as Klue or Crayon are options for later. See ADR-001.

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
