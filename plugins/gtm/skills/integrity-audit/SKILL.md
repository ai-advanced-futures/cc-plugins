---
name: integrity-audit
description: Run a full Truth Tier audit on any marketing artifact — surface blocked claims and compute integrity score
---

# GTM Audit

## Purpose

Audit any marketing artifact (pitch deck, campaign copy, positioning statement, website copy, sales email sequence) for Truth Tier compliance. Produces a `truth-tier-audit.json` with an integrity score and a blocked claim list.

## When to Use

- Before delivering any GTM artifact to the user
- When the user requests `/gtm:audit` on a specific artifact
- As the final gate in every agent workflow (integrity-agent runs this on every path)
- When auditing existing marketing materials for compliance

## Audit Protocol

### Step 1: Load the Artifact
Read the artifact text. Identify the artifact type (positioning, pitch, email, website copy, etc.).

### Step 2: Extract All Claims
A claim is any statement about the product, its capabilities, its customers, its market position, or its future. Extract every claim as a discrete item.

### Step 3: Classify Each Claim
Apply the Truth Tier System (see the skill `integrity-truth-tier-system`) to each claim. Assign tier 1-5.

### Step 4: Run Language Checks
For each claim: check for superlatives, unsourced quantified claims, future-tense-as-present, enthusiasm without evidence.

### Step 5: Block Tier 5 Claims
Any Tier 5 claim is blocked. Provide a suggested rewrite at Tier 3-4 level.

### Step 6: Compute Integrity Score
`score = max(0.0, 1.0 - (blocked_count / total_claims) - (language_issue_count * 0.05))`

### Step 7: Produce Output
Write `truth-tier-audit.json` (see schema in `${CLAUDE_PLUGIN_ROOT}/schemas/truth-tier-audit.json`).

### Step 8: Report to User
Present:
- Integrity score (0-1, target ≥ 0.8)
- Blocked claims with suggested rewrites
- Language issues with fixes
- Overall verdict: CLEAN / NEEDS REVISION / BLOCKED
