---
name: price
description: Compute RIGHT_PRICE for a new feature or offering using a three-path formula — Path A (EVC-validated, when the jtbd gate accepts a jtbd result), Path B (multiplicative estimated, data-poor), or Path C (agentic pricing for Autonomous / Fully Agentic AI features). Applies Amadeo AI_MULTIPLIER, Helmer MOAT_MULTIPLIER, and discriminated output types for each pricing path.
allowed-tools: Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py" *), Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/brain_read.py" *), Bash(uv run "${CLAUDE_PLUGIN_ROOT}/scripts/pricing_calculator.py" *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/brain_read.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/pricing_calculator.py *), Edit(/.pricing/**), Read(//**/skills/price/price.md), Read(//**/agents/new-offering-pricer.md)
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

Activates when the Step 2 gate in `price.md` accepts a jtbd result: with a `plugin-run` block, only the run of the jtbd graph that its `inputs_from` entry names (its `run_id` and the block's `case`); in a person's run, the newest run of the jtbd graph that holds a willingness-to-pay result, confirmed by the person. With `automated: true` and no block, Mode Detection skips only the confirmation question, so the price is Path B and never validated. It skips no script call: the main conversation still runs `brain_read.py wtp`, and the reply names the run that the script found, or its `why`. Only an answer of the person in this run (the answer to the `confirm_jtbd_run` question of `price.md` Step 2, or a reply of the person) confirms a jtbd run. Never write that the person confirmed a run when the person gave no such answer, in a dispatch prompt or in a reply, because a stated confirmation that the person did not give makes a price look validated: a dispatched agent takes no confirmation from its prompt (`price.md` Step 2).

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

1. **Before Step 0** — run `date -u +%Y-%m-%dT%H:%M:%SZ` on its own and keep it as `started_at`. Then run `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py" version` on its own and keep its output as the plugin version. When this call is refused or fails, stop: write no price file and no result file, because the result file must name the version of the plugin, and end the reply with the line `BLOCKED: result_name.py version: <reason>`, where `<reason>` is `refused`, or the exit code and the first line of the message. When a `date` call is denied or fails, run `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/result_name.py" now` on its own and use its output as that time. The result file needs both.
2. **Step 0** — Classify agentic tier (Q1–Q4): route to Path A/B or Path C
3. **Step 1** — Collect inputs for the determined path
4. **Step 2** — Path A gate: the jtbd graph run named by `inputs_from` (or, in a person's run, the newest run with a willingness to pay, confirmed). With no block, run `brain_read.py wtp` first, also with `automated: true`; that mode skips only the confirmation question
5. **Step 2b** — Path A reference price: `alternative_price`, asked only when Path A uses no customer value
6. **Step 3** — Compute with `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/pricing_calculator.py" <function> '<JSON arguments>'` with each `'` in a value written as `'\''`. When the calculator cannot run, stop as `price.md` Step 6 says: compute no figure yourself, write no price file, write the result file with its gap, and end the reply with the line `BLOCKED: pricing calculator <function>: <reason>`.
7. **Step 4** — Apply fear signal checks (accuracy < 0.8 → AI_MULTIPLIER = 1.0)
8. **Step 5** — Compute MOAT_MULTIPLIER (Helmer 7 Powers). With no block, run `brain_read.py moats` first, also with `automated: true` and also when the inputs give the competitors
9. **Step 6** — Compute MARGIN_FLOOR
10. **Step 7** — Apply segment_signal when the formula's value is above WTP_max: a market gap in Path B, headroom in Path A
11. **Step 8** — Output `.pricing/pricing-recommendation.json`
12. **Last** — Write a copy of `pricing-recommendation.json` to `.pricing/<started_at as YYYYMMDDTHHMMSSZ>/`; this run placed the offering in no tier, so its result file holds no `package` result. Then write the result file: Read `${CLAUDE_PLUGIN_ROOT}/agents/new-offering-pricer.md` with the Read tool and follow its `## Result file` section, in every run of `pricing:price`. When the `new-offering-pricer` agent runs this skill, skip this step: that agent writes no result file.

## Output

`.pricing/pricing-recommendation.json` — right price, confidence tier, path used, multipliers, optional segment signal, and the floor warning (`floor_advisory`) when a Path A price is capped below its margin floor.

## Cross-References

- **Upstream data:** `/jtbd-market-discovery:discover` → activates Path A
- **Upstream data:** `/competitive-intelligence:analyze` → informs MOAT_MULTIPLIER
- **Next step:** `/pricing:package` — assign RIGHT_PRICE output to tier
- **Full prompt:** Read `${CLAUDE_SKILL_DIR}/price.md` before you start.
