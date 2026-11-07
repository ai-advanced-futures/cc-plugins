---
name: partnerships-structure
description: Design the business, legal, and operational framework for a strategic partnership using Popp's revenue stream model and Gawer's platform leadership framework. Use when the user wants to structure a partnership deal, design revenue share models, build partner program tiers, draft key contractual terms, decide on interface openness, or define the governance model for a partner relationship.
argument-hint: "[session id, or product name, category, target market, existing integrations, partnership goals]"
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py *), Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/simulate_phase.py *)
---

## Routing

**Quick interactive** (the person explores, gives no session id, and asks for no scored analysis): apply the framework of this skill in this conversation, and ask the person for missing facts.

**Full quality** (the person gives a session id, or asks for a scored analysis):

1. Take the session id from `$ARGUMENTS`. Test it before you put it in a command, because the shell reads the value before the script does: it must match `[A-Za-z0-9._-]{1,64}` and must not be `.` or `..`. When it does not, say that the value is not allowed, start no agent, run no command, and stop. With no session id, ask the person for the missing product context fields. Then run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --init`. It prints the new session id.
2. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/simulate_phase.py --phase structure --session-id '<session id>'`. When a script exits 2 (the session id is not a plain name), show its message and stop. Dispatch no agent, and read no file. On LOW confidence, name the missing earlier phases. Then take the quick interactive path.
3. With a session id and no new context, take `product_context` from `.sp-tmp/<session id>/assess.md`. A run with `claude -p` has no person to ask.
4. Otherwise always dispatch `strategic-partnerships:structure-agent` with the `Agent` tool, also when the phase file exists, because the person asked for a new result. Give it `session_id` and `product_context`. Show the path `.sp-tmp/<session id>/structure.md`.

# Partnership Structure Design

Designs the complete business, legal, and operational framework for a strategic partnership — grounding every decision in Popp's revenue stream taxonomy, Popp's hybrid business model concept, Gawer's 4-lever platform leadership framework, and Parker's platform openness and monetization principles.

> **Frameworks used:** Popp's Partner Taxonomy/Spectrum (A), Popp's Business Model Taxonomy (B), Popp's Revenue Stream Model / 6-Attribute Framework (C), Gawer's 4 Levers (D), Parker's Openness Framework (F), Parker's Monetization Principles (G). See `${CLAUDE_PLUGIN_ROOT}/frameworks.md` for full attribution.

## When to Use

- "How should we structure this partnership deal?"
- "Design a reseller program for us"
- "Create an OEM agreement framework"
- "What revenue share model should we use?"
- "Define our partnership tiers (Gold/Silver/Bronze)"
- "Draft the key terms for a co-sell agreement"
- "How should we structure a white-label deal?"
- "Decide how open our APIs should be"
- "Design our partner program"

---

## Phase 1: Identify the Partnership Model (Popp Framework A)

Confirm which of Popp's 6 canonical models applies. The model selection drives every subsequent structural decision:

| Model | Integration | When to Choose |
|-------|-------------|----------------|
| **Referral** | Low | Partner has access to your buyer; minimal joint operations needed |
| **Revenue Share** | Low-Medium | Complementary products; vendor endorses partner's product; non-competitive |
| **Resell (VAR)** | Medium | Partner has sales infrastructure and vertical expertise you lack |
| **OEM** | High | Partner embeds your product into their solution; charges for combined product |
| **Certified Solution** | Medium-High | Proving interoperability; maintaining integration quality standards |
| **Development Cooperation** | Very High | Joint R&D; co-developed IP; shared roadmaps |

**Important (Popp):** Most real-world partnerships are **hybrid models** — stacking multiple archetypes. A reseller partnership may also include a referral component for deals the partner can't close directly, and a certified solution component to validate the integration. Design for the full stack, not a single model.

---

## Phase 2: Define the Business Model Exchange (Popp Framework B)

Map the business model archetype each party plays in the partnership:

| Party | Archetype | What They Provide | What They Receive |
|-------|-----------|------------------|------------------|
| You | [Inventor / IP Lessor / Contractor / Broker] | Software, IP, capability | Revenue, distribution, market access |
| Partner | [Distributor / IP Lessor / Contractor] | Distribution, services, customers | Margin, capabilities, competitive advantage |

This mapping surfaces the **value exchange** at the archetype level — before getting into revenue specifics.

---

## Phase 3: Design the Revenue Model (Popp Framework C — 6 Attributes)

For each revenue stream in the partnership, define all 6 attributes:

### Revenue Stream Design Template

**Stream 1 — [Name, e.g., "License Royalty"]:**
| Attribute | Definition |
|-----------|-----------|
| **Compensator** | Who pays? (e.g., partner pays vendor) |
| **Effect** | Type of payment (financial payment — cash) |
| **Causality** | Linked to which business pattern? (e.g., each OEM copy shipped → IP Lessor pattern) |
| **Rating** | How measured? (e.g., per seat, per API call, per % of partner revenue) |
| **Charging** | Rule for amount (e.g., 20% of partner's list price per seat, tiered above X seats) |
| **Timing** | When payment occurs (e.g., quarterly postpay, based on prior quarter usage report) |

**Stream 2 — [Name, e.g., "Support & Maintenance"]:**
[same 6-attribute definition]

**Stream 3 — [Name, e.g., "Referral Bonus"]:**
[same 6-attribute definition]

**Hybrid model design:** Design the full stack of revenue streams, not just the primary one. Most durable partnerships have 2–4 revenue streams with different timing and charging models, creating mutual financial stickiness.

---

## Phase 4: Openness Architecture Decisions (Parker Framework F, Gawer Framework D)

Every partnership requires explicit decisions on interface openness — these decisions shape what partners can build, what leverage you retain, and how the ecosystem evolves.

### Parker's 3 Openness Dimensions

| Dimension | Options | Decision | Rationale |
|-----------|---------|----------|-----------|
| **Platform governance** | Proprietary (you control all rules) → Shared (consortium/open governance) | | |
| **Developer access** | Closed (no third-party dev) → Open API (anyone can build) | | |
| **User access** | Restricted (approval required) → Open (self-serve) | | |

**Guidance:** Neither fully open nor fully closed is optimal. The right answer depends on:
- Competitive context (are competitors offering more open interfaces?)
- Ecosystem maturity (early ecosystems need more openness to attract complementors)
- Monetization model (closed APIs enable metered charging; open APIs require other monetization)

### Gawer's 4-Lever Platform Leadership Applied to Structure

| Lever | Decision for This Partnership |
|-------|------------------------------|
| **Scope of the firm** | What will you build for the partner vs. let them build? What's inside the partnership vs. available to all partners? |
| **Technology design** | Which APIs / interfaces will you expose? What remains proprietary? Version compatibility SLA? |
| **Complementor relationships** | How will you manage the competitive tension if this partner is also a potential competitor? Exclusivity scope? |
| **Internal organization** | Who owns this partnership internally? What is the decision authority for roadmap requests? |

---

## Phase 5: Partner Program Tier Design

If building a multi-partner program, define tiers using the following structure (Popp's partner model spectrum as the progression path):

```
Partner Program Tiers

Tier 3 — Registered (Entry: Referral / Certified Solution models)
  Requirements:
  - Signed partner agreement (MNDA + framework agreement)
  - 1 certified technical resource
  - Completed product training
  Benefits:
  - Partner portal access (docs, sandbox, deal registration)
  - Standard discount or referral fee
  - Self-serve technical support
  Commitment: None required

Tier 2 — Silver (Mid: Resell / Revenue Share models)
  Requirements:
  - 2+ certified resources
  - Minimum influenced ARR: $[X]/quarter
  - Active pipeline in deal registration system
  Benefits:
  - Enhanced discount (e.g., 30% vs. 20%)
  - MDF (market development funds) eligibility
  - Technical support SLA: 1 business day response
  - MDF (market development funds): 2–5% of quarterly revenue; eligible for co-marketing, events, and technical enablement (claims due within 60 days of quarter-end)
  - Co-marketing rights (logo use, case studies)
  Commitment: $[X] influenced ARR/year

Tier 1 — Gold / Elite (Advanced: OEM / Development Cooperation)
  Requirements:
  - 5+ certified resources
  - Dedicated partnership practice
  - Minimum influenced ARR: $[X]/quarter
  - Executive sponsorship from partner organization
  Benefits:
  - Maximum discount (e.g., 40%)
  - Technical support SLA: 4-hour response; API availability SLA: 99.9%
  - Executive sponsorship from your side
  - Roadmap input (quarterly roadmap review)
  - Joint GTM planning + co-funded campaigns
  - Named technical account manager
  Commitment: $[X] influenced ARR/year + co-invest
```

---

## Phase 6: Contractual Framework

### Core Agreement Components (all partnership models)

| Term | Standard Position | Notes |
|------|------------------|-------|
| **Term & renewal** | 1–3 years; auto-renew with 90-day opt-out | Longer terms for OEM; shorter for referral |
| **Territory** | Non-exclusive by default; limited geo/vertical exclusivity negotiable | Grant broad exclusivity only with strong revenue minimums |
| **IP ownership** | Each party owns its pre-existing IP; jointly developed IP governed by co-dev agreement | Critical for Development Cooperation model |
| **License grant** | Limited, non-transferable, non-sublicensable | Sublicense rights only for OEM |
| **Revenue share mechanics** | Net 30–45 days; quarterly true-up; audit rights | Partner provides usage reports |
| **Support & SLA** | Define what you owe partner's customers | Passthrough SLA for OEM; direct for resell |
| **Data privacy** | GDPR/CCPA DPA, SOC 2 compliance passthrough | The partner agreement flows down to end customers |
| **Termination triggers** | Material breach (30-day cure), insolvency, change of control | |
| **Change of control** | Either party may terminate on 30-day notice upon acquisition | Especially important for OEM |
| **Liability caps** | The cap is 12 months of fees paid | Annual deal value is the lowest sound cap |

### Structural Red Flags to Avoid

| Red Flag | Risk | Mitigation |
|----------|------|-----------|
| Broad exclusivity without revenue minimums | Locks you out of market with no guaranteed return | Require minimum ARR commitment; exclusivity expires if not met |
| Perpetual license without sunset rights | Permanent obligation with no renegotiation leverage | Term limits or renegotiation rights at 3-year intervals |
| IP assignment clauses | You lose ownership of what you built | Licenses only; the vendor keeps the ownership |
| Liability caps below deal value | Underprotected on material breach | A cap of at least 12 months of fees |
| Missing MFN protection | Partner gets worse terms than competitors get | A Most Favored Nation clause for key terms |
| No audit rights on revenue share | Compensation accuracy is unverifiable | Quarterly self-reporting plus an annual audit right |

---

## Phase 7: Deal Economics Summary

Produce a deal-level economics summary for the proposed structure:

```
Deal Economics: [Partner Name] — [Model Type]

Revenue Streams (Popp 6-Attribute Model):
  Stream 1: [Name] — Compensator: [X] — Rating: [Y] — Charging: [Z] — Timing: [T]
  Stream 2: [Name] — ...

Year 1 Projection:
  Gross revenue from partnership:    $[X]
  Program costs (legal, eng, CS):    $[X]
  Net contribution Year 1:           $[X]

Year 3 Projection (scale):
  Influenced ARR:                    $[X]
  Net margin from partnership:       [%]

Payback on program investment:       [Y] months

Open Questions Before Signing:
  - [Question 1]
  - [Question 2]
```

---

## Output Format

```
# Partnership Structure: [Partner Name / Model]

## Model Selected (Popp): [Model + rationale for hybrid if applicable]

## Business Model Exchange (Popp Framework B)
[Archetype mapping: you → partner]

## Revenue Streams (Popp 6-Attribute Model)
[Table: all streams with 6 attributes each]

## Openness Decisions (Parker + Gawer)
[Table: 3 openness dimensions + 4 levers]

## Partner Program Tier (if multi-partner)
[Tier recommendation with requirements and benefits]

## Key Contract Terms
[Summary of critical terms and red flag avoidances]

## Deal Economics
[Year 1 and Year 3 projections]

## Recommended Next Steps
- Run /strategic-partnerships:partnerships-architect for technical integration design
- Run /strategic-partnerships:partnerships-monetize for full financial model across scenarios
```
