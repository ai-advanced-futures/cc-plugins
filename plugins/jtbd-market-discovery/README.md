# JTBD Market Discovery

Find market opportunities with Jobs To Be Done (JTBD) and numbers. The plugin guides you from one job statement to ranked opportunities, customer segments and a validated price.

**Version:** 1.7.0
**Author:** ai-advanced-futures
**License:** MIT (see `NOTICE`)

## What's New in v1.7.0

- The plugin has a brain: a graph of pages in `docs/jtbd/`. The save code is `scripts/jtbd_graph.py`.
- `jtbd_graph.py write-run` writes the pages of one run: the job, the steps, the outcomes, the segments, the willingness to pay, and the results. `results` and `pages` read them back.
- `jtbd_graph.py check` is the brain check. The skills that write the pages come in the next version.

## What Was New in v1.6.0

- Three skills replace the three commands: `discover`, `quick-validate` and `wtp-check`.
- The skills ask you the questions. A subagent cannot ask, so the orchestrator writes a questions file and stops. The `discover` skill asks you, then starts the orchestrator again.
- Scripts run with `uv run`. Each script lists its own packages.
- The plugin result file standard, its checker and its tests are in the plugin folder.
- Seven defaults are registered in `result-file.json`. Each default that a run used is named in the result file.

See `CHANGELOG.md` for the full list.

## What the plugin does

- **Structured discovery.** It guides you through JTBD analysis with Outcome-Driven Innovation (ODI).
- **Value in money.** It calculates Economic Value to Customer (EVC).
- **Behavior segments.** It finds groups by what people do, not by demographics.
- **Price check.** A 6-layer framework tests that the price is realistic.
- **Hand-off.** It offers the next skill at the end of a run: `/product:explore`, `/gtm` and `/pricing:price`.

### Methods

1. **Outcome-Driven Innovation (ODI)** finds and ranks customer needs.
2. **Economic Value to Customer (EVC)** measures the value that a customer gets: time, errors, revenue and risk.
3. **Christensen's forces** show why people switch: push, pull, anxiety and habit.
4. **Multi-dimensional segmentation** joins needs, circumstances and behavior.
5. **6-layer WTP validation** checks willingness to pay with statistics, comparisons and economics.

## Requirements

- Claude Code.
- [`uv`](https://docs.astral.sh/uv/) on your path. The plugin scripts run with `uv run`. `uv` installs `pandas`, `numpy` and `scikit-learn` for the scripts that need them.

## Install

```
claude plugin marketplace add ai-advanced-futures/cc-plugins
claude plugin install jtbd-market-discovery@cc-plugins
```

## Skills

| Skill | Use it to | Time |
|---|---|---|
| `/jtbd-market-discovery:discover` | Run the 10 phases, from the job to the validated opportunity | 45 to 90 minutes |
| `/jtbd-market-discovery:quick-validate` | Start at phase 6 when you have survey data | 15 to 30 minutes |
| `/jtbd-market-discovery:wtp-check` | Test one price with the 6-layer framework | 10 to 20 minutes |

### discover

```
/jtbd-market-discovery:discover [--defaults] [market area]
```

The skill asks for the market area and what it needs for each phase. It stops at each checkpoint to show the result. Use `--defaults` to take each default answer and ask nothing.

The 10 phases:

1. Job identification
2. Job decomposition (12 to 15 universal steps)
3. Need generation (80 to 100 needs, 4 agents in parallel)
4. Time-task analysis
5. Survey design (optional)
6. Opportunity scoring (ODI)
7. EVC calculation
8. Segmentation. It runs after phase 7, because it reads the EVC.
9. WTP validation
10. Output generation

To continue a run, start `discover` again. The orchestrator reads `state.json` and starts at the first phase that is not complete.

### quick-validate

Use it when you have a job statement, a needs list and a survey CSV with importance and satisfaction ratings. It imports the data, scores the opportunities, estimates EVC, finds segments and validates the price.

### wtp-check

Use it to test a price. The skill asks for the target price, the segment, the market context (B2B or B2C, competitors), the EVC estimate and the survey data if you have it. If you ran `discover` before, `wtp-check` reads the `p7.json` and `p8.json` of that run.

## When to use it

Use it to explore a new market, to check a product idea, to set a price, to find behavior segments or to rank features by customer value.

Do not use it when you know your market well, when you only change an existing feature, or when you cannot reach customers.

```
Do you have survey data?
├─ YES → /jtbd-market-discovery:quick-validate
└─ NO  → /jtbd-market-discovery:discover

Do you only need to test a price?
└─ /jtbd-market-discovery:wtp-check
```

## How it works

The `discover` skill asks the questions in your conversation. It starts the orchestrator (`agents/orchestrator.md`). The orchestrator starts one fresh agent for each phase. Each agent reads its inputs from disk, writes its output to `.jtbd-market-discovery/<session>/pN.json`, and ends.

- **Small context.** Each phase uses about 5 to 10 thousand tokens. A single agent that does all phases reaches about 143 thousand.
- **Safe state.** The output of each phase is on disk. A run survives a context compaction.
- **Questions.** At a checkpoint the orchestrator writes `questions.json` and ends with `QUESTIONS: <path>`. The skill asks you, writes `answers.json` and starts the orchestrator again.
- **No checkpoints.** A start with no `checkpoints` field never stops.

The state folder `.jtbd-market-discovery/` can hold your survey data. Do not commit it.

Phases 6 to 9 write a helper Python file in the session folder and run it with `uv run`. Claude Code asks you to approve each run.

### Architecture

The C4 diagrams are in [docs/diagrams/jtbd-market-discovery-c4.md](docs/diagrams/jtbd-market-discovery-c4.md).

## Output

Each run writes these files to its session folder:

- `final-output.json` (the full result)
- `p1.json` to `p9.json` (the output of each phase)
- `state.json` (the state of the run)
- an executive summary

Each run also writes one result file, in the shared plugin result shape, to `.jtbd-market-discovery/results/`. A halted run writes it too, with its gaps. [ADR-003](docs/adr/ADR-003-plugin-result-file.md) records the rules.

Example of an opportunity in `final-output.json`:

```json
{
  "opportunity_id": "O001",
  "title": "Minimize coverage gaps during critical periods",
  "scores": { "composite": 87, "odi_score": 82, "financial_score": 91 },
  "segment_id": "S001",
  "evc_monthly": 11513,
  "wtp_validated": 75
}
```

## Documentation

- [ADR-001](docs/adr/ADR-001-jtbd-plugin-architecture.md): plugin architecture
- [ADR-002](docs/adr/ADR-002-orchestrator-architecture.md): orchestrator architecture
- [ADR-003](docs/adr/ADR-003-plugin-result-file.md): the plugin result file
- `references/`: ODI, universal job steps, need generation, EVC, WTP and segmentation guides
- `templates/`: job statement, job steps, survey, forces, time-task and output schema

## Troubleshooting

**The CSV does not parse.** Use commas, not tabs. Check that the column names match: `need_id`, `need_description`, `importance`, `satisfaction`. Put double quotes around text that holds a comma.

```csv
need_id,need_description,importance,satisfaction
N001,"Minimize time to estimate departure time",9.2,3.1
N002,"Reduce likelihood of arriving late",9.5,2.8
```

**WTP validation fails for a price that looks fair.** Compare the price with the EVC. The optimal price is 10 to 30% of the EVC. Read the layer that failed in `p9.json`.

**Segmentation finds no distinct groups.** Use more survey responses, or a different segment count.

**All ODI scores are almost equal.** Check that the satisfaction ratings differ from the importance ratings.

**A script fails to start.** Check that `uv --version` works. Read the error text that `uv run` prints.

**A run takes too long.** Use `quick-validate`, or `discover --defaults`.

## Tests

```
python3 -m pytest plugins/jtbd-market-discovery/tests -q
```

Install `plugins/jtbd-market-discovery/requirements-dev.txt` first.

## License

MIT. The notice of the source plugin is in `NOTICE`.
