---
name: audit
description: Audit existing product features to classify them as AI-era vs legacy, detect Ramanujam failure modes (feature shock, minivation, undead), and score value delivery vs price tier. Uses two-layer classification rubric with temporal review fields.
model: sonnet
tools: Read(*), Write(*), Bash(*), Skill(*), AskUserQuestion(*)
---

# Audit Skill

Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them", because a person cannot pick a value from such an option.

## Purpose

Analyze existing features, tiers, and offerings to detect:
- Features no longer delivering proportional value to their price tier
- AI-era vs legacy classification with temporal stability fields
- Ramanujam failure modes (feature shock, minivation, hidden gems, undead features)

**Framework:** Ramanujam feature-to-value alignment + Campbell SaaS benchmarks +
Amadeo VALUE decay detection + Helmer competitive baseline condition.

## Trigger Phrases

`audit pricing`, `legacy features`, `pricing misalignment`, `are we charging the right amount`,
`pricing review`, `over-priced`, `under-priced`, `AI-era audit`

## Inputs

- Feature list with tier assignments
- Current pricing per tier
- Customer segment WTP (optional — from `jtbd-market-discovery`)
- Competitive landscape description (optional — from `competitive-intelligence`)

## Outputs

- Feature classification: Leader / Filler / Killer (Ramanujam)
- AI-era vs Hybrid vs Legacy classification per feature (with Layer 1 + Layer 2 scores)
- Misalignment score per feature
- Recommended tier reassignments
- Ramanujam failure mode flags
- Temporal fields per classification (classification_date, review_date, competitive_baseline_condition)
- Executive summary audit report

---

## Mode Detection

Check dispatch context for `automated: true` before proceeding.
- **Automated** (`automated: true`): Skip all `AskUserQuestion` calls. Use values from the dispatch context. Proceed through all steps without pausing for user input.
- **Interactive** (default): Engage Socratic dialogue at checkpoints as described in the workflow below.

## Workflow

### Step 1 — Ingest Feature List

Ask (AskUserQuestion) [q: feature_list]:

1. **Provide your feature list.** List features with their current tier assignment and price.
   Format: `feature_name | tier (Good/Better/Best) | current price contribution`
2. **What is your current competitive landscape?** How many direct competitors?
   Which AI capabilities are table stakes vs. differentiators?

`<git root>` is the output of `git rev-parse --show-toplevel`, which you run first, on its own; when it fails, `<git root>` is the working directory. Write each script call as 1 command with each path written out: no `$(...)`, no shell variable, no pipe, no redirect, and no second command in the same call, because only that form runs with no question to the person. Write `${CLAUDE_PLUGIN_ROOT}` as the plugin root path that the skill text gives, because the shell of the call does not have that variable.

Check for existing data:
- Run `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/brain_read.py" wtp --root <git root>` on its own. When `found` is `true`, import `result` as the WTP per segment for comparison. When `found` is `false`, show its `why` and go on.
- Run `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/brain_read.py" moats --root <git root>` on its own. When `found` is `true`, import the competitor moats. When `found` is `false`, show its `why` and go on.

### Step 2 — Apply Layer 1 Triage (all features)

For each feature, score 5 dimensions (0 or 1):

| Dimension | Question |
|---|---|
| **ML Inference** | Does this feature use ML/AI inference as the primary value delivery mechanism? |
| **Quality Improvement** | Does outcome quality improve as the feature accumulates more data/usage over time? |
| **Speed Advantage** | Is the speed of outcome delivery measurably faster than the manual/non-AI alternative? |
| **AI Attribution** | Is the AI mechanism the direct cause of value (vs. the underlying dataset)? |
| **Competitive Rarity** | Is this AI capability rare in the current competitive landscape (not table stakes)? |

**Scoring:**
- 0–2 → **Legacy** (static or declining value)
- 3–4 → **Hybrid** (partial AI premium justified)
- 5 → **Provisionally AI-era** (may justify premium multiplier)

### Step 3 — Classify as Leader / Filler / Killer (Ramanujam)

For each feature:

| Category | Definition |
|---|---|
| **Leader** | Creates the most WTP; should anchor the "Better" tier |
| **Filler** | Nice-to-have; fills out tier but doesn't drive purchase decision |
| **Killer** | Actively hurts purchase decision when bundled inappropriately |

Detect Ramanujam failure modes:
- **Feature shock**: >9 features/benefits per tier (complexity overload)
- **Minivation**: Under-charging for a high-WTP feature
- **Hidden gem**: High WTP feature buried in wrong tier
- **Undead feature**: Low usage + low WTP still occupying prime tier real estate

### Step 4 — Apply Layer 2 Gate (AI-era features only, when AI_MULTIPLIER > 5x)

If a feature is classified AI-era and the justified AI_MULTIPLIER would exceed 5x,
check all three conditions:

1. **Autonomy**: Feature executes without human intervention on the primary job
2. **Compounding**: Value delivered increases with usage over time (not fixed at training)
3. **Attribution**: Speed × Accuracy improvement causally isolatable vs. equivalent non-AI implementation

If any condition fails → cap AI_MULTIPLIER at 5x for this feature.

### Step 5 — Score Value vs. Price Tier

For each feature, compute misalignment signal:
- Compare classification (AI-era/Hybrid/Legacy) to current tier placement
- AI-era feature in Good tier = under-priced (hidden gem)
- Legacy feature in Best tier = over-priced (undead)
- Killer feature bundled with core tiers = packaging failure

### Step 6 — Generate Temporal Fields

For each classification, compute:

```json
{
  "classification_date": "ISO date when audit ran",
  "review_date": "classification_date + review_window_months",
  "competitive_baseline_condition": "description of competitive landscape at audit time"
}
```

`review_window_months = 36 / log₂(1 + competitor_count)`, range [6, 36].

If competitor_count unknown → 18 months, labeled:
> "Conservative placeholder (not empirical estimate). Update when competitor count is known."

### Step 7 — Generate Audit Report

Write to `.pricing/audit-report.md`:

```markdown
# Pricing Audit Report
## Date: [date]
## Features Audited: [count]

### AI-Era Features (Layer 1 score = 5)
[list with Layer 2 gate results]

### Hybrid Features (Layer 1 score 3–4)
[list]

### Legacy Features (Layer 1 score 0–2)
[list]

### Failure Modes Detected
- Feature Shock: [tiers with >9 benefits]
- Hidden Gems: [underpriced Leaders]
- Undead Features: [candidates for retirement]

### Recommended Actions
Priority 1 (quick wins): [...]
Priority 2 (strategic repricing): [...]
Priority 3 (retire): [...]

### Classification Review Schedule
[feature] — review by [review_date] ([window] month window)
```

Write structured data to `.pricing/audit-data.json`.

---

## Key Heuristics

**AI-era feature signals (Layer 1 strong indicators):**
- Feature learns from usage and improves automatically
- Customers can't replicate the speed/accuracy with a human + spreadsheet
- The AI model is doing work, not just surfacing data

**Competitive rarity caution:**
- Classification date matters — a "rare" capability in 2024 may be table stakes by 2026
- Always set review_date to prompt reclassification as market matures
- Use `competitive_baseline_condition` to document current landscape state

**Layer 2 attribution note:**
Attribution must be evaluated against a non-AI equivalent implementation, not against
the AI model's training corpus. "Would a rules-based system achieve the same result?"
is the correct comparison question.
