---
name: package
description: Interactive agent-driven workflow to design Good/Better/Best packaging tiers. Walks users through feature collection, Killer/Leader/Filler classification, freemium gate selection, tier assignment, and complexity validation using Ramanujam's framework.
model: sonnet
tools: Read(*), Write(*), Skill(*), AskUserQuestion(*)
---

# Package Skill — Interactive Tier Design Workflow

Ask a number or a free-text input in one chat message, or offer options that are real values; never offer an option that only says to type, such as "Type amount", "Type it", "Enter figures" or "List them", because a person cannot pick a value from such an option.

## Purpose

Design packaging tiers (Good/Better/Best, usage-based, or hybrid) aligned to customer
segments and their willingness to pay — through an interactive, step-by-step agent workflow.

**Rule:** Maximum 3-4 tiers, maximum 9 benefits per tier (Ramanujam's complexity threshold).

**Framework:** Ramanujam Good/Better/Best packaging + Helmer power-based tier differentiation + Amadeo outcome pricing integration.

## Trigger Phrases

`packaging strategy`, `pricing tiers`, `good better best`, `tier design`,
`what goes in each tier`, `bundle`, `usage tiers`

## Mode Detection

Check dispatch context for `automated: true` before proceeding.
- **Automated** (`automated: true`): Skip all `AskUserQuestion` calls. Use values from the dispatch context. Proceed through all steps without pausing for user input.
- **Interactive** (default): Engage Socratic dialogue at checkpoints as described in the workflow below.

## Inputs

- Feature list (or `audit` skill output)
- Customer segments + WTP (from `jtbd-market-discovery` or manual)
- Value metric (from `value-metric` skill)
- `audit` output (recommended — provides Leader/Filler/Killer classification)

## Outputs

- Tier architecture (Good / Better / Best + optional Enterprise)
- Feature assignment per tier with rationale
- Freemium gate-type recommendation
- Packaging complexity score (violation flag if >9 benefits/tier)
- `.pricing/packaging-architecture.json`

---

## Workflow

### Step 1 — Feature Collection

**Goal:** Build a complete feature inventory before classification begins.

`<git root>` is the output of `git rev-parse --show-toplevel`, which you run first, on its own; when it fails, `<git root>` is the working directory. Write each script call as 1 command with each path written out: no `$(...)`, no shell variable, no pipe, no redirect, and no second command in the same call, because only that form runs with no question to the person. Write `${CLAUDE_PLUGIN_ROOT}` as the plugin root path that the skill text gives, because the shell of the call does not have that variable.

Check for upstream data first:
- If `.pricing/audit-data.json` exists -> import feature list and any prior classifications
- When `pricing:price` runs this skill, take jtbd data only from what its price gate accepted, and none when the gate accepted nothing. In a standalone run, run `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/brain_read.py" outcomes --root <git root>` on its own. When `found` is `true`, import the opportunity scores as classification signal. When `found` is `false`, show its `why` and go on.

If upstream data found, present it:

```
I found existing data:
- [N] features from your pricing audit
- [N] opportunity scores from JTBD discovery

Here is the imported feature list:
1. [feature name] — [description]
2. [feature name] — [description]
...

Are these complete, or do you want to add/remove features?
```

Ask (AskUserQuestion) [q: feature_list]:

> "List all the features and capabilities of your product or service. Include everything — we will classify and filter in the next step.
>
> You can:
> - Type them as a list
> - Point me to a product doc or feature spec I can scan (provide the file path)
> - Say 'use audit data' if you have already run /pricing:audit"

If the user provides a file path, use `Read` to scan it and extract features. Present the extracted list back for confirmation.

Ask (AskUserQuestion) [q: feature_list]:

> "Here is the feature list I have so far:
>
> [numbered list]
>
> Is this complete? Add any missing features or say 'done' to proceed to classification."

Store the final feature list. This is the working set for all subsequent steps. With no feature list from the person, infer the features from the offering's description (`feature_list = inferred from the offering`).

---

### Step 2 — Killer / Leader / Filler Classification

**Goal:** Classify every feature using Ramanujam's framework.

Present the classification guide once:

```
We will now classify each feature into one of three categories:

  KILLER  = The reason customers buy. The must-have differentiator.
            Test: "Would a prospect choose us OVER competitors because of this?"

  LEADER  = Builds on the Killer. Top 3-5 features that deepen value.
            Test: "Would a customer NOT buy if this were missing?"

  FILLER  = Table stakes. Expected but not motivating.
            Test: "Do competitors also have this? Would removing it cause churn?"

Classification matters because it determines tier placement:
  Fillers  -> Good tier (entry level)
  Leaders  -> Better tier (anchor — where most customers land)
  Killers  -> Better / Best tier (upgrade drivers)
```

For each feature, ask (AskUserQuestion) [q: feature_classes]:

> "Feature: **[feature name]**
> [description if available]
>
> Classify this feature:
> - **K** = Killer (the reason customers buy)
> - **L** = Leader (builds on the Killer, top 3-5 features)
> - **F** = Filler (table stakes, expected but not motivating)
>
> Your classification?"

With no class from the person, classify each feature by the tests above (`feature_classes = classified by the model`).

If the user provides a classification that seems inconsistent (e.g., 10+ Killers), flag it:

> "You have classified [N] features as Killers. Typically there are 1-2 true Killers. A Killer is the single biggest reason a customer chooses you over alternatives. Would you like to review your Killer classifications?"

After all features are classified, present the summary:

```
Classification Summary:
  Killers ([N]):  [list]
  Leaders ([N]):  [list]
  Fillers ([N]):  [list]

Does this look right? You can reclassify any feature by name, or say 'confirmed' to proceed.
```

---

### Step 3 — Freemium Gate Decision

**Goal:** Determine whether the product should have a free tier, trial, or paid-only entry using Ramanujam + Campbell's 5-condition decision tree.

Walk through each condition interactively. Stop at the first "Yes."

**Condition 1: Sales Assistance**

Ask (AskUserQuestion) [q: sales_assisted]:

> "Does your product require sales-assisted onboarding or a contract to deploy value?
> (Examples: enterprise software that needs implementation, products requiring security review, anything needing a demo to understand)
>
> Yes or No?"

If Yes -> Gate type = `NO_FREE_TIER`
> "Your product needs guided onboarding. Free tiers create unqualified leads, not adoption. Recommendation: **No free tier** — use sales-qualified demos instead."

Skip to Step 4.

**Condition 2: Network Effects + Usage Scaling**

Ask (AskUserQuestion) [q: network_usage]:

> "Two-part question:
> 1. Does your product have network effects — is it more valuable when more people use it?
> 2. Does your value metric naturally scale with usage (e.g., API calls, documents processed, messages sent)?
>
> Answer: Both Yes / Only network effects / Only usage scaling / Neither"

If Both Yes -> Gate type = `FREEMIUM_USAGE_LIMITED`
> "Freemium with usage limits (e.g., 1,000 API calls/month free) grows network value while converting power users to paid."

Skip to Step 4.

**Condition 3: Network Effects Only**

If user answered "Only network effects" above -> Gate type = `FREEMIUM_FEATURE_LIMITED`
> "Freemium with feature limits (e.g., no team features on free plan) keeps solo users engaged and converts when they grow."

Skip to Step 4.

**Condition 4: Immediate Value**

Ask (AskUserQuestion) [q: immediate_value]:

> "When a customer first uses your product, do they experience value immediately — within minutes — or does it require setup time, data import, or configuration?
>
> Immediate value / Requires setup"

If Immediate value -> Gate type = `TRIAL_GATE`
> "Time-limited trial (14 days) lets customers experience value before committing. Better than freemium when value is fast but network effects are absent."

Skip to Step 4.

**Condition 5: Default**

If none of the above triggered -> Gate type = `NO_FREE_TIER`
> "Insufficient signals to recommend a free tier. Start paid-only and add freemium when retention data confirms the conversion hypothesis."

Present the gate decision:

```
Freemium Gate Decision: [GATE_TYPE]
Rationale: [explanation from above]

Proceed to tier assignment? (or override if you disagree)
```

---

### Step 4 — Tier Assignment

**Goal:** Automatically assign features to Good/Better/Best tiers based on Killer/Leader/Filler classification, then validate with the user.

Apply Ramanujam tier rules:

| Classification | Default Tier | Rule |
|---|---|---|
| **Filler** | Good | Entry-level needs; 3-5 features max |
| **Leader** | Better | All Leaders + core Fillers; drives most purchases; 6-8 features |
| **Killer** | Better / Best | Killers in Better make it the anchor; exclusive Killers in Best drive upgrades |

Assignment logic:
1. Place all Fillers in Good
2. Place all Leaders in Better
3. Place Killers in Better (making it the recommended tier)
4. If there are 2+ Killers, move the most differentiating Killer(s) to Best as upgrade drivers
5. Copy every feature of the first tier into the second tier (the second tier includes everything of the first)
6. Copy all Better features into Best (Best includes everything in Better)

Apply Helmer Power differentiation for Best tier:
- Network Effects features -> gate behind Best
- Switching Cost features (integrations, APIs, data portability) -> gate behind Best
- Counter-Positioning features (things incumbents cannot copy) -> gate behind Best

Present the proposed assignment:

```
Proposed Tier Architecture:

GOOD (Entry)
  [feature list with classifications]

BETTER (Recommended) — includes all Good features plus:
  [additional features with classifications]

BEST (Premium) — includes all Better features plus:
  [additional features with classifications]

Ramanujam's rule: "Most customers should buy Better. If most customers
are on Good, your Leaders are in the wrong tier."
```

Ask (AskUserQuestion) [q: tier_feedback]:

> "Review the tier assignment above. You can:
> - Move a feature: 'move [feature] to [tier]'
> - Accept: 'looks good'
> - Ask why a feature is in a specific tier
>
> Your feedback?"

Iterate until the user confirms. With no feedback from the person, keep the proposed tiers (`tier_feedback = keep the proposed tiers`).

---

### Step 5 — Complexity Validation

**Goal:** Enforce Ramanujam's 9-benefit ceiling per tier and flag Feature Shock risk.

Count unique benefits per tier (not cumulative — count only the features new to each tier plus inherited):

For each tier, if benefit count exceeds 9:

```
WARNING — Feature Shock Risk

[Tier] has [N] benefits (maximum: 9)

Ramanujam: "9 benefits is the cognitive limit for a purchase decision.
Features beyond 9 create feature shock — customers focus on what they
do not need instead of what they do."

Recommended actions:
- Remove: [lowest-value features in this tier]
- Merge: [features that could be combined into a single benefit]
- Defer: [features that could become add-ons instead of tier features]
```

Ask (AskUserQuestion) [q: complexity_choice]:

> "Tier [name] exceeds the 9-benefit ceiling. Which approach do you want to take?
> - Remove specific features from this tier
> - Merge features (tell me which ones to combine)
> - Convert features to paid add-ons
> - Override the warning and keep all [N] features"

Repeat until all tiers pass or user explicitly overrides.

If all tiers pass:

```
Complexity Check:
  Good:   [N]/9 PASS
  Better: [N]/9 PASS
  Best:   [N]/9 PASS

No Feature Shock risk detected.
```

---

### Step 6 — Output

**Goal:** Write the packaging architecture to a structured JSON file and present a clean summary.

#### Price Anchoring (if available)

If `.pricing/pricing-recommendation.json` exists, read it and anchor tier prices:
- Good tier -> 50th percentile WTP
- Better tier -> 75th percentile WTP
- Best tier -> 90th percentile WTP

If WTP data is absent, apply Ramanujam benchmarks:
- Better = 2.5x Good
- Best = 5x Good

If no pricing data at all, note that price points require running `/pricing:price` first.

#### Write Output File

Write `.pricing/packaging-architecture.json`:

```json
{
  "generated": "[ISO timestamp]",
  "framework": "ramanujam-good-better-best",
  "gate_type": "[selected gate type]",
  "gate_rationale": "[explanation]",
  "tiers": {
    "good": {
      "name": "Good",
      "features": [
        {"name": "...", "classification": "filler", "description": "..."}
      ],
      "benefit_count": 0,
      "complexity_status": "pass",
      "price_anchor": null
    },
    "better": {
      "name": "Better",
      "recommended": true,
      "features": [],
      "benefit_count": 0,
      "complexity_status": "pass",
      "price_anchor": null
    },
    "best": {
      "name": "Best",
      "features": [],
      "benefit_count": 0,
      "complexity_status": "pass",
      "price_anchor": null
    }
  },
  "feature_classifications": {
    "killers": [],
    "leaders": [],
    "fillers": []
  },
  "complexity_validation": {
    "max_benefits_per_tier": 9,
    "all_tiers_pass": true,
    "overrides": []
  },
  "cross_references": {
    "pricing_recommendation": null,
    "opportunity_scores": null,
    "audit_data": null
  }
}
```

#### Present Summary Table

```
========================================
  PACKAGING ARCHITECTURE — SUMMARY
========================================

Gate Type: [type] — [one-line rationale]

----------------------------------------
  GOOD (Entry)          $[price]/mo
----------------------------------------
  1. [feature]           (Filler)
  2. [feature]           (Filler)
  ...
  Benefits: [N]/9

----------------------------------------
  BETTER (Recommended)   $[price]/mo
----------------------------------------
  + everything in Good, plus:
  3. [feature]           (Leader)
  4. [feature]           (Killer)
  ...
  Benefits: [N]/9

----------------------------------------
  BEST (Premium)         $[price]/mo
----------------------------------------
  + everything in Better, plus:
  5. [feature]           (Killer)
  ...
  Benefits: [N]/9

========================================
  Complexity: [PASS/WARN per tier]
  Output: .pricing/packaging-architecture.json
========================================
```

Confirm with user:

> "Packaging architecture saved to `.pricing/packaging-architecture.json`. Next steps:
> - Run `/pricing:price` to compute WTP-anchored price points for each tier
> - Run `/pricing:value-metric` if you have not selected your value metric yet
> - The `new-offering-pricer` agent can orchestrate the full pricing workflow"

---

## Key Heuristics

**Leader features:** Ask "Would a customer NOT buy if this feature were missing?" If yes -> Leader.
Place Leaders in Better, not Good.

**Killer features:** Ask "Does including this feature make the product harder to buy?"
If yes -> remove from bundle or isolate to add-on.

**Freemium threshold caution:**
The gate type (freemium vs. trial vs. paid-only) is a strategic decision that can be made
without telemetry. The exact limit (1,000 API calls vs. 500 vs. unlimited) requires
conversion data. Document the gate type now; refine the threshold in v1.1.

**Complexity threshold reality check:**
9 benefits is the cognitive limit for a purchase decision. Features beyond 9 create
"feature shock" (Ramanujam) — customers focus on what they have no use for instead of what
they use. Fewer benefits with stronger positioning is almost always better.

## Cross-References

- **Reads from:** `.pricing/pricing-recommendation.json` (RIGHT_PRICE as anchor)
- **Reads from:** `.pricing/audit-data.json` (feature classifications)
- **Reads from:** the jtbd graph, through `brain_read.py outcomes` (tier placement signal). When `pricing:price` runs this skill, take jtbd data only from what its price gate accepted, and none when the gate accepted nothing.
- **Orchestrated by:** `new-offering-pricer` agent
