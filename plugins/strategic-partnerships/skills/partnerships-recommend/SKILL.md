---
name: partnerships-recommend
description: Synthesize the full strategic partnership analysis into a prioritized action plan with go/no-go decisions, using all validated frameworks from Popp, Gawer, Parker, and Jansen. Use when the user wants a final partnership recommendation, a prioritized execution roadmap, a go/no-go decision framework, a board-ready partnership brief, or a 12-month partnership strategy document.
argument-hint: "[session id]"
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

## Routing

**Quick interactive** (the person explores, or gives no session id): apply the framework of this skill in this conversation, and ask the person for missing facts.

**Full quality** (the person gives a session id, or asks for a scored analysis):

1. Take the session id from `$ARGUMENTS`. With no session id, take the quick interactive path. A full run needs the files of the five earlier phases, and the skill `partnerships` makes them.
2. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/simulate_phase.py --phase synthesize --session-id <session id>`. When a script exits 2 (the session id is not a plain name), show its message and stop. Dispatch no agent, and read no file. On LOW confidence, name the missing earlier phases. Then take the quick interactive path.
3. Otherwise always dispatch `strategic-partnerships:synthesizer` with the `Agent` tool, also when the phase file exists, because the person asked for a new result. Give it `session_id`. Show the path `.sp-tmp/<session id>/synthesize.md`.

# Strategic Partnership Recommendation

Synthesizes all outputs from the partnership analysis workflow into a prioritized, board-ready recommendation — grounding go/no-go decisions in Jansen's ecosystem health and power dynamics research, Parker's network effects framework, Popp's partnership spectrum, and Forrester's 2025 benchmark data.

> **Frameworks used:** All frameworks A–I. Popp's Partner Taxonomy (A), Popp's Business Model Taxonomy (B), Popp's Revenue Stream Model (C), Gawer's 4 Levers (D), Parker's Network Effects (E), Parker's Openness (F), Parker's Monetization Principles (G), Jansen's Ecosystem Health (H), Jansen's Power Dynamics (I), Forrester 2025 benchmarks. See `${CLAUDE_PLUGIN_ROOT}/frameworks.md` for full attribution.

## When to Use

- "Give me a final partnership recommendation"
- "What should we pursue first — which partners?"
- "Create a partnership strategy document"
- "Help me present this to leadership / the board"
- "Prioritize our partnership opportunities"
- "Go/no-go: should we pursue [specific partner]?"
- "Build our 12-month partnership roadmap"

---

## Phase 1: Go / No-Go Decision Framework

### Criteria for GO

All of the following should be true (or a strong majority with mitigation plan for exceptions):

**Revenue criteria:**
- 3-year NPV of partnership revenue ≥ 3× program investment cost (unconditional GO threshold; 2–3× triggers CONDITIONAL GO; <2× is NO-GO)
- Partner-influenced ARR target (Year 3) ≥ 20% of total company ARR *OR* contributes materially to total ARR growth (material = ≥10% of ARR by Year 3)
- Payback period on program investment < 24 months

**Strategic criteria (Jansen Framework H & I):**
- Target ecosystem shows healthy signals: growing productivity, niche creation, partner diversity
- Power position is balanced or in your favor (or you have a credible plan to build leverage)
- Substitutability is low — the partner cannot easily replace your capability

**Network effect criteria (Parker Framework E):**
- Partnership strengthens at least one network effect type (cross-side, same-side, or data-driven)
- Partner's distribution channel adds to your cross-side or same-side effects — it doesn't merely duplicate your existing motion

**Structural criteria:**
- Technical integration complexity is achievable within 90 days for low-integration models; 6 months for high-integration models
- No conflicting exclusivity clauses with existing partners in this geography or vertical
- Partner roadmap is directionally aligned with yours (or not in conflict)

### Criteria for NO-GO

Stop or pause if any of the following are true without clear mitigation:

- 3-year NPV < 2× program investment cost
- Requires broad exclusivity that materially limits future partner acquisition
- Technical integration requires > 9 months with no interim value delivery
- Target ecosystem shows declining health: falling productivity, partner churn, saturation (Jansen Framework H)
- Power position is severely against you AND no credible path to improve leverage
- Partnership would create irrecoverable technical dependency (violates Jansen's multi-homing principle)
- Regulatory, compliance, or reputational risk is unmitigated and material

### Criteria for CONDITIONAL GO

Pursue with explicit prerequisites and a defined re-evaluation point:

- 3-year NPV is between 2× and 3× program investment cost (strong result but below the unconditional GO threshold; pursue with defined milestones and a re-evaluation gate at Month 12)
- Revenue potential is strong (NPV ≥ 2× with prerequisites addressed) but requires 1–2 prerequisite investments (API maturity, partner portal, legal infrastructure)
- Power position is currently against you but a specific capability investment (within 60–90 days) changes the dynamic
- Partner is interested but requires co-investment you can fund only after a defined trigger (funding round, revenue milestone)
- Timeline to material impact is 18+ months — sequence after higher-confidence, faster-impact opportunities

---

## Phase 2: Prioritization Matrix

Score each partnership opportunity across two axes and place in the matrix:

**X-axis — Revenue Impact (weighted score):**
- NPV of partnership (50%)
- Strategic value: network effects strengthened, ecosystem position improved (30%)
- Platform multiple impact: does this move you from product → integrated product → platform? (20%)

**Y-axis — Execution Feasibility:**
- Time to first revenue (40%)
- Technical complexity (30%)
- Legal/contractual complexity (20%)
- Organizational readiness (10%)

```
Prioritization Matrix

                High Feasibility (quick)
                │
  High Impact   │  ● QUICK WINS          │  ● STRATEGIC BETS
  (large NPV,  │  Pursue first;          │  Plan for Q2-Q3;
  platform     │  30-90 day horizon      │  critical but hard
  building)    │                         │
                ├─────────────────────────┤
  Low Impact    │  ● OPPORTUNISTIC        │  ● AVOID
  (small NPV,  │  Take if low effort;    │  Do not invest;
  tactical)    │  don't prioritize       │  deprioritize
                │                         │
                │                         │
                │           Low Feasibility (slow)
```

**Popp's sequencing principle (Framework A):** Start with low-integration models (Referral, Revenue Share) to build trust, generate early revenue signals, and test the relationship — before committing to high-integration models (OEM, Development Cooperation). The spectrum is also an onboarding ramp for partners.

---

## Phase 3: Full Framework Synthesis per Opportunity

For each top-priority opportunity, synthesize all framework outputs:

| Dimension | Framework | Finding | Implication |
|-----------|-----------|---------|-------------|
| Partnership model fit | Popp A | [e.g., OEM] | [deal structure implications] |
| Business model exchange | Popp B | [e.g., IP Lessor → IP Distributor] | [hybrid revenue design] |
| Revenue stream design | Popp C | [6-attribute model] | [specific charging/timing] |
| Platform design decisions | Gawer D | [scope + openness + complementor + org] | [architecture requirements] |
| Network effect leverage | Parker E | [cross-side + same-side + data] | [which effects are strengthened] |
| Openness decision | Parker F | [governance + developer + user] | [API strategy] |
| Monetization approach | Parker G | [transaction fee, freemium, enhanced access] | [pricing model] |
| Ecosystem health | Jansen H | [score across 5 dimensions] | [risk level] |
| Power dynamics | Jansen I | [dependency, substitutability, centrality, alternatives] | [negotiation posture] |
| Revenue potential | Forrester 2025 + model | [3-year NPV, payback period] | [investment decision] |

---

## Phase 4: 12-Month Partnership Execution Roadmap

```
Partnership Execution Roadmap

Q1 — Foundation (Months 1–3)
Goal: Legal, technical, and organizational infrastructure in place; first agreement signed.

  Milestone 1.1 (Month 1): Legal Infrastructure
    [ ] Partner agreement templates finalized (MNDA + framework agreement + order form)
    [ ] Revenue share / royalty model legally documented
    [ ] Reviewed by counsel; approved for execution

  Milestone 1.2 (Month 2): Technical Infrastructure
    [ ] Partner portal MVP launched (deal registration, docs, sandbox access)
    [ ] Sandbox environment provisioned and seeded
    [ ] API documentation published (OpenAPI spec; quickstart guide)

  Milestone 1.3 (Month 3): First Agreement
    [ ] First Tier 1 partner agreement executed
    [ ] Technical onboarding completed (Stage 1 + 2)
    [ ] First co-marketing asset published (case study, press release, or joint blog)

Q2 — Activation (Months 4–6)
Goal: First partner-influenced revenue; first OEM or certified integration live.

  Milestone 2.1 (Month 4): First Revenue Signal
    [ ] First referral or reseller deal closed (partner-influenced)
    [ ] Deal registration system validated with live data
    [ ] Partner satisfaction surveyed (NPS baseline)

  Milestone 2.2 (Month 5–6): Integration Live
    [ ] First OEM integration certified and live (if applicable)
    [ ] Tier 2 pipeline: 3–5 partners in onboarding
    [ ] Partner newsletter launched (bi-monthly cadence)

Q3 — Scale (Months 7–9)
Goal: Multiple Tier 1 partners producing; channel contributing measurable ARR.

  Milestone 3.1 (Month 7–8): Program Scale
    [ ] 2+ Tier 1 partners hitting quarterly targets
    [ ] Reseller program open (self-serve application; auto-approval for Registered tier)
    [ ] Partner-influenced ARR: $[X] (benchmark: on track for Forrester >30% growth target)

  Milestone 3.2 (Month 9): Governance
    [ ] First Quarterly Business Review (QBR) with top partners completed
    [ ] Partner advisory board established (2–4 Tier 1 partners)
    [ ] Roadmap review process formalized

Q4 — Optimization (Months 10–12)
Goal: Program profitability validated; 2026 strategy planned.

  Milestone 4.1 (Month 10–11): Optimization
    [ ] Program ROI reviewed vs. business case
    [ ] Underperforming partnerships addressed (tier downgrade or exit)
    [ ] Top partners renewed or expanded to next tier

  Milestone 4.2 (Month 12): Next Year Planning
    [ ] 2026 partnership strategy presented to leadership
    [ ] Partner-sourced pipeline: target [X]% of total pipeline
    [ ] Annual program review published internally
```

---

## Phase 5: Risk Register (Jansen + Parker)

| Risk | Driver | Likelihood | Impact | Mitigation |
|------|--------|-----------|--------|-----------|
| Partner prioritizes competitor | Low power asymmetry; competitor offers better terms | Medium | High | Exclusivity in specific vertical; stronger co-invest; differentiated capabilities |
| Integration delayed by partner engineering | High technical complexity; low partner prioritization | High | Medium | Milestone-based agreement; technical milestones = payment triggers |
| Revenue share disputes | Unclear attribution; audit rights not enforced | Low | High | Clear attribution model in contract; quarterly self-reporting; annual audit right |
| Partner acquired by competitor | Change of control event; new owner changes direction | Low | High | Change-of-control termination clause; 90-day wind-down provision |
| Ecosystem health decline | Platform pivot; market consolidation; technology shift | Medium | High | Diversify across 3+ ecosystems; monitor Jansen health metrics quarterly |
| Over-dependency on one partner | Single partner generates >40% of partner-influenced ARR | Medium | High | Actively diversify; Tier 2 pipeline always active; multi-homing architecture |
| Network effect dampening (Parker G) | Over-monetization; excessive fees reduce partner participation | Low (if monitored) | High | Quarterly participation metrics; review monetization if partner churn rises |

---

## Phase 6: Board-Ready Partnership Brief

```
# Strategic Partnership Strategy — [Company Name]
# Prepared for: [Audience — Board / Executive Team / Investors]
# Date: [Date]

## Executive Summary
[2–3 sentences: what ecosystem position we're pursuing, why now,
and the expected 3-year outcome in revenue and strategic terms]

## Market Context (Forrester 2025)
- 67% of B2B companies expect partner-influenced revenue to grow >30% YoY
- Companies with strong partner ecosystems grow 5× faster than those without
- Platform companies command 8.2× revenue multiples vs. 3.9× for traditional SaaS
- [Company] is positioned to capture this opportunity through [specific strategy]

## Our Partnership Portfolio
| Partnership Type | # Partners (Target) | ARR Target (Year 3) | Model |
|-----------------|---------------------|---------------------|-------|
| [Type 1] | | | |
| [Type 2] | | | |
| [Type 3] | | | |

## Strategic Framework Applied
Recommendations are grounded in:
- Popp & Meyer's validated partnership taxonomy (SAP ecosystem research)
- Gawer & Cusumano's platform leadership framework (MIT/Surrey)
- Parker et al.'s network effects and ecosystem monetization research (Dartmouth/BU)
- Jansen's ecosystem health and power dynamics research (Utrecht University)
- Forrester's 2025 State of B2B Partner Ecosystems data

## Investment Required
- One-time infrastructure: $[X]
- Annual program operating cost: $[X]
- Headcount: [N] FTEs (partner success, partner engineering)
- Total 3-year investment: $[X]

## Expected Returns
- Year 1 partner-influenced ARR: $[X]
- Year 3 partner-influenced ARR: $[X] ([Z]% of projected total ARR)
- 3-year NPV of program: $[X]
- Payback period: [Y] months
- Estimated valuation impact (platform multiple): $[X] → $[Y]

## First 90 Days
1. [Action] — [Owner] — [Week target]
2. [Action] — [Owner] — [Week target]
3. [Action] — [Owner] — [Week target]
```

---

## Full Workflow Summary

This skill synthesizes the complete `strategic-partnerships` workflow:

| Phase | Skill | Primary Frameworks | Output |
|-------|-------|--------------------|--------|
| 1. Readiness | `/strategic-partnerships:partnerships-assess` | Popp B+C+A, Parker E, Jansen H+I | Readiness scorecard; gap list; power position |
| 2. Discovery | `/strategic-partnerships:partnerships-discover` | Popp A, Gawer D, Jansen H+I | Tier 1–3 partner map; ecosystem health |
| 3. Structuring | `/strategic-partnerships:partnerships-structure` | Popp A+B+C, Gawer D, Parker F+G | Deal economics; contract terms; program tiers |
| 4. Architecture | `/strategic-partnerships:partnerships-architect` | Gawer D, Parker F, Jansen I | Technical blueprint; DX plan; openness decisions |
| 5. Monetization | `/strategic-partnerships:partnerships-monetize` | Popp B+C, Parker G, Forrester 2025 | Revenue model; ROI; platform multiple |
| 6. Decision | `/strategic-partnerships:partnerships-recommend` | All frameworks A–I | Go/no-go; roadmap; board brief |
