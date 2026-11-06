---
name: sales-pe-portfolio-prospecting
description: Research PE firm portfolio companies, filter by ICP, enrich via Apollo, score on AI signals and PE urgency, and output a ranked lead list
---

# PE Portfolio Prospecting

## Purpose

Turn a PE firm name into a ranked, enriched lead list of portfolio companies that match your ICP — scored on ICP fit, AI signal strength, and PE urgency signals. PE-backed companies are high-value targets because they operate under board-level pressure to improve margins, consolidate tooling, and demonstrate measurable ROI on every dollar spent.

## Prospecting Protocol

### Step 1: Research PE Firm Portfolio

From the user-provided PE firm name, use web search to identify the firm's current portfolio companies. Collect:
- Company name and domain
- Industry vertical
- Approximate employee count and revenue (from Crunchbase, PitchBook references, or firm website)
- Investment date and stage (growth equity, buyout, add-on)

### Step 2: Apply ICP Filters

Filter portfolio companies against configurable ICP parameters:
- **Geography**: default US
- **Industry**: default B2B SaaS
- **Employee range**: default 50–2,000
- **Revenue range**: default $25M–$500M
- **RPE minimum** (companies over 1,000 employees): default $250K

Discard companies that fail any hard filter. Flag borderline companies (within 10% of a boundary) as "review."

### Step 3: Enrich Qualifying Companies via Apollo

For each company that passes ICP filters, call `mcp__apollo__apollo_enrich_company` to retrieve the items below. If the tool is not in the session, use public web sources or ask the person, and mark each item that you could not verify:
- Verified domain, headquarters, founded year
- Employee count, estimated annual revenue
- Industry classification, sub-industry
- Technology stack (languages, frameworks, infrastructure, AI/ML tools)
- Recent funding events
- Key contacts (C-suite, VP-level)

Calculate Revenue Per Employee (RPE) from enriched data. Re-apply RPE filter if employee count exceeds 1,000.

### Step 4: Score Each Company

Score each qualifying company on three dimensions (each 0–10, total 0–30):

**ICP Fit (0–10)**
- Geography match: +2
- Industry match: +2
- Employee count in sweet spot: +2
- Revenue in sweet spot: +2
- RPE above threshold: +2

**AI Signal Strength (0–10)**
Scan tech stack for AI providers: Claude, OpenAI, ChatGPT, Cursor, Copilot, Bedrock, LangChain, MLflow, Databricks, Gemini.
- 0 AI tools detected: 0 (no signal)
- 1 AI tool: +2 (early adopter)
- 2 AI tools: +4 (active user)
- 3+ AI tools: +6 (fragmentation — high value, consolidation opportunity)
- Recent AI-related acquisition: +2 bonus
- AI/ML job postings active: +2 bonus

**PE Urgency Signals (0–10)**
- Invested within last 18 months: +3 (active value creation phase)
- Invested 18–36 months ago: +2 (mid-hold, pressure building)
- Platform company doing add-ons: +2 (integration complexity)
- PE firm known for operational improvement thesis: +2
- Leadership change within last 6 months: +1 (new mandate)

### Step 5: Rank and Output

Sort companies by total score descending. Output a structured lead list with:
- Company name
- Domain
- Estimated revenue
- Employee count
- RPE
- PE owner (firm name)
- Investment date / stage
- AI signals detected (list of tools)
- ICP fit score
- AI signal score
- PE urgency score
- Total score
- Recommended action (Tier 1: immediate outreach / Tier 2: sequence / Tier 3: monitor)

Tier thresholds:
- Tier 1 (score >= 22): immediate outreach
- Tier 2 (score 15–21): add to sequence
- Tier 3 (score < 15): monitor only

## Output

`pe-portfolio-leads.json` with ranked lead list, scoring breakdowns, and tier assignments.
