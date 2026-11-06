---
name: partnerships-assess
description: Evaluate a software product's current market position, business model archetype, ecosystem power dynamics, and readiness for strategic partnerships. Use when the user wants to assess partnership readiness, evaluate ecosystem fit, audit current partnerships, analyze competitive moats, understand partner leverage, or identify gaps before approaching partners.
argument-hint: "[session id, or product name, category, target market, existing integrations, partnership goals]"
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

## Routing

**Quick interactive** (the person explores, gives no session id, and asks for no scored analysis): apply the framework of this skill in this conversation, and ask the person for missing facts.

**Full quality** (the person gives a session id, or asks for a scored analysis):

1. Take the session id and the product context from `$ARGUMENTS`. Ask the person for each missing field: product name, category, target market, existing integrations, and partnership goals.
2. With no session id, run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --init`. It prints the new session id.
3. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/simulate_phase.py --phase assess --session-id <session id>`. When a script exits 2 (the session id is not a plain name), show its message and stop. Dispatch no agent, and read no file. On LOW confidence, name the missing earlier phases. Then take the quick interactive path.
4. Otherwise always dispatch `strategic-partnerships:assess-agent` with the `Agent` tool, also when the phase file exists, because the person asked for a new result. Give it `session_id` and `product_context`. Show the path `.sp-tmp/<session id>/assess.md`.

# Strategic Partnership Assessment

Evaluates a software product's current position and readiness to enter, expand, or restructure strategic partnerships within a software ecosystem — using validated frameworks from Popp & Meyer, Parker et al., and Jansen.

> **Frameworks used:** Popp's Business Model Taxonomy (B), Popp's Revenue Stream Model (C), Popp's Partner Taxonomy (A), Parker's Network Effects Typology (E), Jansen's Ecosystem Health Indicators (H), Jansen's Power Dynamics (I). See `${CLAUDE_PLUGIN_ROOT}/frameworks.md` for full attribution.

## When to Use

- "Assess my partnership readiness"
- "What's our current ecosystem position?"
- "Should we be looking for strategic partners?"
- "Audit our existing partnerships"
- "What leverage do we have as a potential partner?"
- "Evaluate our product for OEM or white-label opportunities"
- "Analyze our competitive moat before approaching partners"

---

## Phase 1: Business Model Archetype Classification (Popp Framework B)

Classify the product against Popp's three-component taxonomy to understand the natural partnership surface:

**Step 1.1 — Type of Goods Provided:**
- Financial goods (cash, financial instruments)
- Physical goods (hardware, devices)
- **Intangible goods** (software, IP, data, knowledge, brand) ← most software products
- Human goods (professional services, expertise)

**Step 1.2 — Business Model Archetype(s) in Use:**
| Archetype | Definition | Partnership Implication |
|-----------|-----------|------------------------|
| **Inventor / Creator** | Designs and builds original IP | Natural OEM licensor; can supply to partners |
| **IP Lessor** | Licenses access to IP without ownership transfer | Reseller and OEM deals are natural extensions |
| **IP Distributor** | Resells others' IP | Certification partnerships; marketplace plays |
| **Contractor** | Sells human services (support, consulting, implementation) | GSI/consulting ecosystem plays |
| **Broker** | Matches buyers and sellers | Platform/marketplace model; referral programs |

Most vendors are hybrid. Identify which archetypes are active and which are latent (potential future revenue streams).

**Step 1.3 — Current vs. Latent Revenue Streams (Popp Framework C):**

Map each active revenue stream against the 6 attributes:

| Revenue Stream | Compensator | Effect | Rating | Charging | Timing | Causality |
|---------------|-------------|--------|--------|----------|--------|-----------|
| [Stream 1] | | | | | | |
| [Stream 2] | | | | | | |

Then map each **latent partnership revenue stream** — revenue not yet captured that partnership could unlock.

---

## Phase 2: Competitive Moat Analysis (Parker Framework E — Network Effects)

Assess the strength and type of network effects present:

| Network Effect Type | Present? | Strength (1–5) | Assessment |
|--------------------|----------|----------------|------------|
| **Cross-side** (buyers attract sellers, or vice versa) | | | How does adding one partner type benefit the other side? |
| **Same-side** (users benefit other users) | | | Developer ecosystem; community; OSS contribution model |
| **Data-driven** (more users → better product) | | | AI/ML quality improvement loop; training data advantages |

**Moat strength implications for partnership:**
- Strong network effects → high partnership leverage (partners need you more than you need them)
- Weak network effects → need partnership to acquire distribution or features faster than organic growth
- No network effects → partnership is primarily a distribution or revenue play

**Other moat factors to assess:**
- Switching costs (integrations, data, trained workflows)
- IP / patents
- Brand and category leadership
- Regulatory certification / compliance

---

## Phase 3: Ecosystem Position & Power Dynamics (Jansen Frameworks H & I)

**Step 3.1 — Ecosystem Health Assessment:**

| Health Dimension | Current State | Score (1–5) | Notes |
|-----------------|---------------|-------------|-------|
| **Productivity** | Partners actively building/shipping? | | |
| **Robustness** | Can ecosystem survive platform pivots? | | |
| **Niche creation** | New partner types still emerging? | | |
| **Longevity** | Platform + key partners growing YoY? | | |
| **Diversity** | Mix of partner sizes, verticals, models? | | |

**Step 3.2 — Power Dynamics Audit:**

Score the power balance with current or target partners:

| Power Factor | Your Position | Partner Position | Net Power Balance |
|-------------|---------------|-----------------|-------------------|
| **Dependency** (who needs whom more?) | | | |
| **Substitutability** (can either party be replaced?) | | | |
| **Centrality** (who is more central to the ecosystem?) | | | |
| **Alternatives** (how many comparable options exist?) | | | |

Net power balance interpretation:
- **Strongly in your favor** → you can impose terms; risk of over-exploiting (kills partnership)
- **Balanced** → negotiate as equals; most durable partnerships live here
- **Against you** → must offer exceptional value to attract; consider alternative partners

---

## Phase 4: Partnership Model Readiness (Popp Framework A — Spectrum)

Assess readiness for each of Popp's 6 canonical partnership models, ordered from lowest to highest integration:

| Model | Integration | Readiness Score (1–5) | Key Gap |
|-------|-------------|----------------------|---------|
| **Referral** | Low | | Lead tracking, referral portal |
| **Revenue Share** | Low-Medium | | Complementary product mapping, attribution model |
| **Resell (VAR)** | Medium | | Reseller agreement, discount structure, channel manager |
| **OEM** | High | | Licensing framework, royalty model, embedded support SLA |
| **Certified Solution** | Medium-High | | Certification program, test suite, partner portal |
| **Development Cooperation** | Very High | | Joint roadmap process, IP ownership agreement, dev capacity |

**Quick win identification:** Models scoring ≥3 with a single identifiable gap are candidates for 30–90 day activation. A gap is counted at the domain level: legal, technical, organizational, or commercial. A model with gaps in only one domain qualifies as a quick win regardless of how many individual items within that domain need attention.

---

## Phase 5: Readiness Scorecard Summary

Consolidate into a 10-point readiness scorecard:

| Dimension | Score (1–5) | Notes |
|-----------|-------------|-------|
| Business model clarity (can you articulate the partnership value exchange?) | | |
| Revenue model defined (do you know how the partner makes/saves money?) | | |
| Legal & contractual infrastructure (agreement templates, NDA, etc.) | | |
| Technical integration readiness (APIs, SDKs, sandbox, docs) | | |
| Partner portal / onboarding infrastructure | | |
| Sales & channel readiness (channel manager, deal registration) | | |
| Network effect leverage (do you have something partners need to access?) | | |
| Ecosystem health (is this ecosystem worth partnering with?) | | |
| Power position (do you have enough leverage to attract the right partners?) | | |
| Organizational readiness (dedicated partnership team / bandwidth) | | |

**Overall readiness:**
- 40–50: Ready to pursue partnerships aggressively
- 25–39: Ready for low-integration models (referral, revenue share); build toward higher models
- 10–24: Significant gaps; prioritize remediation before approaching partners

---

## Output Format

```
# Partnership Readiness Assessment: [Product Name]

## Executive Summary
[2–3 sentences on position and single most important recommendation]

## Business Model Archetype (Popp)
[Current hybrid model; latent revenue streams identified]

## Network Effects Profile (Parker)
[Type, strength, and strategic implication]

## Ecosystem Power Position (Jansen)
[Power balance; health score]

## Partnership Readiness by Model (Popp Spectrum)
[Table: model → readiness score → key gap]

## Top 3 Gaps to Close
1. [Gap] — [Impact] — [Remediation] — [Timeline]

## Recommended Next Steps
- Run /strategic-partnerships:partnerships-discover to map the partner landscape
- Run /strategic-partnerships:partnerships-structure to design the deal model for your readiest partnership type
```
