---
name: price
description: Price a new feature or offering using a dual-path formula (Path A EVC additive when JTBD data exists, Path B multiplicative when data-poor). Applies Amadeo AI_MULTIPLIER, Helmer MOAT_MULTIPLIER, and adversarial competitive-reference MOAT elicitation.
model: sonnet
tools: Read(*), Write(*), Bash(*), Skill(*), AskUserQuestion(*)
---

# Price Skill

Run only this plugin's own scripts, as `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py" ...`, one command per Bash call. Never run inline code in any language (`python3 -c`, `python3 -`, `ruby -e`, `node -e`, a heredoc), never write a script of your own and run it, and write every file with the Write tool, never with a shell command, because the Bash grant covers only the plugin scripts.
Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them", because a person cannot pick a value from such an option.

## Purpose

Guide through an outcome-based pricing process for a new feature or offering using:
- JTBD opportunity scores + WTP (when available)
- Amadeo VALUE = Speed × Accuracy formula
- Helmer 7 Powers moat assessment (adversarial — requires competitive reference)
- Campbell value metric alignment check

**Primary Persona:** Seed-to-Series B product manager in a data-partial state.

## Trigger Phrases

`how should we price this`, `price this feature`, `new offering pricing`,
`what should we charge`, `pricing a new product`, `set the price`

## Inputs

- Feature/offering description
- Target segment
- JTBD opportunity score (optional — from `jtbd-market-discovery`)
- Competitive data (optional — from `competitive-intelligence`)

## Outputs

- RIGHT_PRICE recommendation with confidence_tier ("validated" or "estimated")
- VALUE_SIGNAL (Path B: unconstrained; Path A: the price before the WTP_max cap, whose excess over the price is headroom)
- segment_signal (when the formula's value exceeds WTP_max: a market gap in Path B, headroom in Path A)
- moat_advisory (when Scale Economy moat detected)
- Pricing model recommendation (Campbell value metric check)

---

## Variable Sourcing Table

| Variable | Source (Priority Order) | Fallback |
|---|---|---|
| BASE_PRICE | Step 4: midpoint(bargain_price, expensive_price) | Required; no default |
| WTP_max | Step 4: expensive_price threshold (customer's "too expensive" answer) | Required; no default |
| AI_MULTIPLIER inputs | User-stated speed/accuracy improvements | 1.0 (no AI premium) |
| MOAT_MULTIPLIER | Adversarial Socratic dialogue (requires competitor reference) | 1.0 + "unvalidated" flag |
| PRODUCTION_COST | `product-finance` query → user input | 0 (flagged as "margin floor unchecked") |
| target_margin | `config/defaults.json` → user input | 0.7 (in config) |
| value_capture_rate | `config/defaults.json` → user input | 0.30 (in config) |
| overhead_rate | `config/defaults.json` → user input | 0.30 (in config) |
| value_share | `config/defaults.json` → user input | 0.40 (in config) |
| AI_VALUE_DELTA (Path A) | EVC minus REFERENCE_PRICE, both in the price's period, when the accepted jtbd file has a `customer_value` result | 0 (no AI value counted) |
| MOAT_VALUE_DELTA (Path A) | Step 5 moat elicitation (requires competitor reference) | 0 when no competitor is named |
| EVC (Path A) | the `customer_value` result of the accepted jtbd file, converted to the price's period | WTP_max when the file has no `customer_value` |
| REFERENCE_PRICE (Path A) | Step 2b: the `alternative_price` answer, asked only when Path A uses no customer value | WTP_max |
| WTP_max (Path A) | the jtbd `willingness_to_pay` result for the offering's segment, in its own period, which is the price's period | its `high`, else its `point`, else its `low` |
| PRICING_UNIT (Paths A and B) | Step 7: the value metric the `value-metric` skill chose | per seat per the price's period in Path A; per seat per month in Path B |

---

## Pricing Formula — Dual-Path Architecture

### Branch Check (Step 2)

- **Path A** activated when: the Step 2 gate accepts a jtbd result from `.jtbd-market-discovery/results/` (in a person's run with none there, finds `.jtbd/wtp-validation.json`) → `confidence_tier` as the Step 2 grade rule sets it
- **Path B** activated when: the gate accepts no jtbd data → `confidence_tier: "estimated"`
  - User-stated value estimates (without JTBD file) use Path B. Self-reported values stay
    "estimated", because no customer data backs them.

---

### Path A — Data-Rich (confidence_tier: "validated" or "estimated", Step 2)

```
EVC = Reference_Price + Differentiation_Value
VALUE_SIGNAL = max(MARGIN_FLOOR, min(EVC, REFERENCE_PRICE + AI_VALUE_DELTA + MOAT_VALUE_DELTA))  [the price before the cap]
RIGHT_PRICE = min(WTP_max, max(MARGIN_FLOOR, min(EVC, REFERENCE_PRICE + AI_VALUE_DELTA + MOAT_VALUE_DELTA)))
```

When the margin floor is above WTP_max, the price is still WTP_max, and the calculator's `floor_advisory` says the offering does not clear its margin floor at this willingness to pay; show that warning with the price.

Where:
- `Reference_Price` = customer's next-best alternative price (the person's answer; in Path A, WTP_max when none is given)
- `AI_VALUE_DELTA` = currency value of AI-driven improvement: EVC minus `Reference_Price` when the accepted file in `.jtbd-market-discovery/results/` has a `customer_value` result (in the old-folder fallback, from `.jtbd/evc-analysis.json` when it states a `period`)
- `WTP_max` = the willingness to pay jtbd measured for the offering's segment: the result whose `segment` matches the `segment` answer, else the file's only result; with several and no match, the highest across them, each converted to `month` first (a `year` value ÷12), in the period of the result taken. It caps the price
- `MOAT_VALUE_DELTA` = currency value of moat-based differentiation
- `EVC` = the customer value: it bounds the formula, and WTP_max caps the price

---

### Path B — Data-Poor (confidence_tier: "estimated")

```
RIGHT_PRICE = max(MARGIN_FLOOR, min(WTP_max, BASE_PRICE × AI_MULTIPLIER × MOAT_MULTIPLIER))
VALUE_SIGNAL = BASE_PRICE × AI_MULTIPLIER × MOAT_MULTIPLIER  [unconstrained]
```

Where:
- `BASE_PRICE` = midpoint(bargain_price, expensive_price) — elicited in Step 4
- `AI_MULTIPLIER` = 1.0 + (speed_improvement × accuracy_improvement)
  - **Fear signal**: if accuracy_improvement < 0.8 → AI_MULTIPLIER defaults to 1.0
  - speed_improvement: ratio multiplier (3.0 = 3× faster than non-AI alternative)
  - accuracy_improvement: quality fraction (0.9 = 90% accurate)
- `MOAT_MULTIPLIER` = Helmer 7 Powers score, clamped [1.0, 2.5]
  - Scale Economy moats: floor locked at 1.0 + penetration pricing advisory surfaced
- `MARGIN_FLOOR` = PRODUCTION_COST / (1 − target_margin)

**VALUE_SIGNAL** in Path B is the unconstrained result: the price the product's value justifies before
market-readiness constraints. When it exceeds WTP_max, Path B shows the gap as a market gap, not
suppressed. In Path A, `value_signal` is the price before the WTP_max cap, and its excess over the price
is headroom.

---

## Mode Detection

Check dispatch context for `automated: true` before proceeding.
- **Automated** (`automated: true`): Skip all `AskUserQuestion` calls. Use values from the dispatch context. Proceed through all steps without pausing for user input.
- **Interactive** (default): Engage Socratic dialogue at checkpoints as described in the workflow below.

## Workflow

### Step 0 — Load Config + Classify Agentic Tier

Read `config/defaults.json` (relative to plugin root). Store all values for use in this session.

Then ask (AskUserQuestion) [q: agentic_tier]:

1. Is this AI capability available from generic vendors — could any LLM or off-the-shelf tool
   do this job without your specific training or data?
2. Does this feature execute multi-step workflows autonomously without human prompting between steps?
3. Does a human review or approve the output before it takes effect in the customer's system?
4. Does this feature fully replace a defined human role or job function end-to-end?

Route based on answers:

```
if Q1 = Yes  → COMMODITY: note no AI premium justified; advise standard SaaS tier placement; STOP
if Q2 = No   → AUGMENTED: continue to Step 1 → Path A/B as normal
if Q3 = Yes  → AUTONOMOUS → Path C-Autonomous (go to Step 3-C)
if Q4 = Yes  → FULLY_AGENTIC → Path C-Fully Agentic (go to Step 3-C)
if Q2 = Yes AND Q3 = No AND Q4 = No → AUTONOMOUS (conservative) → Path C-Autonomous (go to Step 3-C)
```

### Step 1 — Collect Feature Context

Ask one question per AskUserQuestion call [q: none]:

1. What feature or offering are you pricing? Describe the primary job it does for customers. (AskUserQuestion [q: offering])
2. Who is the target customer segment? (AskUserQuestion [q: segment])

### Step 2 — Branch Check

**Block with a jtbd entry.** When the dispatch context holds a `plugin-run` block whose `inputs_from` has an entry with `plugin` `jtbd-market-discovery`, read only the file at that entry's `result_file`. When that file is missing or cannot be read as JSON, refuse it: record the gap `{"kind": "willingness_to_pay", "label": "Willingness to pay", "why": "jtbd result file missing or unreadable"}` and use Path B. Use it only when its `run.run_id` equals the entry's `run_id` and its `run.case` equals the block's `case`. Otherwise refuse it: no Path A, record the gap `{"kind": "willingness_to_pay", "label": "Willingness to pay", "why": "jtbd result run_id or case differs from inputs_from"}`, and use Path B. When it matches but holds no `willingness_to_pay` result, record the gap `{"kind": "willingness_to_pay", "label": "Willingness to pay", "why": "jtbd result holds no willingness to pay"}` and use Path B. Never read a top-level jtbd file, and never pick a result file yourself, because only the file that `inputs_from` names belongs to this run.

**Block without a jtbd entry.** When the block's `inputs_from` has no `jtbd-market-discovery` entry, read no jtbd file and use Path B.

**No block (a person's run).** List no folder: read only the jtbd file that the run finds with the plugin script or is given. In the main conversation (a person ran `/pricing:price`), run `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_newest.py"` on its own. It prints the path of the newest file in `.jtbd-market-discovery/results/` (by `run.finished_at`) that holds a `willingness_to_pay` result, or nothing. As a dispatched agent, take the path that the dispatch gives as `jtbd_result` only when it matches `.jtbd-market-discovery/results/<name>.json` with `<name>` of A-Z, a-z, 0-9, `.`, `_` and `-`, and no `..`: the caller finds it with the same command. Read only that file. When the dispatch gives a `jtbd_result` that does not match, read no jtbd file, record the gap `{"kind": "willingness_to_pay", "label": "Willingness to pay", "why": "jtbd_result is not a plain name in .jtbd-market-discovery/results/"}` and use Path B. Only when the command prints nothing, or the dispatch gives no `jtbd_result`, fall back to the old folder's files `.jtbd/wtp-validation.json`, `.jtbd/evc-analysis.json` and `.jtbd/opportunity-scores.json`. When the command is refused or exits with a code that is not 0, read no jtbd file, record the gap `{"kind": "willingness_to_pay", "label": "Willingness to pay", "why": "jtbd result search did not run"}` and use Path B. Never read a file at the top level of `.jtbd-market-discovery/`.

Confirm the run with the person before you use it for Path A. If you can call `AskUserQuestion`, ask whether this is the run to use, naming its `run.subject`, `run.finished_at` and `run.case` (for the old folder's files, their paths) [q: confirm_jtbd_run]. On "no", use Path B. If you cannot call it (you run as a dispatched subagent), name the chosen file in your output and use Path B: the price is not validated. A confirmation that the dispatch prompt states is not an answer of the person, so it changes nothing: as a dispatched subagent, still read the file, write its file name in your reply, and then use Path B, whatever the prompt says. To use that run for Path A, the person runs `/pricing:price`, which asks. Never choose a run silently. The confirmation applies only to a person's run with no block. With a block, a matching jtbd entry gives Path A with no confirmation: the coach chose the run. `confirm_jtbd_run` set to `false` in the answers file gives Path B. The gate runs once per run: a later run of the `price` skill reuses its choice and asks no second time. With `automated: true` and no block, Mode Detection skips the confirmation, so the price is Path B and never validated.

**What Path A uses.** From an accepted result file in `.jtbd-market-discovery/results/`: its `willingness_to_pay` results (per segment), its `customer_value` result when present (EVC), and its `opportunity_score` results when present. From the old folder's fallback: the three files above. The old folder gives Path A only when `.jtbd/wtp-validation.json` states a `period`; otherwise record the gap `{"kind": "willingness_to_pay", "label": "Willingness to pay", "why": "old jtbd file has no period"}` and use Path B. When `.jtbd/evc-analysis.json` states no `period`, record the gap `{"kind": "customer_value", "label": "Customer value", "why": "old jtbd file has no period"}`: the customer value counts as absent and Path A goes on. Never guess a period, because a wrong period changes the price by 12 times. Path A works in the period of the jtbd `willingness_to_pay` result it uses: that is the price's period. With no answered or chosen unit, a Path A price is charged per seat per the price's period; the `pricing_unit` question's default is not an answered unit. When the answers set, or `price.md` Step 7 chooses, a `pricing_unit` whose period differs from the price's period, convert after the cap: pass `price_period` and `unit_period` to `compute_path_a`, which converts the capped price, the headroom and the margin floor by the same rule (×12 from month to year, ÷12 from year to month), and label each figure with that unit; a unit Step 7 chooses after the price is computed means one more `compute_path_a` call with both periods. A `pricing_unit` with any other period is refused: record the gap `{"kind": "launch_price", "label": "Pricing unit", "why": "pricing unit has a period the price cannot take"}` and charge per seat per the price's period. When the calculator exits 1 with `pricing unit has a period the price cannot take`, record the same gap. Before Path A uses any other jtbd money value, convert it to the price's period: a `year` value is divided by 12 for a monthly price, and a `month` value is multiplied by 12 for a yearly price; a value in the price's period is used as written. When a value has no `period`, or any other period, refuse it and record the gap `{"kind": "<its kind>", "label": "<its label>", "why": "jtbd value has no period the price can take"}`: a refused `willingness_to_pay` gives Path B, and a refused `customer_value` counts as absent. Never guess a period, because a wrong period changes the price by 12 times. When the accepted jtbd file has a `customer_value` result, EVC is that value and AI_VALUE_DELTA is EVC minus REFERENCE_PRICE, both in the price's period. A Path A price never exceeds WTP_max: a higher value is headroom, shown in `value_signal`, not the price.

Path A: go to Step 2b, then to Step 5. A Path A price is `validated` only when its `willingness_to_pay` result, and its `customer_value` result when it used one, has a `customer_data` or `published` source; otherwise its `confidence_tier` is `estimated` and the report calls it "Path A, from jtbd (an estimate)". The calculator returns `validated` for every Path A price; write the tier this rule gives. Path B: `confidence_tier: "estimated"` (go to Step 3). User-stated value estimates without a jtbd result stay in Path B ("estimated").

### Step 2b — Path A Reference Price

Path A uses no customer value when the accepted file in `.jtbd-market-discovery/` has no `customer_value` result, when the gate refused it (a refused `customer_value` counts as absent), or when the old folder's `.jtbd/evc-analysis.json` gave none.

When Path A uses no customer value, REFERENCE_PRICE is what customers pay today for the nearest alternative, per the price's period. Take it from the answers file's `alternative_price`, else ask the person (AskUserQuestion [q: alternative_price]), else use WTP_max, also when the person declines.

When Path A uses a customer value, ask nothing and use WTP_max as REFERENCE_PRICE, even when the answers file gives `alternative_price`: AI_VALUE_DELTA is EVC minus REFERENCE_PRICE, so the price is the same either way.

Then go to Step 5.

### Step 3 — Elicit Outcome Description (Path B)

Ask one question per AskUserQuestion call [q: none]:
1. What specific outcome does this feature deliver? What job does it complete for the customer? (AskUserQuestion [q: outcome])
2. How much faster does this feature complete the job vs. the manual/non-AI alternative? (AskUserQuestion [q: speed_improvement])
   (Express as ratio: e.g., "3× faster" → speed_improvement = 3.0)
3. What accuracy/quality level does the AI achieve? (0–1 scale, e.g., 0.9 = 90% accurate) (AskUserQuestion [q: accuracy_improvement])

⚠️ If accuracy < 0.8 — surface the fear signal:
> "AI accuracy below 80% creates customer fear, not value. Pricing premium not justified.
> Consider improving the model before setting a premium price."

### Step 3-C — Collect Path C Inputs

**If AUTONOMOUS:**

Ask one question per AskUserQuestion call [q: none]:
1. How many hours does this task take a human today? (e.g., "2 hours per claim review") (AskUserQuestion [q: hours_per_task])
2. What is the fully-loaded hourly cost of the human who does this task? (AskUserQuestion [q: hourly_cost])
   (salary ÷ 2080 hours/year, include benefits, management overhead)
3. What is the most a customer would pay per task? (WTP ceiling per transaction) (AskUserQuestion [q: wtp_max])
4. What is the per-task production cost? (tokens, compute, API costs per task execution) (AskUserQuestion [q: production_cost])

**If FULLY_AGENTIC:**

Ask one question per AskUserQuestion call [q: none]:
1. What is the annual salary of the role this feature replaces? (AskUserQuestion [q: annual_salary])
2. What fraction of that role does the agent automate? (0–1, e.g., 0.90 = covers 90%) (AskUserQuestion [q: automation_rate])
3. What is the annual WTP ceiling? (most a customer would pay per agent per year) (AskUserQuestion [q: wtp_max])
4. What is the annual production cost? (hosting, tokens, model API costs per agent instance) (AskUserQuestion [q: production_cost])

⚠️ If automation_rate < `automation_rate_fear_signal_threshold` (from config) — surface fear signal:
> "Agent covers less than [X]% of the role — customer still needs a human for the remainder.
> Consider positioning as Autonomous (human-in-the-loop) and pricing per task instead."

### Step 4 — Run Abbreviated WTP Elicitation (Path B)

Ask 3 questions, one per AskUserQuestion call [q: none]:
1. "At what price does this feature feel like a bargain? Why?" (AskUserQuestion [q: bargain_price])
2. "At what price does this feature feel too expensive? Why?" (AskUserQuestion [q: expensive_price])
3. "What are you currently paying for the nearest alternative?" (AskUserQuestion [q: alternative_price])

Set BASE_PRICE = midpoint of bargain/expensive range.
Set WTP_max = expensive threshold.

### Step 5 — MOAT Elicitation (Adversarial — Both Paths)

**Self-rating without competitive reference is not accepted.**

If `.competitive-intelligence/strategic-analysis.json` exists → surface competitor moat
scores as grounding context before each question.

Ask questions that require naming competitors, one per AskUserQuestion call [q: none]:

1. (AskUserQuestion [q: competitors]) "Name two direct competitors. What specifically makes your switching costs stronger
   than theirs? Describe a concrete scenario where a customer would find it costly to leave."
2. (AskUserQuestion [q: network_effects]) "What network effects does your product have? How do they compare to [competitor names]?
   Give a specific example of a customer who benefits more because other customers use your product."
3. (AskUserQuestion [q: scale_advantage]) "Do you have a scale advantage (lower cost per unit at scale)? If yes, are you using that
   advantage to grow market share (penetration) or to protect margins (premium)?"

Score Helmer powers (1.0–2.5 per applicable power; 1.0 if no competitive data provided):
- Network Effects: 1.0–2.5
- Switching Costs: 1.0–2.5
- Scale Economies: ← see advisory below
- Counter-Positioning, Branding, Cornered Resource, Process Power: 1.0–2.5

**Scale Economy Advisory (hard override):**
If Scale Economy is the primary moat type:
> "⚠️ Scale Economy moat detected. Your pricing power comes from volume, not premium.
> Consider penetration pricing to grow market share and widen the cost advantage.
> MOAT_MULTIPLIER = 1.0 (hard override — all other Helmer scores are ignored for Scale Economy moats)."

If no competitor named → MOAT_MULTIPLIER = 1.0 + surface "competitive position unvalidated" warning
in output (does not change the multiplier value).

### Step 6 — Apply Formula

Compute with `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/pricing_calculator.py" <function> '<JSON object of its arguments>'`, one call per function. Before you build the command, test each value for a `'`, and write each `'` as `'\''`, because a `'` ends the quotes and the shell runs the rest of the value. `compute_margin_floor` takes `production_cost` and `target_margin`. The calculator prints the result as JSON. It exits 1 with the message on a bad value, and 2 when the command is wrong (the function, the argument names or the JSON): after an exit 2, correct the command 1 time from this step and run it again.

**When the calculator cannot run, stop.** This is a refused call, a second exit 2, an exit code other than 0, 1 and 2, an exit 0 with no JSON, or an exit 1 with a message that this file does not name. Compute no figure yourself, because only the calculator's figures are tested. Write no price file (`pricing-recommendation.json`, its copy, `new-offering-price.md`, `new-offering-data.json`, `packaging-architecture.json`) and run no later step. In a run of `pricing:price`, write the result file (`## Result file` of `agents/new-offering-pricer.md`) with `"results": []` and the gap `{"kind": "launch_price", "label": "Pricing calculator", "why": "pricing calculator <function>: <reason>"}`, where `<reason>` is `refused`, or the exit code and the first line of the message. End the reply with the line `BLOCKED: pricing calculator <function>: <reason>`. To run again, remove the cause, then run `/pricing:price` again: allow the `uv run` call of the plugin scripts (for a dispatched agent, in the session that dispatches it), or correct the input that the message names.
- Path A: `compute_path_a(reference_price, ai_value_delta, moat_value_delta, margin_floor, evc, wtp_max)`, with `price_period` and `unit_period` when the answers set a `pricing_unit` in another period. In Path A, `reference_price` and `production_cost` are per the price's period, as every money input of `compute_path_a` is.
- Path B: `compute_path_b(base_price, ai_multiplier, moat_multiplier, margin_floor, wtp_max)`
  — pass `accuracy_fear_signal_threshold` from `config/defaults.json` `path_b.accuracy_fear_signal_threshold`
    to `compute_ai_multiplier()` before calling `compute_path_b()`
- Path C-Autonomous: `compute_path_c_autonomous(time_saved_per_task, hourly_cost_of_human,
  value_capture_rate, margin_floor, wtp_max_per_task)`
  — load `value_capture_rate` from `config/defaults.json`
- Path C-Fully Agentic: `compute_path_c_fully_agentic(annual_salary, overhead_rate,
  automation_rate, value_share, margin_floor, wtp_max_annual, automation_rate_fear_signal_threshold)`
  — load `overhead_rate`, `value_share`, `automation_rate_fear_signal_threshold` from `config/defaults.json`
  — result is a discriminated union: read the output's `type`: `PathCFullyAgenticPriced` or
    `PathCFullyAgenticReclassified`, before you read `right_price`
  — if `PathCFullyAgenticReclassified`: surface `result.risk_advisory`, show
    `result.recovery_inputs_required`, and redirect user to Path C-Autonomous pricing
  — `ValueError` from calculator functions indicates invalid inputs — surface as user-facing
    error with the parameter name and value from the exception message

### Step 7 — Campbell Value Metric Check

Run `value-metric` skill to validate the pricing model aligns with how customers experience value.

### Step 8 — Present Recommendation

**Path A output:**
```
RIGHT_PRICE: $[amount] (confidence: [validated | estimated: Path A, from jtbd (an estimate)])
EVC: $[amount] (it bounds the formula; the price is capped at WTP_max)
Price before the WTP_max cap: $[value_signal]
Headroom: $[value_signal − amount] above the price (0 when the cap did not bind)
Floor warning: [floor_advisory, when present]
Pricing model: [Campbell recommendation]
```

**Path B output:**
```
PRICING ESTIMATE (UNVALIDATED) — confidence: estimated
RIGHT_PRICE: $[amount] (bounded by WTP_max: $[amount])
VALUE_SIGNAL: $[amount] (what the formula suggests without WTP constraint)
Strategic gap (Path B only): $[VALUE_SIGNAL − WTP_max] — market not yet ready to pay value-justified price
Pricing model: [Campbell recommendation]
[moat_advisory if present]
```

**Path C-Autonomous output:**
```
AGENTIC PRICING (AUTONOMOUS) — confidence: estimated
RIGHT_PRICE: $[amount] per task
  Task value: $[time_saved]h × $[hourly_cost]/hr = $[task_value]
  Value captured: [rate]× of task value
  Margin floor: $[amount]/task
Pricing model: [Campbell recommendation]
```

**Path C-Fully Agentic output (priced — automation_rate ≥ threshold):**
```
AGENTIC PRICING (FULLY AGENTIC) — confidence: estimated
RIGHT_PRICE: $[amount] per agent per year
  Replacement cost: $[salary] × (1 + [overhead]) = $[replacement_cost]
  Automation coverage: [rate]× of role → value pool: $[automation_value]
  Value captured: [share]× of replacement value
  Margin floor: $[amount]/year
Pricing model: [Campbell recommendation]
```

**Path C-Fully Agentic output (reclassified — automation_rate < threshold):**
```
⚠️ RECLASSIFIED TO PATH C-AUTONOMOUS
[risk_advisory text — explains coverage gap]
Recovery inputs needed: [list from result.recovery_inputs_required]
→ Redirect to Step 3-C (Autonomous) with the inputs listed above
```

### Step 9 — Write Output

Write to `.pricing/pricing-recommendation.json`:

```json
{
  "right_price": 0.0,
  "confidence_tier": "validated | estimated",
  "price_path": "A | B | C-autonomous | C-fully-agentic",
  "agentic_tier": "commodity | augmented | autonomous | fully_agentic | null",
  "pricing_unit": "per task | per agent per year | <the value metric Step 7 chose; when it chose none, per seat per the price's period in Path A and per seat per month in Path B>",
  "value_signal": 0.0,
  "segment_signal": {
    "wtf_gap": 0.0,
    "interpretation": "string"
  },
  "moat_advisory": "string | null",
  "floor_advisory": "string | null",
  "risk_advisory": "string | null"
}
```

---

## Key Heuristics

**Path B VALUE_SIGNAL interpretation:**
In Path B, the gap between VALUE_SIGNAL and RIGHT_PRICE is the market gap — the
customer's market-readiness hasn't caught up to the product's delivered value. This gap is
an input to `jtbd-market-discovery` for opportunity scoring in v1.1.

**MOAT elicitation failure modes:**
- User names competitors but can't articulate differentiation → MOAT_MULTIPLIER = 1.0
- User claims strong moat without comparative evidence → flag as unvalidated
- User describes Scale Economy advantages → switch to penetration advisory

**AI_MULTIPLIER fear signal guidance:**
Accuracy below 80% means customers are likely to experience errors and lose trust. A
premium price on a low-accuracy AI feature accelerates churn and damages trust. Fix
the model before pricing it as an AI-era feature.
