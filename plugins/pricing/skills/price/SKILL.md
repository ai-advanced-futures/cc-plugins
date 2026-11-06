---
name: price
description: Compute RIGHT_PRICE for a new feature or offering using a three-path formula — Path A (EVC-validated, when the jtbd gate accepts a jtbd result), Path B (multiplicative estimated, data-poor), or Path C (agentic pricing for Autonomous / Fully Agentic AI features). Applies Amadeo AI_MULTIPLIER, Helmer MOAT_MULTIPLIER, and discriminated output types for each pricing path.
allowed-tools: Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/*), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

# Price — Compute RIGHT_PRICE

Run only this plugin's own scripts, as `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py" ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because the Bash grant covers only the plugin scripts.
Run every agent you dispatch in the foreground and wait for it to finish; never run one in the background (`run_in_background: true`) before the result file is written, because a background run can end before it writes the result file.
This plugin's root is `${CLAUDE_PLUGIN_ROOT}`; wherever a file you read writes `${CLAUDE_PLUGIN_ROOT}`, use that path.

Price a new AI-era or legacy feature using the appropriate path for your data availability and feature type.

## When to Use

- "How should we price this new AI feature?"
- "What should we charge for our document processing API?"
- "Price our new outcome-based offering"
- "What's the right price point for our enterprise tier?"
- "Price this autonomous agent feature"

## Paths

### Path A — Data-Rich (confidence: `validated` only with customer data or published sources)

Activates when the Step 2 gate in `price.md` accepts a jtbd result: with a `plugin-run` block, only the `result_file` its `inputs_from` names, when `run.run_id` and `run.case` match; in a person's run, the newest willingness-to-pay result in `.jtbd-market-discovery/results/`, confirmed by the person, and only when there is none, `.jtbd/wtp-validation.json`. With `automated: true` and no block, Mode Detection skips the confirmation, so the price is Path B and never validated.

```
RIGHT_PRICE = min(WTP_max, max(MARGIN_FLOOR, min(EVC, REFERENCE_PRICE + AI_VALUE_DELTA + MOAT_VALUE_DELTA)))
```

Path A works in the period of the jtbd `willingness_to_pay` result it uses: that is the price's period. With no answered or chosen unit, a Path A price is charged per seat per the price's period; the `pricing_unit` question's default is not an answered unit. When the answers set, or `price.md` Step 7 chooses, a `pricing_unit` whose period differs from the price's period, convert after the cap: pass `price_period` and `unit_period` to `compute_path_a`, which converts the capped price, the headroom and the margin floor by the same rule (×12 from month to year, ÷12 from year to month), and label each figure with that unit; a unit Step 7 chooses after the price is computed means one more `compute_path_a` call with both periods. A `pricing_unit` with any other period is refused: record the gap `{"kind": "launch_price", "label": "Pricing unit", "why": "pricing unit has a period the price cannot take"}` and charge per seat per the price's period. When the calculator exits 1 with `pricing unit has a period the price cannot take`, record the same gap.

### Path B — Data-Poor (confidence: `estimated`)

Activates when no JTBD data:

```
RIGHT_PRICE = max(MARGIN_FLOOR, min(WTP_max, BASE × AI_MULTIPLIER × MOAT_MULTIPLIER))
VALUE_SIGNAL = BASE × AI_MULTIPLIER × MOAT_MULTIPLIER  [unconstrained gap signal]
```

### Path C — Agentic Features

**C-Autonomous** (human-in-the-loop AI):
```
RIGHT_PRICE = max(MARGIN_FLOOR, min(WTP_max_per_task, value_per_task × VALUE_CAPTURE_RATE))
```

**C-Fully Agentic** (autonomous AI, no human review):
```
RIGHT_PRICE = max(MARGIN_FLOOR, min(WTP_max_annual, REPLACEMENT_COST × AUTOMATION_RATE × VALUE_SHARE))
```
Returns `PathCFullyAgenticPriced` or `PathCFullyAgenticReclassified` (discriminated union).

## Flow

1. **Before Step 0** — run `date -u +%Y-%m-%dT%H:%M:%SZ` on its own and keep it as `started_at`, and keep the `version` of `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`. When a `date` call is denied or fails, run `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py" now` on its own and use its output as that time. The result file needs both.
2. **Step 0** — Classify agentic tier (Q1–Q4): route to Path A/B or Path C
3. **Step 1** — Collect inputs for the determined path
4. **Step 2** — Path A gate: the jtbd result in `.jtbd-market-discovery/results/` named by `inputs_from` (or, in a person's run, the newest, confirmed; with none there, `.jtbd/wtp-validation.json`)
5. **Step 2b** — Path A reference price: `alternative_price`, asked only when Path A uses no customer value
6. **Step 3** — Compute with `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/pricing_calculator.py" <function> '<JSON arguments>'` When the script fails to import a package, work the figure out from the formula stated in the command, with no code at all, and end each result's `method` with: Computed by the model from the formula stated in the command; no script ran. With no script, when the margin floor is above WTP_max, write the floor warning yourself, in the calculator's words: Below margin floor: the price is capped at the highest willingness to pay (<WTP_max>), which is below the margin floor (<MARGIN_FLOOR>), so the offering does not clear its margin floor at this willingness to pay.
7. **Step 4** — Apply fear signal checks (accuracy < 0.8 → AI_MULTIPLIER = 1.0)
8. **Step 5** — Compute MOAT_MULTIPLIER (Helmer 7 Powers)
9. **Step 6** — Compute MARGIN_FLOOR
10. **Step 7** — Apply segment_signal when the formula's value is above WTP_max: a market gap in Path B, headroom in Path A
11. **Step 8** — Output `.pricing/pricing-recommendation.json`
12. **Last** — Write a copy of `pricing-recommendation.json` to `.pricing/<started_at as YYYYMMDDTHHMMSSZ>/`; this run placed the offering in no tier, so its result file holds no `package` result. Then write the result file: Read `${CLAUDE_PLUGIN_ROOT}/agents/new-offering-pricer.md` with the Read tool and follow its `## Result file` section, in every run.

## Output

`.pricing/pricing-recommendation.json` — right price, confidence tier, path used, multipliers, optional segment signal, and the floor warning (`floor_advisory`) when a Path A price is capped below its margin floor.

## Cross-References

- **Upstream data:** `/jtbd-market-discovery:discover` → activates Path A
- **Upstream data:** `/competitive-intelligence:analyze` → informs MOAT_MULTIPLIER
- **Next step:** `/pricing:package` — assign RIGHT_PRICE output to tier
- **Full prompt:** See `price.md` in this directory
