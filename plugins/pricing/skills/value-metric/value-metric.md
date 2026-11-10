---
name: value-metric
description: Select the right pricing axis for a product or feature using Campbell's 3 criteria and Amadeo's VALUE = Speed × Accuracy formula. Detects the per-user antipattern and recommends AI-era vs legacy value metrics.
model: sonnet
tools: Read(*), Write(*), Skill(*), AskUserQuestion(*)
---

# Value Metric Skill

Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them", because a person cannot pick a value from such an option.

## Purpose

Identify the pricing axis that reflects how customers actually experience value — avoiding
the per-user antipattern and maximizing pricing growth alignment.

**Framework:** Patrick Campbell's 3 criteria (alignment, understandability, growth alignment)
+ Luis Amadeo's VALUE = Speed × Accuracy of Outcome test.

## Trigger Phrases

`what should we price on`, `per seat vs usage`, `pricing axis`, `value metric`,
`how should we charge`, `pricing model`

## Inputs

- Product/feature description
- Target customer segment
- Primary outcome delivered to customers
- Existing pricing model (if any)

## Outputs

- Recommended value metric with rationale
- Campbell criteria scores (alignment, understandability, growth alignment)
- AI-era vs legacy metric classification
- Per-user antipattern flag (if detected)
- Ranked alternative metrics with trade-offs

---

## Mode Detection

Check dispatch context for `automated: true` before proceeding.
- **Automated** (`automated: true`): Skip all `AskUserQuestion` calls. Use values from the dispatch context. Proceed through all steps without pausing for user input.
- **Interactive** (default): Engage Socratic dialogue at checkpoints as described in the workflow below.

## Workflow

### Step 1 — Collect Product Context

Ask one question per AskUserQuestion call [q: none]:

1. **What does your product/feature do?** Describe the primary outcome in one sentence. (AskUserQuestion [q: offering])
2. **Who is the target customer segment?** (Persona, company size, role) (AskUserQuestion [q: segment])
3. **How does a customer know they got value?** What do they walk away with? (AskUserQuestion [q: value_sign])
4. **What is your current pricing model?** (per seat, flat fee, usage-based, etc. — or "none yet") (AskUserQuestion [q: current_pricing_model])

### Step 2 — Identify the Primary Job

Map the outcome to a JTBD job statement:
> "When [context], I want to [motivation], so I can [expected outcome]."

`<git root>` is the output of `git rev-parse --show-toplevel`, which you run first, on its own; when it fails, `<git root>` is the working directory. Write each script call as 1 command with each path written out: no `$(...)`, no shell variable, no pipe, no redirect, and no second command in the same call, because only that form runs with no question to the person. Write `${CLAUDE_PLUGIN_ROOT}` as the plugin root path that the skill text gives, because the shell of the call does not have that variable.

When `pricing:price` runs this skill, take jtbd data only from what its price gate accepted, and none when the gate accepted nothing. In a standalone run, run `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/brain_read.py" outcomes --root <git root>` on its own. When `found` is `true`, surface the top-scored outcome. When `found` is `false`, show its `why` and go on.

### Step 3 — Apply Campbell's Gut-Check Test

For each candidate metric (per seat, per outcome, per usage unit, per time saved, per
revenue generated):

Score each on 3 dimensions (0 or 1):

| Dimension | Question |
|---|---|
| **Alignment** | Does growth in this metric reflect growth in value delivered? |
| **Understandability** | Can the customer control this metric? Do they understand it? |
| **Growth alignment** | Will customers *want* this metric to grow as they succeed? |

Flag per-user antipattern: if metric = per-seat AND growth in seats ≠ growth in value
delivered → surface Campbell's warning.

### Step 4 — Apply Amadeo's AI-Era Test

Score the metric on a 4th dimension (0 or 1):

| Dimension | Question |
|---|---|
| **AI-era alignment** | Does this metric scale with Speed × Accuracy of Outcome as AI improves? |

AI-era metrics: per-outcome, per-prediction, per-task-completed, per-revenue-generated,
per-time-saved. These scale as AI performance compounds.

Legacy metrics: per-seat, per-user, flat-fee. These stay flat as AI improves.

### Step 5 — Rank and Present

Present ranked metric options:

```
Recommended: [metric] (Campbell score: X/3 + AI-era: Y)
Rationale: [1-2 sentences]

Alternatives:
  2. [metric] — [trade-off note]
  3. [metric] — [trade-off note]

⚠️ Per-user antipattern: [if detected, explain the risk]
```

### Step 6 — Write Output (optional)

If user confirms, write to `.pricing/value-metric.json`:

```json
{
  "recommended_metric": "string",
  "campbell_score": 3,
  "ai_era_aligned": true,
  "per_user_antipattern_detected": false,
  "rationale": "string",
  "alternatives": []
}
```

---

## Key Heuristics

**AI-era pricing power signals:**
- Metric is the *outcome* (revenue, time saved, documents processed) not the *input* (seats, API calls)
- Metric grows as the AI model improves (compounding returns to the customer)
- Customer can attribute the metric directly to your product's value

**Per-user antipattern red flags:**
- Pricing per-seat when seats are unrelated to value units
- Pricing per-user when growth in users is just "team size" not "more outcomes"
- Exception: per-user IS valid when each user genuinely creates proportional value

**Legacy metric signals:**
- Flat fee (no growth alignment)
- Per-seat when seat count = headcount, not outcome count
- Per-feature-unlock when no natural scaling dimension exists
