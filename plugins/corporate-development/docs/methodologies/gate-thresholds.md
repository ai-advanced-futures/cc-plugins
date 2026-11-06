# M&A Pipeline Gate Thresholds

Single source of truth for GO / CONDITIONAL / NO_GO decision boundaries across all 7 phases.

---

## Phase 0 — Acquisition Readiness

**Scoring weights:** CEO Readiness 30%, Strategic Clarity 20%, Organizational Capability 25%, Financial Readiness 15%, Governance Framework 10%

| Gate | Score Range | Meaning |
|------|-------------|---------|
| GO | 80–100 | Organization ready to begin M&A activity |
| CONDITIONAL | 65–79 | Ready with specific gaps to address before closing |
| NO_GO | < 65 | Critical readiness deficiencies; pause until resolved |

**Hard NO_GO triggers (regardless of score):**
- CEO 3 A's average score < 7.0 / 10
- No strategic acquisition targets defined
- No committed capital for acquisition

---

## Phase 1 — Deal Sourcing

**Gate logic:** Information-gathering phase — always returns GO when required inputs are valid.

| Gate | Condition |
|------|-----------|
| GO | Required inputs present (`target_markets`, `strategic_focus`, `budget_range`) |
| NO_GO | Required inputs missing or malformed |

Score is `null` (not applicable for this phase).

---

## Phase 2 — Target Assessment

**Scoring weights:** Strategic Fit 35%, Market Opportunity 25%, Competitive Position 20%, Risk Factors 20%

| Gate | Score Range | Meaning |
|------|-------------|---------|
| GO | 70–100 | Strong strategic fit; proceed to due diligence |
| CONDITIONAL | 50–69 | Conditional fit; specific concerns to validate |
| NO_GO | < 50 | Poor strategic fit or disqualifying risk factors |

**Hard NO_GO trigger:** `company_name` not provided (structural input error).

---

## Phase 3 — Operational Due Diligence

**Scoring weights:** Team 25%, Technology 25%, Product 20%, Operations 20%, Market Position 10%

Each sub-dimension scored 0–100; overall health = weighted composite.

| Gate | Score Range | Meaning |
|------|-------------|---------|
| GO | 70–100 | Acceptable operational health; proceed to Phase 5 |
| CONDITIONAL | 50–69 | Proceed with documented remediation plan |
| NO_GO | 0–49 | Operational risks too severe to proceed |

**Special case:** If no dimension objects are provided → CONDITIONAL with `phase_3_not_assessed: true`.

---

## Phase 4 — Financial Due Diligence

**Scoring weights:** Revenue Quality 30%, Unit Economics 25%, Profitability 20%, Growth 15%, Valuation 10%

| Gate | Score Range / Condition | Meaning |
|------|------------------------|---------|
| GO | Financial health > 70, LTV/CAC > 2.5, recurring revenue > 70% | Strong financials |
| CONDITIONAL | Financial health 50–70 with clear improvement path | Proceed with conditions |
| NO_GO | Financial health < 50, unsustainable unit economics, or > 50% single-customer concentration | Do not proceed |

---

## Phase 5 — Integration Planning

**Gate logic:** Qualitative assessment based on integration complexity and risk.

| Gate | Condition |
|------|-----------|
| GO | Low–moderate integration complexity; clear execution plan |
| CONDITIONAL | High complexity but manageable with sufficient resources/timeline |
| NO_GO | Integration complexity renders deal value-destructive |

Score is `null` (qualitative phase).

---

## Phase 6 — Deal Decision

**Gate logic:** Synthesizes all prior phase gates and scores into a final recommendation.

| Gate | Condition |
|------|-----------|
| GO | All phases GO or CONDITIONAL with mitigable risks; expected value positive |
| CONDITIONAL | Mixed phase outcomes; proceed subject to specific closing conditions |
| NO_GO | Any Phase 0/2 hard NO_GO unresolved, or weighted risk profile unacceptable |

Score is `null` (synthesis phase).

---

## Pipeline-Level Behavior

| Phase NO_GO | Pipeline behavior |
|-------------|-------------------|
| Phase 0 | Stop immediately — acquirer not ready |
| Phase 1 | Stop — sourcing inputs invalid (rare) |
| Phase 2 | Stop — target fails strategic fit |
| Phase 3 | Stop — target fails operational threshold |
| Phase 4 | Stop — target fails financial threshold |
| Phase 5 | Stop — integration deemed value-destructive |
| Phase 6 | Pipeline complete with NO_GO recommendation |

**CONDITIONAL never stops the pipeline.** Conditions are documented and carried to Phase 6 for final synthesis.
