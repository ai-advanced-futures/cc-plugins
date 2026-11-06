# Integrity Score — Canonical Definition

## Formula

```
integrity_score = passing_claims / total_claims

where:
  passing_claims  = total_claims - tier_5_blocked   (numerator)
  total_claims    = all claims reviewed (denominator — does NOT change when claims are blocked)
  tier_5_blocked  = claims assigned Tier 5 and removed from output
```

Plain English: what fraction of claims reviewed were NOT Tier 5?
- Tier 5 claims reduce the numerator (fewer passing claims) while the denominator stays fixed.
- A blocked claim is NOT removed from total_claims — removing it would inflate the score.
- Example: 10 claims, 3 blocked → score = 7/10 = 0.70 (not 7/7 = 1.0)

Where:
- `total_claims` = total number of claims reviewed in this artifact set (the denominator, fixed)
- `tier_5_blocked` = number of claims assigned Tier 5 (SPECULATION) and removed from output
- `passing_claims` = total_claims − tier_5_blocked (the numerator)

## Behavior

| Scenario                        | Score |
|---------------------------------|-------|
| All claims Tier 1–4             | 1.00  |
| 10 claims, 1 blocked            | 0.90  |
| 10 claims, 5 blocked            | 0.50  |
| All claims blocked              | 0.00  |
| No claims reviewed              | 1.00  |

## Thresholds

- **Floor: 0.60** — Below this, return artifact to calling agent for revision. Do NOT deliver to user.
  Set `floor_breached: true` in `truth-tier-audit.json` when score falls below this threshold.
- **Target: 0.85+** — Acceptable quality threshold for artifact delivery

## What Does NOT Affect Score

- Language issues (superlatives, missing attribution) — these are advisory; they appear in `issues[]`
  but do NOT reduce the integrity score
- Tier 2, 3, 4 claims that were successfully reworded — they count as passing

## Relationship to Truth Tier System

Language issues and Tier rewrites are a separate quality signal from the integrity score.
A high integrity score means the claims that ARE in the artifact have evidence backing.
A low integrity score means too many claims were fabricated (Tier 5) and had to be removed.

## Implementation

`scripts/truth_tier_validator.py` — `TruthTierValidator.audit()` computes this score.
See `truth-tiers.md` for the full tier classification system.
