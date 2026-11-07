# Strategic Partnerships

This plugin helps a software company find, design, and decide on partnerships in a software ecosystem. It guides founders, product leaders, and business development teams through six phases: readiness assessment, partner discovery, deal structure, technical integration, revenue model, and a go or no-go recommendation.

The frameworks come from **Karl Michael Popp and Ralf Meyer** (*Profit from Software Ecosystems*), **Gawer and Cusumano** (*Platform Leadership*), **Parker, Van Alstyne and Choudary** (*Platform Revolution*), **Slinger Jansen** (research on ecosystem health and power dynamics, Utrecht University), and **Forrester** (partner ecosystem data).

The plugin file [frameworks.md](./frameworks.md) names the source of each framework.

---

## Overview

`strategic-partnerships` runs a complete, research-based workflow for software ecosystem partnerships. It covers each stage of the partnership life cycle: it checks readiness, finds and ranks candidates, structures deals, designs technical integrations, models revenue, and gives a go or no-go decision.

You can use the plugin in two ways:

- **Full run.** One skill runs all six phases. The skill runs the Python scripts for the scoring and the math, and it starts an agent for each part that needs judgment. A full run takes time. Use a phase skill for a short run.
- **One phase.** A phase skill applies the framework of one phase in your conversation. You can ask it for a scored analysis too. Then it starts the agents of the phase and runs the scripts of the phase.

No agent of the plugin has the tools `Bash` or `Agent`. The skills run the scripts and start the agents in your conversation. Each agent can only read files and write files. The agent `apollo-enricher` also has one Apollo tool.

---

## Install

You need [`uv`](https://docs.astral.sh/uv/). The plugin runs its scripts with `uv run`.

```bash
claude plugin install strategic-partnerships@cc-plugins
```

---

## Skills

The plugin has 7 skills. Run a skill as `/strategic-partnerships:<skill>`.

| Skill | Use it to |
|---|---|
| `partnerships` | Run all six phases, from the product context to the go or no-go result. Claude also starts it when you ask for a partnership strategy, a partner search, a deal structure, an integration design, a partnership revenue model, or a go or no-go decision. |
| `partnerships-assess` | Check your partnership readiness (phase 1). |
| `partnerships-discover` | Map the partner ecosystem and find partner candidates (phase 2). |
| `partnerships-structure` | Design the deal economics and the contract frame (phase 3). |
| `partnerships-architect` | Design the technical integration (phase 4). |
| `partnerships-monetize` | Model the revenue and the ROI (phase 5). |
| `partnerships-recommend` | Make the go or no-go decision and the roadmap (phase 6). |

### The product context

The skill `partnerships` needs 5 facts about your product:

1. The product name
2. The product category
3. The target market
4. The existing integrations
5. The partnership goals

Give them after the skill name, as free text. The skill asks you only for the facts that you did not give.

```
/strategic-partnerships:partnerships Acme CRM, B2B sales software, mid-market sales teams in the US, integrates with Gmail and Slack, goal: find reseller and OEM partners
```

### The two paths of a phase skill

- **Quick interactive.** The skill applies its framework in your conversation. It can ask you questions.
- **Full quality.** Give a session id, or ask for a scored analysis. The skill checks that the earlier phases have output. When they do not, it names them and takes the quick path. Else it starts the agents of the phase, runs the scripts of the phase, and shows the path of the output file. `partnerships-recommend` starts the synthesizer.

---

## The six phases

### Phase 1: `/strategic-partnerships:partnerships-assess`

**Check your partnership readiness.**

The skill uses the Business Model Archetype Taxonomy of Popp to classify your current model (Inventor, IP Lessor, IP Distributor, Contractor, Broker). It maps the existing and the latent revenue streams with the 6-attribute model of Popp (Compensator, Effect, Causality, Rating, Charging, Timing). It checks your moat with the Network Effects Typology of Parker (cross-side, same-side, data-driven). It scores your position and your power with the ecosystem health and power dynamics frameworks of Jansen.

Output: readiness scorecard, gap list, power position summary, and the recommended first partnership model.

### Phase 2: `/strategic-partnerships:partnerships-discover`

**Map the ecosystem and find partner candidates.**

The skill finds candidates for each of the 6 partnership models of Popp (Referral, Revenue Share, Resell, OEM, Certified Solution, Development Cooperation). It scores them on Audience Overlap (30%), Strategic Fit (25%), Revenue Potential (25%), and Execution Feasibility (20%). It puts them in Priority A (pursue now), Priority B (pursue within 6 months), or Priority C (monitor). It checks the ecosystem health (Jansen) and the power dynamics.

Output: ranked partner map, the top 3 first partnerships, and an ecosystem health summary.

### Phase 3: `/strategic-partnerships:partnerships-structure`

**Design the deal economics and the contract frame.**

The skill uses the Hybrid Revenue Model of Popp to design revenue streams with more than one source. It maps each stream against the 6 attributes. It uses the 4 levers of platform leadership of Gawer to make structure decisions (scope, interface design, complementor relations, internal organization). It uses the openness framework of Parker (governance, developer access, user access) to decide the API and the partner program.

Output: deal economics, revenue stream design, partner program tiers, key contract terms, and a red flag checklist.

### Phase 4: `/strategic-partnerships:partnerships-architect`

**Design the technical integration.**

The skill uses the 4 levers of Gawer as the main decision frame. It uses the openness framework of Parker to select an ecosystem profile (Closed Platform, Controlled Ecosystem, Open Platform, Hybrid). It gives a reference architecture for each partnership model (Technology Integration, OEM or White-label, Reseller or VAR, Open Source and Commercial). It includes a developer experience checklist and a technical onboarding pipeline for partners.

Output: architecture diagram, build, buy, or configure advice, developer experience gaps, and engineering effort estimates.

### Phase 5: `/strategic-partnerships:partnerships-monetize`

**Model and improve the partnership revenue.**

The skill lists all revenue streams with the 6-attribute model of Popp. It gives the revenue mechanics and the typical range for each partnership model (referral 5-15% of ACV, reseller 20-40% discount, OEM 15-40% royalty, open core funnel, development cooperation R&D cost share). It models the effect of the platform revenue multiple (8.2x for platforms, 3.9x for traditional SaaS). It compares the projections with the 2025 data of Forrester (67% of firms expect partner revenue to grow more than 30% each year). The scripts calculate the NPV and the ROI.

Output: financial model (year 1, year 3, NPV), ROI analysis, Forrester benchmark comparison, and profit improvement moves.

### Phase 6: `/strategic-partnerships:partnerships-recommend`

**Make the go or no-go decision and the roadmap.**

The skill combines the output of all frameworks into one recommendation. The go or no-go rule uses the ROI multiple (NPV divided by the program cost): GO at 3 or more, CONDITIONAL GO from 2 to less than 3, and NO-GO below 2. It puts each opportunity in a 2x2 matrix (Quick Wins, Strategic Bets, Opportunistic, Avoid). It adds a 12-month roadmap, a risk register, and a board-ready partnership brief with the Forrester 2025 market context.

Output: go or no-go decisions, 12-month roadmap, risk register, and board brief.

---

## Outputs

A full run writes into the folder `.sp-tmp/<session_id>/` in your current folder. Git shows the folder `.sp-tmp/` as a new folder. To keep it out of your commits, add the line `.sp-tmp/` to the file `.gitignore` of your project. The folder holds:

- `session.json`: the state of the run, the pre-flight confidence and the evaluator result of each phase
- `preflight-<phase>.json` and `evaluator-<phase>.json`: the result of the pre-flight script and of the evaluator script for each phase
- `assess.md`, `discover.md`, `structure.md`, `architect.md`, `monetize.md`: the output of each phase
- `discover-model-<n>.md` and `discover-model-<n>.json`: the candidates of each partnership model (n = 1 to 6)
- `candidates.json`, `ecosystem-health.json`, `power-dynamics.json`: the input of the scoring scripts
- `partner-scores.json`, `ecosystem-health-result.json`, `power-dynamics-result.json`: the result of the scoring scripts
- `apollo-enrichment.md`: the company data from Apollo, or a notice that Apollo was not available
- `apollo-raw.json`: the raw Apollo answer. The file exists only when Apollo answered.
- `npv-input.json`, `monetize-notes.md`, `npv-result.json`: the input of the NPV script, the projections of the monetize agent, and the result of the NPV script
- `synthesize.md`: the go or no-go result, the risk register, and the next steps

At the end of a run, the skill shows the go or no-go result, the path of `synthesize.md`, each phase with low pre-flight confidence, and each phase that the evaluator failed.

A low confidence or a failed check does not stop the run. The synthesizer puts the gaps into the risk register.

The plugin removes a session folder that is older than 60 minutes and not complete, at the start of the next full run. A complete session stays until you delete it.

---

## Optional tool: Apollo

The discover phase can add company data from [Apollo](https://www.apollo.io/). This tool is optional. Without it, the plugin writes a notice in `apollo-enrichment.md`, and the run goes on.

To add the Apollo server, run this command. Replace `<your-token>` with your Apollo API key.

```bash
claude mcp add apollo -e APOLLO_API_KEY=<your-token> -- npx -y @thevgergroup/apollo-io-mcp@3.0.0
```

The server name must be `apollo`. The plugin sends the names of 10 or fewer companies to Apollo. The server reads the key from its own environment, and the plugin holds no key. The file `apollo-raw.json` holds the raw Apollo answer.

---

## Partnership models covered

### The 6 partnership models of Popp

| Model | Integration | Description |
|-------|-------------|-------------|
| **Referral** | Low | Partner generates leads; fee on qualified leads or closed deals |
| **Revenue Share** | Low-Medium | Complementary products; vendor endorses partner; receives % of revenue |
| **Resell / VAR** | Medium | Partner purchases and resells; VARs add vertical expertise |
| **OEM** | High | Partner embeds your product in their solution; charges for combined offering |
| **Certified Solution** | Medium-High | Certification proves integration quality; maintains partner competition |
| **Development Cooperation** | Very High | Joint R&D; co-developed IP; shared roadmaps |

### More models covered

| Model | Integration | Description |
|-------|-------------|-------------|
| **Open Core + Commercial** | Varies | OSS for community distribution; commercial enterprise tier |
| **Marketplace Listing** | Varies | AWS, Azure, GCP, Salesforce AppExchange, HubSpot, etc. |
| **GSI / SI Ecosystem** | High | Practice-based partnerships with System Integrators |

---

## Frameworks and attribution

The plugin uses peer-reviewed research and authoritative practitioner frameworks:

| Framework | Author(s) | Source |
|-----------|-----------|--------|
| Partner Model Taxonomy (Spectrum) | Popp & Meyer | *Profit from Software Ecosystems* (2010) |
| Business Model Archetype Taxonomy | Popp & Meyer | *Profit from Software Ecosystems* (2010) |
| Revenue Stream 6-Attribute Model | Popp & Meyer | *Profit from Software Ecosystems* (2010) |
| 4 Levers of Platform Leadership | Gawer & Cusumano | *Platform Leadership* (2002); MIT Sloan Management Review |
| Network Effects Typology | Parker, Van Alstyne & Choudary | *Platform Revolution* (2016) |
| Platform Openness Framework | Parker, Van Alstyne & Choudary | *Platform Revolution* (2016) |
| Ecosystem Monetisation Principles | Parker, Van Alstyne & Choudary | *Platform Revolution* (2016) |
| Ecosystem Health Indicators | Jansen | IWSECO 2012; *Is Your Software Ecosystem in Danger?* (2021) |
| Power Dynamics in Ecosystems | Jansen | PROFES 2016; *Journal of Systems and Software* (2019) |
| State of B2B Partner Ecosystems 2025 | Forrester | RES182126 (2025) |
| Platform Revenue Multiple Data | The Strategy Institute | Partner Ecosystem Strategy (2024) |

See [frameworks.md](./frameworks.md) for the full attribution, the publication lists, and a map of where each framework applies.

---

## Key data points

- **67%** of B2B companies expect partner-influenced revenue to grow more than 30% each year (Forrester 2025)
- **5x** faster growth for companies with strong partner ecosystems than for companies without
- **8.2x** revenue multiples for platform companies, and **3.9x** for traditional SaaS
- **$5.89B to $11.81B**: partner ecosystem platform market (2025 to 2034)
- Open core funnel, typical conversion: OSS to free cloud about 5%; free to paid about 10%; paid to enterprise about 20%

---

## Configuration

The plugin needs no setting and no environment variable. Install `uv`, and run a skill. The Apollo server is optional (see above).

---

## Use with other plugins

These plugins work well with `strategic-partnerships`. The plugins that this marketplace does not have yet come with the story that ports them.

| Plugin | Use |
|--------|-----|
| `competitive-intelligence` (STORY-71) | Use its analysis as the frame for `partnerships-discover`. It shows who wins which segments. This plugin shows who to partner with in response. |
| `jtbd-market-discovery` (STORY-70) | Its outcome data helps you define the ideal customer for `partnerships-assess`, and the audience overlap scores. |
| `pricing` (STORY-76) | The revenue model of `partnerships-monetize` gives the partner-influenced ARR assumptions for the pricing model. |
| `gtm` (STORY-78) | The channel strategy of `partnerships-recommend` gives the input for the channel go-to-market plan. |
| `product-finance` (STORY-77) | The NPV and the program cost of `partnerships-monetize` give the input for the financial model. |
| `corporate-development` (STORY-79) | For an acquisition target that starts as a partner candidate, use the output of `partnerships-recommend` as the first input. |
| `product` | API and integration features that a partnership needs become requirements in the product requirements. |

---

## Privacy

The plugin reads the product context that you give. It writes only into `.sp-tmp/` in your current folder. If you add the Apollo server, the plugin sends the names of 10 or fewer candidate companies to Apollo.

---

## Tests

Run the tests in the plugin folder:

```bash
pip install -r requirements-dev.txt
pytest tests/ -q -rs
```

---

## License and notice

This repository is under the Apache-2.0 license. The code of this plugin comes from an MIT-licensed plugin. [NOTICE](./NOTICE) holds the notice and the permission text.

---

## Recommended reading

1. **Popp & Meyer**, *Profit from Software Ecosystems* (2010): the base text for this plugin
2. **Gawer & Cusumano**, *Platform Leadership* (2002)
3. **Cusumano, Gawer & Yoffie**, *The Business of Platforms* (2019)
4. **Parker, Van Alstyne & Choudary**, *Platform Revolution* (2016)
5. **Forrester**, *The State of B2B Partner Ecosystems* (annual report)
