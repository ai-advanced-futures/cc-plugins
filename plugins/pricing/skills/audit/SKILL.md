---
name: audit
description: Audit existing features for AI-era classification and pricing antipatterns using the two-layer Amadeo rubric (Layer 1 fast triage, Layer 2 high-multiplier gate). Classifies each feature as AI_ERA, HYBRID, or LEGACY and outputs a time-bound review schedule.
---

# Audit — AI-Era Classification

Classify your existing features and detect pricing antipatterns before you over- or underprice your AI-era capabilities.

## When to Use

- "Audit our current pricing"
- "Which of our features are legacy vs AI-era?"
- "Are we pricing our AI features correctly?"
- "Run a pricing review across our tier structure"
- "Which features should get the AI premium?"

## Classification Rubric

### Layer 1 Fast Triage (all features, 5 dimensions)

| Dimension | Score |
|-----------|-------|
| Uses ML/AI inference as primary value delivery | 0 or 1 |
| Quality improves as feature accumulates data/usage | 0 or 1 |
| Faster outcome delivery than manual/non-AI alternative | 0 or 1 |
| AI mechanism is direct cause of value (not just data) | 0 or 1 |
| AI capability rare in current competitive landscape | 0 or 1 |

- **0–2** → LEGACY (no AI premium)
- **3–4** → HYBRID (partial AI premium)
- **5** → Provisionally AI_ERA → Layer 2 gate

### Layer 2 High-Multiplier Gate (when AI_MULTIPLIER > 5× projected)

All three required:
1. **Autonomy** — executes without human intervention
2. **Compounding** — value grows with usage over time
3. **Attribution** — Speed × Accuracy isolatable vs. non-AI equivalent

If any fails → AI_MULTIPLIER capped at 5×.

### Review Window

`review_window_months = 36 / log₂(1 + competitor_count)` clamped to [6, 36]

## Flow

1. Collect feature list from user or codebase
2. Apply Layer 1 triage to each feature (5 dimensions)
3. Apply Layer 2 gate to any feature scoring 5/5
4. Compute review window per feature
5. Detect Ramanujam failure modes (Feature Shock, Minivations, Hidden Gems, Undead Features)
6. Detect per-user antipattern
7. Output `.pricing/audit-report.md` and `.pricing/audit-data.json`

## Output

- `.pricing/audit-report.md` — human-readable classification + review schedule
- `.pricing/audit-data.json` — machine-readable feature classifications

## Cross-References

- **Next step:** `/pricing:price` — compute RIGHT_PRICE for each AI_ERA or HYBRID feature
- **Orchestrated by:** `pricing-auditor` agent for full end-to-end audit workflow
- **Full prompt:** See `audit.md` in this directory
