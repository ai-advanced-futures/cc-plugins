---
name: partnerships-discover
description: Map the software ecosystem to identify, classify, and rank strategic partnership candidates using Popp's canonical partnership taxonomy and Jansen's power dynamics framework. Use when the user wants to find potential partners, map the competitive ecosystem, discover partner programs to join, identify OEM or reseller candidates, find integration opportunities, or understand where they sit in the ecosystem's power structure.
argument-hint: "[session id, or product name, category, target market, existing integrations, partnership goals]"
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/*)
---

## Routing

**Quick interactive** (the person explores, gives no session id, and asks for no scored analysis): apply the framework of this skill in this conversation, and ask the person for missing facts.

**Full quality** (the person gives a session id, or asks for a scored analysis):

1. Take the session id from `$ARGUMENTS`. With no session id, ask the person for the missing product context fields. Then run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/session_manager.py --init`. It prints the new session id.
2. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/simulate_phase.py --phase discover --session-id <session id>`. When a script exits 2 (the session id is not a plain name), show its message and stop. Dispatch no agent, and read no file. On LOW confidence, name the missing earlier phases. Then take the quick interactive path.
3. With a session id and no new context, take `product_context` from `.sp-tmp/<session id>/assess.md`. A run with `claude -p` has no person to ask.
4. Otherwise always dispatch `strategic-partnerships:discover-agent` with the `Agent` tool, also when the phase file exists, because the person asked for a new result. Give it `session_id` and `product_context`. Show the path `.sp-tmp/<session id>/discover.md`.

# Partner Ecosystem Discovery

Maps the software ecosystem surrounding a product to surface, classify, and rank strategic partnership candidates — using Popp's validated partner taxonomy, Gawer's complementor framework, and Jansen's power dynamics model.

> **Frameworks used:** Popp's Partner Model Taxonomy/Spectrum (A), Gawer's 4 Levers — Complementor relationships (D), Jansen's Ecosystem Health (H) and Power Dynamics (I). See `${CLAUDE_PLUGIN_ROOT}/frameworks.md` for full attribution.

## When to Use

- "Find potential partners for my product"
- "Map the ecosystem around [product/category]"
- "What partner programs should we join?"
- "Identify integration opportunities"
- "Who should we approach for an OEM deal?"
- "Discover reseller or VAR channel candidates"
- "Find open source projects to partner with"
- "Where do we sit in this ecosystem's power structure?"

---

## Phase 1: Ecosystem Boundary Setting

Before discovering candidates, define the ecosystem boundaries:

**1.1 — Value Chain Position:**
Where does your product sit in the software industry value chain (Popp)?
- **Upstream:** Infrastructure, platform, data layer — enables other products
- **Midstream:** Application layer — solves a specific business problem
- **Downstream:** Services, implementation, support — wraps the application layer

Your value chain position determines which partner models are natural for you (see Phase 3).

**1.2 — Ecosystem Topology:**
Map the actors in your ecosystem:
- **Platform owner** — controls the core platform and its governance
- **Key complementors** — build critical extensions that drive platform value
- **Aggregators** (Gawer, 2025) — new type of complementor that bundles multiple platform services
- **Consumers** — end users of the platform or complementors' products
- **Competing platforms** — alternative ecosystems vying for the same complementors

Which role do you play today? Which role could you play with a partnership?

---

## Phase 2: Partner Candidate Discovery by Popp Model

Systematically identify candidates for each of Popp's 6 partnership models. Work through each model type and populate candidates:

### Model 1: Referral Candidates (Low Integration)
Criteria: Organizations with access to your buyer that are not in your sales motion.
- Who sells to your ICP (ideal customer profile) but doesn't compete with you?
- Who has relationships with your buyer's economic decision-maker?
- What consultancies or advisors do your buyers trust?

Candidate sources:
- Industry analyst firms and advisory shops
- Professional associations in your vertical
- Complementary SaaS vendors with overlapping customer bases
- Independent consultants and implementation partners

### Model 2: Revenue Share Candidates (Low-Medium Integration)
Criteria: Complementary products where endorsement flows naturally; non-competitive.
- What products do your customers use alongside yours (the "before/after" workflow)?
- What vendors actively recommend your category to their customers?
- Where does your product appear in another vendor's integration marketplace?

Candidate sources:
- Vendor integration marketplaces (Salesforce AppExchange, HubSpot, etc.)
- G2/Capterra "frequently compared with" data
- Customer surveys: "What other tools do you use with this product?"

### Model 3: Resell / VAR Candidates (Medium Integration)
Criteria: Organizations with sales infrastructure to reach your target market; capacity to add services wrap.
- Which regional or vertical-specific VARs already serve your ICP?
- Which Managed Service Providers (MSPs) serve your target infrastructure stack?
- Which System Integrators (SIs) implement solutions in your category?
- Which Global System Integrators (GSIs) have practices in your vertical?

Candidate sources:
- Major GSIs: Accenture, Deloitte, KPMG, PwC, Capgemini, Wipro, Infosys, TCS
- Regional VARs and boutique consultancies
- Vertical-specific IT service firms (e.g., healthcare IT, financial services IT)
- Cloud marketplace ISVs already selling to your buyer

### Model 4: OEM Candidates (High Integration)
Criteria: Organizations that lack your core capability and serve an overlapping customer base; would benefit from embedding your product without building it.
- Which larger platforms have a gap your product fills?
- Which vertical SaaS players need your horizontal capability (auth, payments, search, analytics, etc.)?
- Which hardware or device manufacturers need embedded software?
- Which enterprise software vendors are building adjacent to your space?

Candidate sources:
- Direct competitors' ecosystem partners (they need your capability but can't use your competitor)
- Platform vendors adjacent to your category
- Enterprise software megasuites that prefer to buy a capability in place of a build

### Model 5: Certified Solution Candidates (Medium-High Integration)
Criteria: Products that need to prove interoperability with yours for their customers to trust both.
- Which vendors' customers regularly ask "does it work with [your product]?"
- Which standards bodies or certification programs are relevant in your industry?
- Which compliance frameworks require certified tooling?

Candidate sources:
- Customer support tickets: "does it work with X?"
- Community forums: "how do I integrate with Y?"
- Industry compliance frameworks (SOC 2, HIPAA, ISO 27001, FedRAMP)
- Technology alliances (e.g., CNCF, OpenID Foundation, etc.)

### Model 6: Development Cooperation Candidates (Very High Integration)
Criteria: Organizations with complementary technical capabilities and aligned roadmaps; joint product is better than either alone.
- Which vendors are solving adjacent problems and could co-build a better combined solution?
- Which open source foundations have projects your product could co-develop?
- Which research institutions or standards bodies are working on problems you're solving?

---

## Phase 3: Partner Scoring and Ranking

Score each identified candidate across four dimensions:

| Criterion | Weight | Scoring Guidance |
|-----------|--------|-----------------|
| **Audience Overlap** | 30% | % of their active customers who match your ICP. Score 1–5: 1=<10%, 5=>60% |
| **Strategic Fit** | 25% | Roadmap and mission alignment; cultural compatibility. Score 1–5 |
| **Revenue Potential** | 25% | Estimated partner-influenced ARR in 24 months. Score 1–5: 1=<$50k, 5=>$1M |
| **Execution Feasibility** | 20% | Time, cost, and risk of establishing the partnership. Score 1–5: 1=18+ months, 5=<30 days |

**Composite score** = [(Audience × 0.30) + (Strategic × 0.25) + (Revenue × 0.25) + (Feasibility × 0.20)] × 4

Priority assignment:
- Score > 16: Priority A — Pursue immediately
- Score 12–15: Priority B — Pursue within 6 months
- Score < 12: Priority C — Monitor; revisit at next planning cycle

---

## Phase 4: Power Dynamics Assessment per Candidate (Jansen Framework I)

For each Priority A candidate, assess the power balance before outreach:

| Power Factor | Your Position | Partner Position | Net Balance |
|-------------|---------------|-----------------|-------------|
| **Dependency** (who needs whom more?) | | | |
| **Substitutability** (can either be replaced?) | | | |
| **Centrality** (who is more central to the ecosystem?) | | | |
| **Alternatives** (how many comparable options?) | | | |

**Negotiation stance based on power balance:**
- Power in your favor → assertive terms; risk of overplaying hand
- Balanced → collaborative negotiation; build long-term trust
- Power against you → lead with exceptional value prop (exceptional = at least 2 of: unique capability not easily replicated, significant cost savings >30% for partner, or direct access to an otherwise-inaccessible customer segment); consider starting with lower-integration model (referral → resell) before committing to OEM

---

## Phase 5: Ecosystem Health Check (Jansen Framework H)

For each ecosystem you're considering joining or building, assess:

| Health Dimension | Ecosystem A | Ecosystem B | Notes |
|-----------------|-------------|-------------|-------|
| Productivity (active partner output) | | | |
| Robustness (survives disruption) | | | |
| Niche creation (new partner types emerging) | | | |
| Longevity (YoY growth) | | | |
| Diversity (partner size/vertical mix) | | | |

**Red flags:** Any ecosystem with declining productivity + low diversity is a risky bet regardless of current platform size.

---

## Output Format

```
# Partner Ecosystem Map: [Product Name]

## Ecosystem Boundary
[Value chain position; role today; target role]

## Priority A — High Priority (score > 16)
| Partner | Model Type | Score | Audience Overlap | Revenue Est. | Power Balance | Action |
|---------|-----------|-------|-----------------|--------------|---------------|--------|

## Priority B — Medium Priority (score 12–15)
[table]

## Priority C — Monitor (score < 12)
[table]

## Top 3 First Partnerships (90-day horizon)
1. [Partner] — [Model] — [Why now] — [First step]

## Ecosystem Health Summary
[Assessment of target ecosystem(s)]

## Power Position Summary
[Where you have leverage; where you need to build it]

## Recommended Next Steps
- Run /strategic-partnerships:partnerships-structure for the Priority A partnership deal design
- Run /strategic-partnerships:partnerships-architect for technical integration blueprint
- Run /strategic-partnerships:partnerships-monetize to model revenue potential across tiers
```
