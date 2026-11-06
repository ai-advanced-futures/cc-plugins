---
name: integrity-truth-tier-system
description: Classify every marketing claim into one of five Truth Tiers before it reaches any artifact
---

# Truth Tier System

## Purpose

The Truth Tier System is the Marketing Integrity Engine's classification backbone. Every claim in every GTM artifact — positioning statements, pitch decks, campaign copy, sales scripts — receives a Truth Tier before delivery. Tier 5 claims are blocked.

**Core principle:** A marketing claim is only as strong as its evidence. Evidence determines tier. Tier determines permitted language and permitted artifacts.

## The Five Tiers

| Tier | Label | Evidence Required | Permitted Language | Permitted In |
|---|---|---|---|---|
| 1 | **Shipped** | Code exists, tested, GA, customers using it | "Available today", "Customers use X to..." | All artifacts |
| 2 | **In-Flight** | Code in progress, beta/EA, partial deployment | "Now in early access", "Beta customers are..." | All artifacts, labeled |
| 3 | **Committed** | Designed + budgeted + exec-sponsored + scheduled | "Coming in [quarter]", "On our Q3 roadmap" | Sales, investor, roadmap artifacts |
| 4 | **Strategic Intent** | Direction stated, not yet funded or scheduled | "Our vision is...", "We intend to..." | Vision docs, investor narrative only |
| 5 | **Speculation** | None | **BLOCKED** | Blocked from all artifacts |

## Language Rules

### Superlative Detection
Flag these words and ask for proof: `best`, `fastest`, `leading`, `top`, `#1`, `most advanced`, `most powerful`, `most innovative`, `most trusted`, `world-class`, `industry-leading`, `unmatched`, `premier`, `only`, `first`

**Rule:** Superlative without a cited benchmark → demote to Tier 4 or remove.

### Quantified Claim Sourcing
Flag any claim with numbers (%, X times, Nx faster) without an in-line source.

**Rule:** "Increases conversion by 300%" → require "(source: A/B test Q4 2025, n=1,200)" or demote.

### Future-Tense-as-Present Detection
Flag: "will", "shall", "going to", "soon", "upcoming" used to describe product capabilities.

**Rule:** Future tense = Tier 3 minimum. Verify budget + exec sponsor + schedule exist before Tier 3.

### Enthusiasm Without Evidence
Flag: emotional appeals that outpace documented reality.

**Rule:** "Transformative", "revolutionary", "game-changing" without a Tier 1-2 capability supporting it → blocked.

## Classification Protocol

For each claim in the artifact:
1. Identify the claim text
2. Identify the evidence source (codebase scan, roadmap doc, customer data, or none)
3. Assign tier based on evidence type
4. Run language checks
5. If Tier 5: block the claim, provide suggested rewrite at Tier 3-4 level
6. If Tier 4 in a non-permitted artifact: flag and demote language

## Output Format

Produces `truth-tier-audit.json`:

```json
{
  "artifact": "pitch-deck v2",
  "audited_at": "2026-02-24T10:00:00Z",
  "integrity_score": 0.85,
  "blocked_count": 1,
  "claims": [
    {
      "text": "Available today for all customers",
      "tier": 1,
      "blocked": false,
      "language_issues": []
    },
    {
      "text": "We will revolutionize the market",
      "tier": 5,
      "blocked": true,
      "language_issues": ["Superlative without proof", "Future tense without evidence"],
      "suggested_fix": "Remove or replace with a specific Tier 1-2 capability claim"
    }
  ]
}
```
