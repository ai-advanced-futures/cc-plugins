# Strategic Partnerships Plugin — Frameworks & Attribution

This document records all thought leaders, authors, and validated frameworks incorporated into the `strategic-partnerships` plugin. Every framework used in the plugin's skills is sourced from peer-reviewed research, practitioner books, or industry data — and is attributed here.

---

## 1. Karl Michael Popp & Ralf Meyer

**Affiliation:** Popp is Senior Director M&A, Global Business Development & Ecosystem, Office of the CEO at SAP SE. 30+ acquisitions, 50+ partnership engagements across his career. Co-editor of IEEE Software special issues on managing platforms and ecosystems. Chair of the European Workshop on Software Ecosystems (IWSECO) 2012–2018.

**Primary Work:**
- *Profit from Software Ecosystems: Business Models, Ecosystems and Partnerships in the Software Industry* (Books on Demand, 2010) — with Ralf Meyer
- *Profit from Software Ecosystems: Student Workbook* (2011)
- *Advances in Software Economics: A Reader on Business Models and Partnering* (2011)
- "Software Industry Business Models" — *IEEE Software*, 2011
- "Managing Software Ecosystems through Partnering" (with van Angeren & Kabbedijk) — in *Software Ecosystems*, Edgar Elgar, 2013
- "The Impact of Software-as-a-Service on Partner Management" — ICSOB 2013
- IWSECO Proceedings 2012, 2013, 2014, 2016, 2018

**Website:** https://www.drkarlpopp.com

---

<!-- §assess-start -->
<!-- §discover-start -->
<!-- §structure-start -->
### Framework A: Popp's Partner Model Taxonomy (Spectrum of Integration)

**Source:** *Profit from Software Ecosystems*, Chapter 6: Partnership Models; drkarlpopp.com/partnermodelsinthesoftwareindustry

The canonical taxonomy of software industry partner models, ordered from lowest to highest integration depth:

| # | Model | Integration | Description |
|---|-------|-------------|-------------|
| 1 | **Referral** | Low | Partner generates leads; vendor pays referral fee on qualified leads or closed deals. "Easy creation, low impact on both organizations." |
| 2 | **Revenue Share** | Low-Medium | Vendor endorses partner's complementary product; vendor receives % of partner revenue when customer buys. Requires non-competitive, complementary offerings. |
| 3 | **Resell (VAR)** | Medium | Partner purchases vendor's software and sells to end customers. Revenue: license + support & maintenance fees. VARs add vertical expertise (e.g., oil & gas consulting). |
| 4 | **OEM** | High | Vendor supplies software; partner integrates it into their solution and charges only for their complete product. Not charged separately — key distinction from resell. Compensation: revenue share of partner's sales, or fixed per-unit fee. |
| 5 | **Certified Solution** | Medium-High | Vendor certifies integration quality between two products. Maintains partner competition (price pressure) while ensuring integration standards. Reduces customer integration costs. |
| 6 | **Development Cooperation** | Very High | Joint R&D between vendor and partner. Co-developed IP, shared roadmaps, deep technical collaboration. |

**Used in skills:** `assess`, `discover`, `structure`, `recommend`

---

<!-- §monetize-start -->
### Framework B: Popp's Business Model Taxonomy

**Source:** *Profit from Software Ecosystems*, Chapter 2; drkarlpopp.com/businessmodelsinthesoftwareindustry

Three-component classification system:

**Component 1 — Type of Goods:**
- Financial goods (cash, assets)
- Physical goods (tangible, durable/non-durable)
- Intangible goods (software, IP, knowledge, brand)
- Human goods (people's time and expertise)

**Component 2 — Business Model Archetypes:**
| Archetype | Definition |
|-----------|------------|
| **Creator** | Transforms inputs using internal assets to design the product |
| **Distributor** | Acquires and resells without modification |
| **Lessor** | Grants temporary usage rights without ownership transfer |
| **Broker** | Matches buyers and sellers without taking ownership |
| **Contractor** | Sells human services (support, consulting, implementation) |

**Typical software industry combinations:**
- **Inventor** (creator of intangible goods) + **IP Lessor** (licensing) + **IP Distributor** (reselling) + **Contractor** (consulting/support)
- Most vendors use **hybrid models** blending multiple archetypes

**Used in skills:** `assess`, `structure`

---

### Framework C: Popp's Revenue Stream Model (6-Attribute Framework)

**Source:** *Profit from Software Ecosystems*; drkarlpopp.com/revenuemodelssoftwareindustry

Every revenue stream is defined by 6 attributes:

| Attribute | Definition | Examples |
|-----------|------------|---------|
| **Compensator** | Who pays? | Customer, third party, advertiser |
| **Effect** | Type of compensation | None (OSS), goods/services exchange, financial payment |
| **Causality** | Links to exactly one business pattern | License sale → IP Lessor pattern |
| **Rating** | How usage is measured | By amount (users, seats, processors, throughput), by time (minutes, periods), or combination |
| **Charging** | Payment calculation rules | Fixed fee, tiered pricing, pay-per-use, revenue share |
| **Timing** | When payment occurs | Prepay, scheduled (monthly/annual), postpay |

**Hybrid Revenue Models:** A single vendor typically stacks multiple revenue streams. E.g., SaaP (Software as Product): IP Lessor (license) + Contractor (support/maintenance). SaaS: IP Lessor + Physical Lessor + Contractor bundled. Most partner deals are also hybrid.

**Used in skills:** `structure`, `monetize`

---

## 2. Annabelle Gawer & Michael A. Cusumano

**Affiliation:** Gawer is Chaired Professor of Digital Economy, University of Surrey, Director of Centre for Digital Economy (CoDE). Cusumano is SMR Distinguished Professor, MIT Sloan School of Management. Combined: 30+ years researching platform strategy from Intel, Microsoft, Cisco, Apple, and Google.

**Primary Works:**
- *Platform Leadership: How Intel, Microsoft, and Cisco Drive Industry Innovation* (Harvard Business School Press, 2002)
- *The Business of Platforms: Strategy in the Age of Digital Competition, Innovation, and Power* (HarperCollins, 2019) — with David B. Yoffie (Harvard Business School)
- "The Elements of Platform Leadership" — *MIT Sloan Management Review*
- "Managing Software Platforms and Ecosystems" — *IEEE Software*, 2019 (with Cusumano & Jansen)
- "Industry Platforms and Ecosystem Innovation" — *Journal of Product Innovation Management*
- "Digital Platforms and Ecosystems: Remarks on the Dominant Organizational Forms of the Digital Age" — SSRN, 2021

---

<!-- §architect-start -->
### Framework D: Gawer's 4 Levers of Platform Leadership

**Source:** *Platform Leadership* (2002); "The Elements of Platform Leadership" — *MIT Sloan Management Review*

Four strategic levers for building and sustaining platform leadership:

| Lever | Strategic Question | Key Decisions |
|-------|--------------------|---------------|
| **1. Scope of the Firm** | What to build internally vs. let complementors build? | Internalize vs. externalize components; risk of over-integrating (kills ecosystem) or under-integrating (cedes value) |
| **2. Product Technology Design** | How open or closed should interfaces be? | Modularity of architecture; which interfaces to open (APIs) vs. close (proprietary); open standards vs. proprietary lock-in |
| **3. Relationships with Complementors** | How to balance co-opetition? | Collaborate where ecosystem grows the pie; compete where zero-sum; governance of competitive tension |
| **4. Internal Organization** | How to structure internally to manage ecosystem? | Cross-functional platform teams; ecosystem-aware product roadmaps; partner success functions |

**Key insight:** Platform owners that "create complements internally" risk antagonizing ecosystem partners. Platform owners that keep interfaces too closed risk being bypassed. The optimal zone requires dynamic calibration of all 4 levers.

**Evidence from research (2025):** Platform inconsistencies between declared and undeclared practices trigger "social contagion of misconduct" among complementors (Gawer, 2025, Amazon Marketplace case study).

**Used in skills:** `architect`, `structure`, `recommend`, `discover`

---

## 3. Geoffrey G. Parker, Marshall W. Van Alstyne & Sangeet Paul Choudary

**Affiliation:** Parker is Professor at Dartmouth Tuck School of Business. Van Alstyne is Professor at Boston University. Choudary is founder of Platformation Labs, advisor to G20.

**Primary Works:**
- *Platform Revolution: How Networked Markets Are Transforming the Economy and How to Make Them Work for You* (W.W. Norton, 2016)
- "Innovation, Openness, and Platform Control" — *Management Science*

---

### Framework E: Network Effects Typology

**Source:** *Platform Revolution*, Chapter 2

Three distinct types of network effects with different strategic implications:

| Type | Mechanism | Strategic Implication |
|------|-----------|----------------------|
| **Cross-side effects** | Value created when consumers attract producers and vice versa | B2B2C partnerships; marketplace dynamics; developer ecosystems need critical mass on both sides |
| **Same-side effects** | Consumers benefit other consumers; producers benefit other producers | Community-driven products; OSS ecosystems; standards adoption |
| **Data-driven effects** | Scale improves data quality → better matching/recommendations → more users | AI/ML platforms; the more partners use it, the smarter it gets |

**Virtuous cycle:** Network effects create sustainable competitive advantage that price or brand alone cannot replicate. Partners attached to a platform with strong network effects face high switching costs.

**Used in skills:** `assess`, `recommend`

---

### Framework F: Platform Openness Decision Framework

**Source:** *Platform Revolution*, Chapter 7

Three dimensions of openness every platform must decide:

| Dimension | Spectrum | Examples |
|-----------|----------|---------|
| **Manager/sponsor participation** | Proprietary (single owner) → Shared (consortium/open governance) | Apple (proprietary) vs. Eclipse Foundation (shared) |
| **Developer participation** | Closed (no third-party development) → Open APIs (anyone can build) | Facebook Graph API → fully open marketplaces |
| **User participation** | Restricted (invite-only) → Unrestricted (public) | Early Gmail → public SaaS |

**Key principle:** Differentiation occurs through deliberate openness decisions. Neither fully open nor fully closed is optimal — the right answer depends on competitive context, ecosystem maturity, and monetization strategy.

**Used in skills:** `architect`, `structure`

---

<!-- §architect-end -->
### Framework G: Ecosystem Monetization Principles

**Source:** *Platform Revolution*, Chapter 8

Core principles for monetizing without dampening network effects:

- **Transaction fees** — small tax on interactions; scales with volume
- **Freemium models** — different pricing tiers; free side grows the network, paid side monetizes it
- **Enhanced access** — premium tools or data for power users/partners
- **Data insights** — aggregated analytics helping participants improve performance
- **Selective side charging** — charging one side improves quality by filtering low-commitment participants

**The cardinal rule:** Capture a portion of excess value created without dampening participation. Over-monetization kills the network that generates the value.

**Used in skills:** `monetize`, `structure`

---

<!-- §structure-end -->
## 4. Slinger Jansen

**Affiliation:** Associate Professor, Utrecht University. 9,131+ citations. Research focus: software ecosystems, software product management, ecosystem health, and partner governance.

**Primary Works:**
- "Defining Software Ecosystems: A Survey of Software Platforms and Business Network Governance" — IWSECO 2012
- "Partnership Characteristics within Large Software Ecosystems" — IWSECO 2011
- "A Power Perspective on Software Ecosystem Partnerships" — PROFES 2016 (with Valença & Alves)
- "Is Your Software Ecosystem in Danger? Preventing Ecosystem Death Through Lessons in Ecosystem Health" — 2021
- "Strategies for Managing Power Relationships in Software Ecosystems" — *Journal of Systems and Software*, 2019
- "Multi-homing in Ecosystems and Firm Performance" (VTT Research)
- Co-editor: *Managing Software Platforms and Ecosystems* — IEEE Software, 2019

---

### Framework H: Jansen's Ecosystem Health Indicators

**Source:** "Defining Software Ecosystems" (IWSECO 2012); "Is Your Software Ecosystem in Danger?" (2021)

An ecosystem's health determines its long-term viability as a partnership platform:

| Health Dimension | Healthy Signal | Warning Signal |
|-----------------|----------------|---------------|
| **Productivity** | Partners actively building, releasing, shipping | Stagnant partner output; long release cycles |
| **Robustness** | Ecosystem survives disruption (platform pivots, market shifts) | Single-partner dependency; platform fragility |
| **Niche creation** | New partner types emerging; ecosystem expanding scope | Niche saturation; partners competing for same customers |
| **Longevity** | Platform + key partners growing year-over-year | Partner churn; declining active integrations |
| **Diversity** | Mix of large and small complementors; multiple verticals | Concentration risk; 1-2 dominant complementors |

**Used in skills:** `assess`, `recommend`

---

### Framework I: Power Dynamics in Software Ecosystem Partnerships

**Source:** "A Power Perspective on Software Ecosystem Partnerships" — PROFES 2016; "Strategies for Managing Power Relationships" — *Journal of Systems and Software*, 2019

Power is asymmetric in software ecosystems. Four power-relevant factors:

| Factor | Description | Strategic Response |
|--------|-------------|-------------------|
| **Dependency** | How dependent is each party on the other? High dependency = low power | Diversify; multi-home across platforms; reduce single-partner lock-in |
| **Substitutability** | Can each party be replaced? Low substitutability = high power | Build unique capabilities that make you irreplaceable |
| **Centrality** | How central is each party to the ecosystem's network? | Become the bridge node between adjacent ecosystems |
| **Alternatives** | How many comparable alternatives exist? Fewer alternatives = more power | Create exclusive capabilities; patent; build switching costs |

**Used in skills:** `assess`, `discover`, `recommend`, `monetize`

---

<!-- §assess-end -->
<!-- §discover-end -->
## 5. Industry Research & Market Data

### Forrester Research — State of B2B Partner Ecosystems 2025

**Source:** "Continued Growth In Scale And Complexity: The State Of Partner Ecosystems In 2025" — Forrester, 2025; "The State of B2B Partner Ecosystems, 2025" (full report, RES182126)

Key data points used in plugin benchmarks:

| Metric | Data Point | Source |
|--------|-----------|--------|
| Indirect revenue growth expectation | 67% expect >30% YoY growth | Forrester 2025 |
| Partner-influenced revenue | Two-thirds expect >30% growth YoY | Forrester 2025 |
| Fastest-growing partner type | Technology partners, distribution, digital GTMs | Forrester 2025 |
| Primary ecosystem driver | Customer obsession / buyer expectation | Forrester 2025 |

### The Strategy Institute — Partner Ecosystem Strategy

**Source:** "Partner Ecosystem Strategy: A Framework for Scalable Business Growth" — The Strategy Institute, 2024

| Metric | Data Point |
|--------|-----------|
| Growth advantage | Companies with strong partner ecosystems grow 5× faster |
| Executive priority | 76% of executives consider partnerships essential for revenue goals |
| Platform revenue premium | Platform companies command 8.2× revenue multiples vs. 3.9× for traditional SaaS |
| Market size | Partner ecosystem platforms: $5.89B (2025) → $11.81B (2034) |

### Open Core Industry Data

**Source:** Industry analysis (Palark Tech Blog, The New Stack, InfoWorld, 2024–2025)

Typical open core monetization funnel conversion rates:
- Community OSS users → Free cloud: ~5%
- Free cloud → Paid starter: ~10%
- Paid starter → Enterprise: ~20%
- Enterprise cloud → Enterprise on-prem: ~10%

---

<!-- §monetize-end -->
<!-- §synthesize-start -->
## Framework Application Map

| Skill | Frameworks Applied |
|-------|--------------------|
| `assess` | A (Partner Taxonomy), B (Business Model Taxonomy), C (Revenue Stream Model), E (Network Effects), H (Ecosystem Health), I (Power Dynamics) |
| `discover` | A (Partner Taxonomy), D (4 Levers), H (Ecosystem Health), I (Power Dynamics) |
| `structure` | A (Partner Taxonomy), B (Business Model Taxonomy), C (Revenue Stream Model), D (4 Levers), F (Openness), G (Monetization Principles) |
| `architect` | D (4 Levers), F (Openness), I (Power Dynamics) |
| `monetize` | B (Business Model Taxonomy), C (Revenue Stream Model), G (Monetization Principles), I (Power Dynamics), Forrester 2025, Industry Open Core Data |
| `recommend` | A–I (all frameworks), Forrester 2025 benchmarks |

---

## Recommended Reading List

For practitioners using this plugin who want to go deeper:

1. **Popp & Meyer** — *Profit from Software Ecosystems* (2010) — the foundational text for this plugin
2. **Popp & Meyer** — *Profit from Software Ecosystems: Student Workbook* (2011)
3. **Gawer & Cusumano** — *Platform Leadership* (2002) — strategic platform design
4. **Cusumano, Gawer & Yoffie** — *The Business of Platforms* (2019) — modern platform economics
5. **Parker, Van Alstyne & Choudary** — *Platform Revolution* (2016) — network effects and ecosystem design
6. **Jansen (IWSECO proceedings)** — annual research on ecosystem health and governance
7. **Forrester** — *The State of B2B Partner Ecosystems* (annual) — market benchmarks
<!-- §synthesize-end -->
