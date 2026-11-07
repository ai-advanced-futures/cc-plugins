# pricing

Pricing for AI-era software products. The plugin finds the right price for one offering. It also checks the prices of existing features and designs Good/Better/Best tiers.

The plugin tells AI-era offerings (value grows with the speed and accuracy of the outcome) from legacy features (value stays the same or falls). It prices each kind in its own way.

The version of the plugin is in `.claude-plugin/plugin.json`. The changes are in [CHANGELOG.md](CHANGELOG.md).

## Install

```bash
claude plugin marketplace add ai-advanced-futures/cc-plugins
claude plugin install pricing@cc-plugins
```

## Skills

Run each skill as `/pricing:<skill>`.

| Skill | Use it to | Output |
|---|---|---|
| `value-metric` | Choose the pricing axis (Campbell's 3 criteria and the AI-era test) | `.pricing/value-metric.json` |
| `audit` | Classify features as AI-era, Hybrid or Legacy; find the Ramanujam failure modes | `.pricing/audit-report.md`, `.pricing/audit-data.json` |
| `price` | Compute RIGHT_PRICE (Path A, Path B or Path C) | `.pricing/pricing-recommendation.json` |
| `package` | Design Good/Better/Best tiers and the free-tier gate | `.pricing/packaging-architecture.json` |
| `cost-amplifier-diagnostic` | Compute the cost of an agentic offering with its 8 cost amplifiers | cost readout (internal) |
| `value-metric-tree-walk` | Walk the value-metric tree from the success mode to a terminal node | tree result |
| `pattern-selection-agentic` | Choose pricing patterns for an agentic offering | pattern selection |
| `sensitivity-stress` | Test the price against the 5 stress cases | sensitivity matrix |

The 4 last skills run in the Phase 1 Insight workflow of the `agentic-pricing-strategist` agent.

## Agents

| Agent | Use it to |
|---|---|
| `pricing-auditor` | Audit the pricing of an existing product and write an executive report |
| `new-offering-pricer` | Price a new feature or offering, from the outcome to the final price and tiers |
| `agentic-pricing-strategist` | Run the Phase 1 Insight workflow: diagnose the offering, walk the value-metric tree, write 3 handoff files |
| `price-runner` | Run the `price` skill and place the offering in the tiers, when another plugin or session dispatches it |

### Agents run as subagents

An agent runs as a subagent. It cannot ask the person. It takes each answer from the dispatch fields. When a required field is missing, the agent writes `.pricing/open-questions.json` and ends with `DONE: pricing OPEN: .pricing/open-questions.json`.

| Agent | Required dispatch fields |
|---|---|
| `agentic-pricing-strategist` | `portco_arr_band`, `archetype_hints`, `current_pricing_model` |
| `new-offering-pricer` | `offering` |
| `pricing-auditor` | `feature_list` |

A dispatch with no `plugin-run` block can give `jtbd_result`: the path of the jtbd result to use, a file under `.pricing/`. The caller writes it with `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/brain_read.py" wtp --root <git root> --out <run folder>/upstream`.

The file has this shape:

```json
{"agent": "new-offering-pricer", "questions": [{"input": "offering", "question": "What does the offering do?"}]}
```

The `price-runner` agent keeps its halt: when an input is missing, it stops and writes the gap in the result file.

## The price skill

### Path A (data-rich)

Path A starts when the price gate accepts a jtbd result from the jtbd graph. The plugin reads the graph with `scripts/brain_read.py`, which calls the save script of the `jtbd-market-discovery` plugin.

```
EVC = Reference_Price + Differentiation_Value
RIGHT_PRICE = min(WTP_max, max(MARGIN_FLOOR, min(EVC, REFERENCE_PRICE + AI_VALUE_DELTA + MOAT_VALUE_DELTA)))
confidence_tier: "validated" with customer data or published sources, else "estimated"
```

`EVC` is the customer value. It bounds the formula, and WTP_max caps the price.

Path A works in the period of the jtbd `willingness_to_pay` result it uses: that is the price's period. With no answered or chosen unit, a Path A price is charged per seat per the price's period; the `pricing_unit` question's default is not an answered unit. When the answers set, or `price.md` Step 7 chooses, a `pricing_unit` whose period differs from the price's period, convert after the cap: pass `price_period` and `unit_period` to `compute_path_a`, which converts the capped price, the headroom and the margin floor by the same rule (×12 from month to year, ÷12 from year to month), and label each figure with that unit; a unit Step 7 chooses after the price is computed means one more `compute_path_a` call with both periods. A `pricing_unit` with any other period is refused: record the gap `{"kind": "launch_price", "label": "Pricing unit", "why": "pricing unit has a period the price cannot take"}` and charge per seat per the price's period. When the calculator exits 1 with `pricing unit has a period the price cannot take`, record the same gap.

### Path B (data-poor, estimated)

Path B starts when no jtbd data is accepted.

```
RIGHT_PRICE  = max(MARGIN_FLOOR, min(WTP_max, BASE × AI_MULTIPLIER × MOAT_MULTIPLIER))
VALUE_SIGNAL = BASE × AI_MULTIPLIER × MOAT_MULTIPLIER   (no limit: shows the gap)
confidence_tier: "estimated"
```

An automated run with no jtbd data uses Path B. Its price is never "validated".

### Path C (agentic offerings)

Autonomous (a person checks each task, per-task price):

```
value_per_task = time_saved_per_task × hourly_cost_of_human
RIGHT_PRICE    = max(MARGIN_FLOOR, min(WTP_max_per_task, value_per_task × value_capture_rate))
```

Fully agentic (per-agent-per-year price):

```
replacement_cost = annual_salary × (1 + overhead_rate)
RIGHT_PRICE      = max(MARGIN_FLOOR, min(WTP_max_annual, replacement_cost × automation_rate × value_share))
```

When `automation_rate` is below the threshold, the result is reclassified to Autonomous and lists `recovery_inputs_required`.

### Terms

- `AI_MULTIPLIER = 1.0 + (speed_improvement × accuracy_improvement)`. `speed_improvement` is a ratio (4.0 = 4 times faster than the manual way). `accuracy_improvement` is a fraction from 0 to 1. Below 0.8, `AI_MULTIPLIER` is 1.0.
- `MOAT_MULTIPLIER` is the Helmer 7 Powers score, from 1.0 to 2.5. A Scale Economy moat locks it at 1.0 and adds a penetration-pricing advisory.
- `MARGIN_FLOOR = PRODUCTION_COST / (1 − target_margin)`.

The calculations run in `scripts/pricing_calculator.py`. The skill runs it with `uv run`:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/pricing_calculator.py" <function> '<JSON object of arguments>'
```

Write each `'` in a value as `'\''`.

When the calculator cannot run, the run stops and computes no figure: see `skills/price/price.md` Step 6.

## Classification of features

Layer 1 scores 5 questions, 0 or 1 each:

1. The feature uses machine-learning inference to deliver its value.
2. The quality improves as the feature collects data or use.
3. The outcome is faster than the manual or non-AI way.
4. The AI is a direct cause of the value.
5. The AI capability is rare among competitors.

Score 0–2 is **Legacy**. Score 3–4 is **Hybrid**. Score 5 is **AI-era** (not final until Layer 2).

Layer 2 applies only when `AI_MULTIPLIER` is above 5. All 3 must be true: autonomy, compounding, attribution. If one is false, `AI_MULTIPLIER` is capped at 5.

The review window is `36 / log₂(1 + competitor_count)` months, from 6 to 36.

## Input from other plugins

| Plugin | Role | Data |
|---|---|---|
| `jtbd-market-discovery` | Upstream | Reads the willingness-to-pay result of the jtbd graph (`brain_read.py wtp`) → activates Path A |
| `jtbd-market-discovery` | Upstream | Reads the outcome scores of the jtbd graph (`brain_read.py outcomes`): tier placement and audit context |
| `competitive-intelligence` | Upstream | Reads the competitor moats of the competitive-intelligence graph (`brain_read.py moats`) |
| `product-finance` | Downstream | Reads `.pricing/pricing-recommendation.json` for margin and LTV work |

A plugin run reads only the jtbd run that its `inputs_from` field names. A person's run takes the newest run that holds a willingness to pay and asks the person to confirm it. When a graph is not there, pricing shows a plain message and goes on with no input.

### SessionStart hook

`hooks/hooks.json` registers one `SessionStart` hook. At the start of a session it looks for the files above and tells you which ones it found. It only reads files and never blocks the session.

## Files in `.pricing/`

```
.pricing/
├── audit-report.md              audit report for people
├── audit-data.json              audit data for tools
├── new-offering-price.md        price report for people
├── new-offering-data.json       new-offering data for tools
├── pricing-recommendation.json  price output
├── value-metric.json            pricing axis
├── packaging-architecture.json  tiers and free-tier gate
├── open-questions.json          questions an agent could not ask (see above)
└── results/                     one result file for each run of the price skill
```

`pricing-recommendation.json`:

```json
{
  "right_price": 0.0,
  "confidence_tier": "validated | estimated",
  "price_path": "A | B | C-autonomous | C-fully-agentic",
  "agentic_tier": "commodity | augmented | autonomous | fully_agentic | null",
  "pricing_unit": "string",
  "value_signal": 0.0,
  "segment_signal": { "wtf_gap": 0.0, "interpretation": "string" },
  "moat_advisory": "string | null",
  "floor_advisory": "string | null",
  "risk_advisory": "string | null"
}
```

| Field | Meaning |
|---|---|
| `segment_signal` | Path B: the gap between VALUE_SIGNAL and WTP_max → recommendation to run JTBD. Path A: headroom above WTP_max, not a market gap |
| `floor_advisory` | A warning when the margin floor is above WTP_max |
| `moat_advisory` | A note when a Scale Economy moat is present |

## Development

Run the tests from the plugin folder:

```bash
cd plugins/pricing
uv run --with-requirements requirements-dev.txt python -m pytest tests -q
```

## Frameworks

- **Luis F. Amadeo**: VALUE = Speed × Accuracy of Outcome
- **Madhavan Ramanujam**, *Monetizing Innovation*: Killer/Leader/Filler, Good/Better/Best
- **Patrick Campbell / ProfitWell**: value-metric criteria, per-user antipattern
- **Hamilton Helmer**, *7 Powers*: moat multiplier, Scale Economy advisory
- **Tony Ulwick**, Outcome-Driven Innovation: EVC and Path A

Equations, the Fear/Love model and worked examples are in [FRAMEWORKS.md](FRAMEWORKS.md). The source of the Agentic Pricing Framework is in [ATTRIBUTION.md](ATTRIBUTION.md).
