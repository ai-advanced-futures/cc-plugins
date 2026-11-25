# value-ip

## What's New in v1.4.0

- **feat:** the result of each run is also a graph. `/value-ip:learn` turns the result file in `.value-ip/results/` into pages in `docs/value-ip/`: one Run page, one Differentiator page for each claim that survived the debate, one Verdict page and one Gap page for each result the run did not produce. Each page links to its Run page. The result file stays as it was.
- **feat:** the skills `/value-ip:setup`, `/value-ip:learn` and `/value-ip:ask`, the brain hook, and `knowledge` as a dependency. The graph follows the brain standard of the `knowledge` plugin, so `/knowledge:ask` finds its pages.
- **feat:** a page is a `draft` until a person confirms it. Each page is the judgement of the model (`grade: model`), and no page is called validated.

## What's New in v1.3.1

- **fix:** when the dispatch gives a `ran` list and it is empty, the run stops with a halted result file that names the gap, and does not start the debate (#112)
- **fix:** the runner reads the synthesizer's reply: when the reply says `no result file:` or does not end with a result path, the runner says there is no result file and why; a stop because the result name is taken still writes the handoff, marked halted, with no result file (#113)
- **fix:** the debate coordinator reads and challenges only the frameworks that ran, and all four when no list is given; with guard or challenge it reads the analyses given in the dispatch; the synthesizer reads the same way (#171)
- **test:** an empty `ran` halts; the runner trusts the synthesizer's reply; the coordinator and the synthesizer work only on `ran`, or on all four with no list

## What's New in v1.3.0

- **The shared result file.** Every `/value-ip:analyze` run, a person's run too, writes one file to `.value-ip/results/`: one `differentiator` per IP claim that survived the debate and one `right_to_win` from the verdict. Each is the debate's judgement, names the frameworks behind it, and is never called validated. A skipped framework is listed as a gap.
- **A route for a coach.** `agents/analyze-runner.md` runs the command when another session dispatches it with a `plugin-run` block. The block's `automated: true` wins over `auto_mode`.
- **Mission-control.** `release.json` now declares the integration block. The run writes `.value-ip/value-ip-handoff.json` and ends with `DONE: value-ip`.
- **Questions.** `questions/analyze.json` lists the one input, the artifact. With no artifact named, the run auto-detects one and marks the result as resting on that default.
- **Fixes.** The config, lens and method files are read by their full plugin paths, so an installed plugin finds them.
- **Running code and honest sources.** Every file a person's run follows says to run only the plugin's own scripts, one per Bash call, with no inline code, and the command grants only those scripts. The result file name comes from `scripts/result_name.py`. A picked default, or a value taken from another file, is marked as a default. A person's run keeps its work in its own `.value-ip/` folder and asks for its artifact. A denied `date` call falls back to `scripts/result_name.py now` for the time.
- **fix:** a debate round is one questions-and-responses pass; the coordinator runs at least 2 and writes `debate_rounds: <N>`, counting its `round-N-responses.md` files, and the command keeps that number for the partial-status gate.

> **Find what's truly yours — before your competitors do.**

Multi-agent debate system for detecting true value differentiation and IP claims from any artifact — plans, PRDs, code, competitive analyses, or M&A due diligence documents.

## What It Does

Given any artifact, this plugin answers one question: **does this contain genuine, defensible differentiating value — and if so, what exactly is the IP?**

Four framework lens agents analyze the artifact independently, a debate coordinator runs Socratic challenges, and a synthesizer produces a **dual output**: a structured Value & IP Scorecard and a Devil's Advocate Report.

## Frameworks Used

| Framework | Author | Focus |
|-----------|--------|-------|
| **Helmer's 7 Powers** | Hamilton Helmer | Structural competitive barriers |
| **Blue Ocean ERRC** | Kim & Mauborgne | New value curve creation |
| **Disruption Theory** | Clayton Christensen | Disruptive vs. sustaining innovation |
| **Core vs. Context** | Geoffrey Moore | True differentiation vs. commodity |

## Commands

```bash
/value-ip:analyze    # Full multi-agent debate — produces scorecard + devil's advocate
/value-ip:challenge  # Quick devil's advocate — challenge value claims fast
/value-ip:guard      # Proactive guardian — GREEN/YELLOW/RED verdict before completing work
```

## Auto Mode (YOLO)

For automated pipelines, mission-control team contexts, or any case where the plugin should run without human input.

**Activation:** Set `"auto_mode": true` in `plugins/value-ip/config/pipeline-defaults.json`:

```json
{
  "auto_mode": true,
  "auto_answers": {
    "artifact_selection": "auto-detect",
    "multiple_artifacts_policy": "ask",
    "continue_rounds_policy": "stop_if_no_tensions",
    "framework_failure_policy": "skip_and_continue",
    "commit_output": false,
    "output_format": "both"
  },
  "pipeline": {
    "max_rounds": 4,
    "min_rounds": 2
  }
}
```

**Behavior in auto mode:**
- `/value-ip:analyze` — skips artifact selection prompt; auto-detects from conversation context. Skips commit question at end.
- `/value-ip:challenge` — skips artifact prompt; uses whatever is in context.
- `/value-ip:guard` — skips "what are you building?" prompt; infers from context.

**Pipeline state:** All commands write `.value-ip-state.json` at each phase transition (INIT → FRAMEWORK_ANALYSIS → DEBATE → SYNTHESIS → COMPLETE). If context is compacted mid-run, the orchestrating agent can read this file to resume from the correct phase. The state file is gitignored — it is ephemeral runtime state.

**Reset to interactive mode:** Set `"auto_mode": false` (or delete `pipeline-defaults.json`) to restore all prompts.

## Output

### Value & IP Scorecard
```
# Value & IP Analysis — [Artifact Name]

## FRAMEWORK VERDICTS
| Framework | Score (1-5) | Structural Power Found | Notes |
...

## IP CLAIMS (True Differentiators)
1. **[Name]** — [description]
   - Helmer power: [power]
   - Blue Ocean: [value created]
   - Disruption type: [type]
   - Core vs. context: CORE — protectable

## OVERALL VERDICT
- TRUE DIFFERENTIATORS: N
- RECOMMENDATION: PASS | CONDITIONAL | FAIL
```

### Devil's Advocate Report
```
## DEVIL'S ADVOCATE CHALLENGES
### Challenge 1 — [Agent]
"[Specific challenge the team must answer]"
- [ ] Team response: _______________
```

## The graph

`scripts/vip_graph.py` is the save code of the graph. Each write goes through it.

| Command | What it does |
|---|---|
| `init`, `upgrade` | Make the bundle `docs/value-ip/` and its registry entry in `.claude/knowledge.json`, or bring it to the standard. |
| `ingest <result file>` | Make the pages of one result file. It refuses a file that is already in the graph, a file outside the project, and a result with no `model` source. |
| `verify-run <run> --by human:<login>` | A person confirms a run: its pages get `status: stable` and a `verified` entry. |
| `pending` | List the result files of `.value-ip/results/` and the Run page that holds each, or `null`. |
| `results [--run <run>]` | Print one run, the latest by `started_at` by default, as JSON: the run, its differentiators, its verdicts and its gaps. |
| `regen`, `check`, `log`, `new`, `set`, `link`, `unlink`, `remove`, `resolve` | The operations of the brain standard. |

Page types: `Run` (RUN), `Differentiator` (DIFF), `Verdict` (VERDICT) and `Gap` (GAP). The edge `run` points from each page to its Run page. The brain check has the rules `VIP-schema`, `VIP-id`, `VIP-link`, `VIP-required`, `VIP-run` (a result file is on one Run page), `VIP-verified` (a `stable` page has a `verified` entry of a person) and `VIP-stale`. The hook runs `regen`, the brain check and the general check of `knowledge` after each write.

Another plugin reads the graph with `vip_graph.py results`, or through `/knowledge:ask`. ADR-003 gives the reasons for the design.

## Works With

This plugin integrates with outputs from:
- `competitive-intelligence` — ecosystem maps and competitive lens analyses
- `pricing` — EVC data and feature classification
- `corporate-development` — M&A due diligence (IP valuation for deals)
- `product-finance` — financial models and ROI analyses
- `prd`, `tech-budget`, `thinktank`, `superpowers`

## Installation

Install it with `claude plugin install value-ip@cc-plugins`. After installation:

```bash
/value-ip:analyze    # Start here
```

## Contributing

Contributions welcome. The plugin follows the [engineering standards](../../../../CLAUDE.md).

### Structure

```
plugins/value-ip/
├── .claude-plugin/
│   ├── plugin.json           # Plugin metadata and version
│   └── release.json          # webCompatible flag, test command, package excludes
├── hooks/                    # The brain hook: regen and both checks after a write to the graph
├── schema/                   # value-ip.yaml (LinkML) and the generated JSON Schema and slots
├── templates/                # The router block that setup writes into CLAUDE.md
├── agents/                   # Six debate agents (helmer, blue-ocean, christensen, moore, debate-coordinator, synthesizer)
├── commands/                 # Three commands (analyze.md, challenge.md, guard.md)
├── config/
│   └── pipeline-defaults.json  # Auto mode config (set auto_mode: true for YOLO)
├── docs/
│   └── adr/
│       └── ADR-001-value-ip-plugin-architecture.md  # Architecture decisions
├── scripts/                  # Python support scripts (artifact_detector, ip_extractor, scorecard_generator, pipeline_state, etc.), the save code vip_graph.py and its modules in viplib/
├── skills/
│   ├── setup/, learn/, ask/      # The graph skills
│   ├── ip-extraction/SKILL.md    # IP claim extraction methodology
│   └── lenses/               # Four framework SKILL.md files
├── tests/                    # pytest test suite (55 tests)
├── SKILL.md                  # Root plugin skill (auto-activation triggers)
└── README.md                 # This file
```

### Development Setup

```bash
# From plugins/value-ip: install the test dependencies
uv pip install -r requirements-dev.txt -r ../knowledge/requirements-dev.txt

# Run the tests
VALUE_IP_REQUIRE_LINKML=1 pytest tests/ -q -rs

# CI fails the step when a test skips
```

### Adding a Framework Lens

1. Create `skills/lenses/<name>/SKILL.md` — defines the analytical framework
2. Create `agents/<name>-agent.md` — dispatch instructions for the lens agent
3. Add the agent to the dispatch list in `commands/analyze.md`
4. Update `ip_extractor.py` if the new lens contributes to IP claim scoring
5. Update `scripts/frameworks.py` with any new data structures
6. Add tests in `tests/`

### Architecture

See [`docs/adr/ADR-001-value-ip-plugin-architecture.md`](docs/adr/ADR-001-value-ip-plugin-architecture.md) for full architecture decisions, C4 diagrams, and rationale for all major design choices.

### Submitting Changes

1. Create a feature branch from `main`
2. Write tests first (TDD) — `pytest tests/ -q` from `plugins/value-ip`
3. Update `plugin.json` version (patch/minor/major per semver)
4. Update `marketplace.json` description if behavior changes
5. Update `ADR-001` if architectural decisions change
6. Open a PR against `main` with descriptive title and summary

## License

The Apache License 2.0 of this repository covers the plugin. The MIT notice of the ported code is in [NOTICE](NOTICE).
