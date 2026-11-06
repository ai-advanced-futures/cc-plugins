# data-strategy

This plugin assesses the data strategy of a software company. It checks if the data work fits the business goals, how mature the data platform is, and how good the data products are. It writes 3 documents.

## Install

```
claude plugin install data-strategy@cc-plugins
```

The plugin runs Python scripts with `uv run`. Install `uv` first. The scripts need no other package.

## Skills

| Skill | What it does |
|-------|--------------|
| `/data-strategy:data-strategy` | Full assessment. Asks all the questions, then runs the 3 domains, the synthesis, and the deliverables. |
| `/data-strategy:strategy` | Strategy only. Checks the 11 DAMA-DMBOK knowledge areas and the Gartner D&A maturity level. |
| `/data-strategy:platform` | Data platform only. Checks the 4 Data Mesh principles and the engineering lifecycle. Can scan the project for pipeline files. |
| `/data-strategy:products` | Data products only. Checks the product portfolio and the data contracts. |
| `/data-strategy:roadmap` | Writes the 3 deliverables again from an earlier assessment. Asks nothing. |

## The questions

Only a skill asks you questions. The agents ask nothing. The questions are in `docs/intake.md`:

1. Company context: what the company does, its stage, its main goal, and a maturity rating from 1 to 5.
2. DAMA: a rating from 0 to 4 for each of the 11 knowledge areas.
3. Gartner: a rating from 0 to 4 for 5 analytics abilities.
4. Data Mesh: a value from 0.0 to 1.0 for each of the 4 principles.
5. Codebase scan (optional): if you agree, the plugin lists file names in the current project with Glob to find data pipeline tools.

## Frameworks

| Framework | Agent | Domain |
|-----------|-------|--------|
| DAMA-DMBOK (11 knowledge areas) | `strategy-assessor` | Governance maturity |
| Gartner D&A Maturity (5 levels) | `strategy-assessor` | Business maturity |
| Data Mesh (Dehghani, 4 principles) | `platform-auditor` | Architecture |
| Data Engineering Lifecycle (Reis and Housley) | `platform-auditor` | Implementation |
| Data as a Product (DJ Patil, Dehghani) | `product-analyst` | Product portfolio |
| Data Contracts (Andrew Jones) | `product-analyst` | Producer and consumer rules |

## Output

The plugin writes to the folder `.data-strategy-tmp/<session_id>/` of the current project. It writes nowhere else.

| File | Content |
|------|---------|
| `context.yaml`, `session.json` | Your answers and the session data |
| `strategy.md`, `platform.md`, `products.md` | One file for each domain |
| `synthesis.md` | The joined result |
| `strategy-report.md` | Deliverable 1: maturity scores, gaps, and recommendations |
| `data-platform-adr.md` | Deliverable 2: platform decisions in an ADR |
| `data-roadmap.md` | Deliverable 3: an effort and impact matrix |

## Agents

The skill `data-strategy` starts `data-strategy:orchestrator`. The orchestrator starts the other agents in this order: the 3 domain agents (`strategy-assessor`, `platform-auditor`, `product-analyst`) in parallel, then `synthesizer`, then `deliverable-generator`. See `docs/adr/ADR-001-data-strategy-plugin-architecture.md` and `docs/diagrams/data-strategy-c4.md`.

## Scripts

Scripts do the scoring, so the agents do not calculate the numbers. Run each one with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py <input.json>`.

| Script | Purpose |
|--------|---------|
| `dama_scorer.py` | Scores the 11 DAMA knowledge areas |
| `maturity_calculator.py` | Gives the Gartner maturity level (1 to 5) |
| `data_mesh_evaluator.py` | Scores the 4 Data Mesh principles |
| `product_portfolio_scorer.py` | Scores each data product and the portfolio |
| `roadmap_builder.py` | Sorts items into 4 groups by effort and impact |
| `session_manager.py` | Makes the session, and checks the `.done` flags and the output files |

## Data and privacy

The plugin reads your answers. With your consent, it reads file names in the current project with Glob. It writes only to `.data-strategy-tmp/`. The 3 domain agents can use web search, and a search query can hold words from your company context. Do not give secrets in your answers.

## Tests

```
python3 -m pip install -r requirements-dev.txt
python3 -m pytest tests -q
```

The CI job `data-strategy` runs the same tests.
