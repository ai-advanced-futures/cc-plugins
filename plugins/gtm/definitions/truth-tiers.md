# Truth Tier System — Canonical Definition

The Truth Tier System classifies every marketing and sales claim by the strength of its evidence basis.
All claims in GTM artifacts must be assigned a tier. Tier 5 claims are always removed.

| Tier | Label            | Evidence Basis                                                        | Required Language                                    |
|------|------------------|-----------------------------------------------------------------------|------------------------------------------------------|
| 1    | SHIPPED          | Feature is live in production; customers actively use it              | Assert as fact: "X does Y"                           |
| 2    | IN-FLIGHT        | Feature is actively under development; expected in weeks              | "Coming soon", "in development", "launching [Q/yr]"  |
| 3    | COMMITTED        | On roadmap with budget, exec sponsor, and assigned dev resources      | "Planned for [timeframe]", "on our roadmap for [Q]"  |
| 4    | STRATEGIC INTENT | Direction set; no committed plan or budget yet                        | "We plan to explore", "our direction includes"       |
| 5    | SPECULATION      | No evidence basis — inference, aspiration, or invention               | **BLOCKED — never appears in any output**            |

## Tier Assignment Rules

- Evidence in `product.capabilities[]` + live in production → Tier 1
- Evidence in `product.capabilities[]` + under active development → Tier 2
- Evidence in roadmap doc with budget and exec sponsor → Tier 3
- Stated direction without committed plan → Tier 4
- No evidence or inference only → Tier 5 (blocked)
- Value-ip survived claims without explicit production evidence → Tier 3 (COMMITTED) by default

## Superlatives and Quantified Claims

- Superlatives ("best", "fastest", "leading", etc.) require verifiable benchmark evidence to qualify as Tier 1
- Without evidence, superlatives are Tier 5 and must be removed
- Quantified claims ("[X]% improvement") require an attributed source in parentheses
- Without attribution, quantified claims are Tier 5 and must be removed

## Integrity Score Formula

```
integrity_score = (total_claims - tier_5_blocked) / total_claims
```

- Range: 0.0 to 1.0
- Floor: 0.60 (below this, return artifact to calling agent for revision)
- Target: 0.85+
- Empty claim set: score = 1.0 (no violations)
- All blocked: score = 0.0

## Value-IP Survived Claims

Claims that have survived the value-ip 4-framework debate are classified as **Tier 3 (COMMITTED)**
by default — not Tier 1 (SHIPPED). Rationale: surviving a debate framework proves the claim is
defensible as a strategic position, but does NOT prove the capability is live in production.
Only explicit production deployment evidence (live customers using the feature) elevates to Tier 1.

## Cross-References

This file is the canonical source for the Truth Tier System. Other references:
- `integrity-agent.md` — applies this system claim-by-claim to every artifact
- `codebase-scanner.md` — maps codebase sources to Truth Tiers for capability extraction
- `knowledge-agent.md` — maps ingested document types to Truth Tiers
- `integrity-score.md` — defines the integrity score formula derived from tier assignments
- `scripts/truth_tier_validator.py` — Python implementation of tier classification

## Agent Application

`integrity-agent` applies this system to every artifact before delivery to the user.
No artifact bypasses the integrity-agent. See `integrity-score.md` for full score formula details.
