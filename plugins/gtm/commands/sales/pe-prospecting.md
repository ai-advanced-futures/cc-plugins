---
description: Research PE firm portfolio companies, filter by ICP, enrich via Apollo, score on AI signals and PE urgency, and output a ranked lead list
allowed-tools: ["Read(*)", "Write(*)", "Agent", "Glob(*)", "Grep(*)", "WebSearch(*)", "AskUserQuestion(*)", "mcp__apollo__apollo_enrich_company", "mcp__apollo__apollo_search_companies", "mcp__apollo__apollo_get_organization_job_postings", "mcp__apollo__apollo_search_people", "mcp__apollo__apollo_bulk_enrich_organizations", "mcp__hubspot__hubspot-search-objects"]
---

# /gtm:sales:pe-prospecting

## Purpose

Research a PE firm's portfolio companies, filter them against your ICP, enrich via Apollo.io, and score each on ICP fit, AI signal strength, and PE urgency signals. Output is a ranked lead list with tier assignments and recommended next actions. PE portfolio companies are high-priority targets: they operate under board-level pressure to improve margins, consolidate tooling, and demonstrate measurable ROI — making them receptive to solutions that reduce cost or accelerate growth.

## Usage

```
/gtm:sales:pe-prospecting
/gtm:sales:pe-prospecting --firm "Vista Equity Partners"
/gtm:sales:pe-prospecting --firm "Thoma Bravo" --geography "US,UK" --industry "B2B SaaS"
/gtm:sales:pe-prospecting --firm "Insight Partners" --min-employees 100 --max-employees 1000
/gtm:sales:pe-prospecting --firm "Summit Partners" --min-revenue 50000000 --max-revenue 300000000
```

## ICP Filter Parameters (User-Configurable)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `geography` | US | Country or comma-separated list of countries |
| `industry` | B2B SaaS | Industry vertical filter |
| `min_employees` | 50 | Minimum employee count |
| `max_employees` | 2,000 | Maximum employee count |
| `min_revenue` | $25M | Minimum annual revenue |
| `max_revenue` | $500M | Maximum annual revenue |
| `rpe_minimum` | $250K | Revenue per employee floor (applied to companies with 1,000+ employees) |

## Process

1. **Collect PE firm name** — if `--firm` is not provided, ask the user via `AskUserQuestion` for the PE firm name. Confirm the firm name is valid and researchable.

2. **Research portfolio companies via web search** — use `WebSearch` to find the PE firm's current portfolio. Search queries:
   - `"{firm name}" portfolio companies`
   - `"{firm name}" current investments`
   - Visit the firm's website portfolio page if available
   Collect for each company: name, domain, industry, approximate size, investment date, investment type (growth, buyout, add-on).

3. **Apply ICP filters** — filter the raw portfolio list against the configured ICP parameters. For each company:
   - Check geography (HQ location matches filter)
   - Check industry (matches or is adjacent to filter)
   - Check employee count (within min/max range)
   - Check revenue (within min/max range, if known from web research)
   - Discard companies that fail hard filters
   - Flag companies within 10% of a boundary as "borderline — review"

4. **Enrich qualifying companies via Apollo** — for each company that passes ICP filters, call `mcp__apollo__apollo_enrich_company` with the company domain. Extract:
   - Verified domain, headquarters, founded year
   - Employee count, estimated annual revenue
   - Industry classification, sub-industry
   - Technology stack (languages, frameworks, infrastructure, AI/ML tools)
   - Recent funding events
   - Calculate RPE (revenue / employees). Re-apply RPE filter for companies with 1,000+ employees.

5. **Check job postings for AI signals** — for each enriched company, call `mcp__apollo__apollo_get_organization_job_postings` and scan for:
   - AI/ML engineer, data scientist, prompt engineer roles
   - Job descriptions mentioning: Claude, OpenAI, GPT, LLM, machine learning, AI platform
   - Count of active AI-related postings

6. **Score each company on three dimensions** (0–10 each, 30 max):

   **ICP Fit (0–10):**
   - Geography match: +2
   - Industry match: +2
   - Employee count in sweet spot (middle 50% of range): +2
   - Revenue in sweet spot (middle 50% of range): +2
   - RPE above threshold: +2

   **AI Signal Strength (0–10):**
   Scan enriched tech stack for: Claude, OpenAI, ChatGPT, Cursor, Copilot, Bedrock, LangChain, MLflow, Databricks, Gemini.
   - 0 AI tools: 0 (no signal)
   - 1 AI tool: +2 (early adopter)
   - 2 AI tools: +4 (active user)
   - 3+ AI tools: +6 (fragmentation — consolidation opportunity)
   - Recent AI-related acquisition: +2 bonus
   - Active AI/ML job postings: +2 bonus

   **PE Urgency Signals (0–10):**
   - Invested within last 18 months: +3 (active value creation phase)
   - Invested 18–36 months ago: +2 (mid-hold, pressure building)
   - Platform company doing add-on acquisitions: +2 (integration complexity = pain)
   - PE firm known for operational improvement thesis: +2
   - Leadership change (CEO/CTO/CIO) within last 6 months: +1 (new mandate, new budget)

7. **Rank and tier the lead list** — sort by total score descending. Assign tiers:
   - **Tier 1** (score >= 22): Immediate outreach — high ICP fit + strong signals
   - **Tier 2** (score 15–21): Add to outreach sequence — good fit, moderate signals
   - **Tier 3** (score < 15): Monitor only — keep on radar for signal changes

8. **Search for buyer contacts at Tier 1 companies** — for each Tier 1 company, call `mcp__apollo__apollo_search_people` to find:
   - CTO, VP Engineering, VP IT, Head of AI/ML (technical buyer)
   - CFO, COO, VP Operations (economic buyer — PE portfolio companies are margin-focused)
   - Include seniority, title, LinkedIn URL

9. **Check HubSpot for existing records** (if connected) — call `mcp__hubspot__hubspot-search-objects` to de-duplicate against existing CRM records. Flag companies already in pipeline.

10. **Write output artifacts:**
    - `pe-portfolio-leads.json` — ranked lead list with full scoring breakdown
    - `pe-prospecting-summary.md` — executive summary with Tier 1 highlights and recommended next steps
    - Append Tier 1 contacts to `gtm-context.json.pipeline.prospects[]`, tagging each entry with `"source": "pe-prospecting"` to prevent silent overwrite of existing records from other prospecting runs. De-duplicate by domain before appending.

11. **Pass to integrity-agent** — validate any claims about PE firm investment thesis, portfolio company metrics, or market size references.

## Output Artifacts

- `pe-portfolio-leads.json` — ranked lead list with company data, scores, tiers, and contacts
- `pe-prospecting-summary.md` — executive summary with Tier 1 highlights and outreach recommendations
- Appends Tier 1 contacts to `gtm-context.json.pipeline.prospects[]` tagged `"source": "pe-prospecting"` (no overwrite)

## Scoring Reference

| Dimension | Max Score | Key Signals |
|-----------|-----------|-------------|
| ICP Fit | 10 | Geography, industry, size, revenue, RPE |
| AI Signal Strength | 10 | Tech stack AI tools, fragmentation, AI hires, AI acquisitions |
| PE Urgency | 10 | Investment recency, add-on activity, op improvement thesis, leadership change |
| **Total** | **30** | |

## AI Tool Detection List

The following tools are scanned in the company tech stack to assess AI signal strength and fragmentation:

| Tool | Category |
|------|----------|
| Claude | LLM provider |
| OpenAI | LLM provider |
| ChatGPT | LLM provider (consumer signal) |
| Cursor | AI dev tool |
| Copilot | AI dev tool |
| Bedrock | AI infrastructure |
| LangChain | AI orchestration |
| MLflow | ML operations |
| Databricks | Data + AI platform |
| Gemini | LLM provider |

3+ providers detected = **fragmentation signal** = consolidation opportunity = higher score.
