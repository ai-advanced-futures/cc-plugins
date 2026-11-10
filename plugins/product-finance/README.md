# Product Finance Plugin

Financial analysis for product teams: SaaS metrics, AI economics, market sizing, instrumentation plans, and a cost-coverage readout. The version is in `.claude-plugin/plugin.json`. The changes of each version are in `CHANGELOG.md`.

## Overview

**Financial Intelligence as Code.** The plugin puts CFO-level analysis in the work of a product team: CAC, LTV, margins, Rule of 40, the ROI of AI features, and the plan to measure them. Each formula is in a Python script, so the figures are exact. The documentation index is `docs/INDEX.md`.

Who gets what:

- **Product teams** check the ROI of a feature before they build it.
- **Engineering leaders** see the cost of a feature while they build it.
- **CFOs** get the financial health of a product on request.

The plugin has three tiers: commands ask the questions, agents do the analysis, and skills hold the method for one metric.

## Quick Start

Install the plugin from the marketplace of this repository:

```
/plugin install product-finance@cc-plugins
```

Then set up the baseline assumptions, and run an analysis:

```
/product-finance:setup
/product-finance:health-check
/product-finance:ai-economics
/product-finance:unit-economics
```

All `.product-finance/` paths are under the git root. Run `git rev-parse --show-toplevel` to find it.

## Configuration

Run `/product-finance:setup` to write the baseline assumptions. The plugin writes its files under `.product-finance/`, at the git root. You can change the baseline assumptions and the KPI thresholds for each engagement.

To run a command with no questions, copy `templates/auto-config.template.json` to `.product-finance/auto-config.json` and set `enabled` to `true`. The command then reads each answer from that file.

## Commands Reference

| Goal | Use |
|------|-----|
| Size a market | `/product-finance:discover` |
| Write the baseline assumptions | `/product-finance:setup` |
| ROI of a feature | `/product-finance:feature-roi` |
| Cost and ROI of AI | `/product-finance:ai-economics` |
| CAC, LTV, payback | `/product-finance:unit-economics` |
| Financial health and benchmarks | `/product-finance:health-check` |
| Gaps in financial tracking | `/product-finance:instrumentation` |
| A model for a services business | `/product-finance:services-model` |
| The cost-coverage readout | `/product-finance:cost-coverage` |

### Discovery and analysis

#### `/product-finance:discover`
Market sizing and opportunity assessment. It reads the jtbd graph of the jtbd-market-discovery plugin for market data.

**Use when:** you start a product or feature and need the size of the opportunity.

**Outputs:** TAM, SAM and SOM, revenue opportunity, CAC estimates by channel, and a market sizing report.

#### `/product-finance:setup`
Guided collection of the baseline financial assumptions.

**Use when:** you use the plugin for the first time.

**Collects:** the pricing model, the team costs, the current metrics, and the market assumptions.

**Outputs:** `.product-finance/assumptions.json`

### Strategic planning

#### `/product-finance:feature-roi`
ROI of a feature or an initiative.

**Use when:** you rank features or check an investment.

**Analyzes:** the build cost, the revenue impact, the payback period, and the NPV.

#### `/product-finance:ai-economics`
Cost and ROI of AI features.

**Use when:** you build an AI feature and must show the investment to a CFO.

**Tracks:** AI cost for each interaction and user, AI cost as a share of revenue, the cost trend, and the value of the AI capability.

**Calculates:** AI ROI = (AI-enabled value − AI costs) / AI costs, break-even, and optimization options.

### Operations and monitoring

#### `/product-finance:unit-economics`
Unit economics and their health.

**Calculates:** CAC, LTV, the LTV:CAC ratio (target: 3:1 or better), the CAC payback period, the Magic Number, and cohorts.

#### `/product-finance:health-check`
Financial health with board-level KPIs.

**Use when:** you prepare a board review, a quarterly review, or an investor update.

**Assesses:** Rule of 40 (revenue growth % + EBITDA margin % of 40 or more), the unit economics, retention and expansion, efficiency ratios, and benchmarks.

### Implementation and instrumentation

#### `/product-finance:instrumentation`
A plan to track financial data.

**Use when:** you build a product or fix a gap in financial data.

**Generates:** event schemas (`subscription_created`, `feature_used`, `ai_request_completed`), database migrations, code templates for events, and API endpoint specifications.

### Services modeling

#### `/product-finance:services-model`
A financial model for a consulting or professional services business: utilization, capacity, pipeline math, break-even, hiring triggers, and scenarios.

**Use when:** capacity, not subscription, limits your business.

### Cost coverage

#### `/product-finance:cost-coverage`
The `cost-coverage-readout` of the agentic pricing Charter (audience: internal). It combines the diagnosis and the cost-amplifier readout of the pricing plugin with the financials of the company.

**Inputs:**
- `diagnosis_path`: the file `agentic-pricing-diagnosis.json` of the pricing plugin
- `amplifier_path`: the file `cost-amplifier-readout.json` of the pricing plugin (its audience must be `internal`)
- `gm_pct`, `nrr_delta_pct`, `forecast_variance_pct`: financial metrics of the company
- `cost_per_interaction_baseline`, `headline_price`: both must be more than 0
- `engagement_id` (UUID) and `produced_at` (RFC 3339)

**Computes:** the S1-S5 sensitivity matrix, the Y1, Y2 and Y3 gross margin path, and the multiple-compression signals.

**Outputs:** `.product-finance/{engagement_id}/cost-coverage-readout.json`, checked against the Charter schema in `schemas/agentic-pricing/`.

## Charter Federation

The plugin takes part in the agentic pricing Charter:

| Schema | Role | Other side |
|---|---|---|
| `cost-coverage-readout` | produces (audience: internal) | a reader of the readout |
| `cost-amplifier-readout` | consumes | the pricing plugin |

The file `.charter-conforms` states this. ADR-002 gives the decision to compute the math in this plugin, with no import from the pricing plugin.

## Result File

Five commands write a result file for other plugins: `discover`, `feature-roi`, `unit-economics`, `ai-economics` and `cost-coverage`. Each run writes one file to `.product-finance/results/`, also a run that halts or is partial. The plugin has one runner for each command, `agents/<command>-runner.md`. A runner asks the person nothing. It takes the answers from the `plugin-run` block of its dispatch. The session that dispatches a runner must give the grants in [Grants that a caller must give](#grants-that-a-caller-must-give). ADR-006 gives the decisions.

## Grants that a caller must give

A plugin run of this plugin gets no permission from its own tools list. The session that starts it must give these grants, or a run in the default mode refuses the calls and writes no result. `<plugin root>` is the absolute path of the install folder of this plugin. `<answers path>` is the file that the `plugin-run` block names, and it needs a grant only when it is outside the project. Each is an absolute path, so a rule has 2 slashes, for example `Read(//srv/plugins/pricing/**)`. `caller-grants.json` holds the same list.

<!-- caller-grants:start -->
```
Bash(uv run <plugin root>/scripts/ai_roi_calculator.py*)
Bash(uv run "<plugin root>/scripts/ai_roi_calculator.py*)
Bash(uv run <plugin root>/scripts/jtbd_read.py*)
Bash(uv run "<plugin root>/scripts/jtbd_read.py*)
Bash(uv run <plugin root>/scripts/market_sizing_calculator.py*)
Bash(uv run "<plugin root>/scripts/market_sizing_calculator.py*)
Bash(uv run <plugin root>/scripts/plugin_result/plugin_result_check.py*)
Bash(uv run "<plugin root>/scripts/plugin_result/plugin_result_check.py*)
Bash(uv run <plugin root>/scripts/result_name.py*)
Bash(uv run "<plugin root>/scripts/result_name.py*)
Edit(/.product-finance/**)
Read(/<plugin root>/**)
Read(/<answers path>)
```
<!-- caller-grants:end -->

## Integration

### With the jtbd-market-discovery plugin

Run the jtbd-market-discovery plugin first. Then run `/product-finance:discover`. The command reads the jtbd graph of the project through `scripts/jtbd_read.py`, and writes the run it reads into `.product-finance/upstream/`. `scripts/probe-plugin.sh` finds the jtbd plugin. It is a byte copy of the same file in the other plugins, and it changes only with them. When the project has no jtbd plugin, no jtbd graph, or no fitting run, the command shows a `NO-JTBD:` line and sizes the market from your answers.

### Alone

The plugin works with no other plugin. A person can give the input to each command.

## Board-Level KPIs

- **Growth:** ARR, MRR, revenue growth rate, new, expansion and churned ARR
- **Profitability:** EBITDA margin, gross margin, contribution margin, Rule of 40
- **Unit economics:** CAC, LTV, LTV:CAC, CAC payback, Magic Number
- **Retention:** NRR, GRR, logo retention, churn, expansion revenue
- **AI:** cost for each interaction, cost as a share of revenue, AI-enabled revenue, AI ROI

`docs/KPI_DEFINITIONS.md` defines each one.

## Data Model

The plugin keeps its state in `.product-finance/`:

```
.product-finance/
  ├── assumptions.json     # Financial assumptions and inputs
  ├── metrics.json         # Current financial metrics
  ├── auto-config.json     # Answers for a run with no person present
  ├── reports/             # One report for each command run
  ├── results/             # The result files
  └── instrumentation-plan.json
```

## Requirements

- **uv.** The plugin runs each script with `uv run`. `uv` reads the block at the top of the script and installs its packages.
- **Python:** 3.11 or later.
- **Packages:** `unit_economics.py`, `rule_of_40.py`, `instrumentation_analyzer.py` and `cost_coverage_readout.py` need `pydantic`. The other scripts need only the standard library.

## Development

The test files are in `tests/`. They need the packages in `requirements-dev.txt`:

```
pip install -r requirements-dev.txt
pytest tests/ -q -rs
```

The suite must show no skipped test.

## Documentation

- **Index:** `docs/INDEX.md`
- **Methodology:** `docs/METHODOLOGY.md`
- **KPI definitions:** `docs/KPI_DEFINITIONS.md`
- **Integration guide:** `docs/INTEGRATION_GUIDE.md`
- **Decisions:** `docs/adr/`
- **Diagram:** `docs/diagrams/product-finance-c4-context.md`

## Examples

- `examples/saas-product-analysis/`: a full product analysis
- `examples/ai-feature-roi/`: the ROI of an AI feature
- `examples/instrumentation-plan/`: an instrumentation plan

## Sources

The method uses published SaaS frameworks: Rule of 40 (Brad Feld), SaaS metrics (Ben Murray), LTV:CAC and growth benchmarks (Tomasz Tunguz), the SaaS playbook (David Skok), and industry benchmarks (McKinsey & Company, SaaS Capital).

## License

The license of the repository applies. See `NOTICE` for the origin of the plugin.
