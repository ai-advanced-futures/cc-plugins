---
name: package
description: Interactive agent-driven workflow for Good/Better/Best tier packaging. Walks users through feature collection, Killer/Leader/Filler classification, freemium gate decision tree, tier assignment, and 9-benefit complexity validation using Ramanujam's framework.
allowed-tools: Edit(/.pricing/**)
---

# Package — Interactive Good/Better/Best Tier Design

Agent-driven workflow that walks you through building a tier architecture step by step: feature collection, classification, freemium gate selection, tier assignment, and complexity validation.

## When to Use

- "Design our Good/Better/Best tiers"
- "What should go in each pricing tier?"
- "Should we have a free tier?"
- "Help us redesign our packaging"
- "What freemium strategy is right for us?"

## Classification Framework

### Ramanujam Killer/Leader/Filler

| Category | Definition | Tier Placement |
|----------|-----------|----------------|
| **Killer** | The reason customers buy — must-have differentiator | Better / Best |
| **Leader** | Builds on the Killer — top 3–5 features | Better |
| **Filler** | Table stakes — expected but not motivating | Good |

### Freemium Gate Decision Tree

1. `requires_sales_assistance` → **NO_FREE_TIER**
2. `has_network_effects AND value_metric_scales_with_usage` → **FREEMIUM_USAGE_LIMITED**
3. `has_network_effects` → **FREEMIUM_FEATURE_LIMITED**
4. `value_immediately_apparent` → **TRIAL_GATE**
5. default → **NO_FREE_TIER**

### Complexity Guard

- Maximum **9 benefits per tier** (Ramanujam rule)
- Tiers exceeding 9 benefits flagged as Feature Shock risk

## Interactive Flow

1. **Feature Collection** — gather features from user input or scan existing product docs
2. **Killer/Leader/Filler Classification** — classify each feature interactively with guidance
3. **Freemium Gate Decision** — walk through 5-condition decision tree one question at a time
4. **Tier Assignment** — auto-assign features to Good/Better/Best, present for user validation
5. **Complexity Validation** — enforce 9-benefit ceiling, flag Feature Shock risk
6. **Output** — write `.pricing/packaging-architecture.json` and present summary table

## Output

`.pricing/packaging-architecture.json` — tier definitions, feature assignments, freemium gate type, WTP-anchored price points, complexity validation.

## Cross-References

- **Reads from:** `.pricing/pricing-recommendation.json` (RIGHT_PRICE as anchor)
- **Reads from:** the jtbd graph, through `brain_read.py outcomes` (if it holds data — for tier placement signal). When `pricing:price` runs this skill, take jtbd data only from what its price gate accepted, and none when the gate accepted nothing.
- **Orchestrated by:** `new-offering-pricer` agent
- **Full prompt:** See `package.md` in this directory
