---
description: Build ICP-driven prospecting strategy and find qualified prospects using Apollo.io and SPIN selling
allowed-tools: ["Read(*)", "Write(*)", "Agent", "Glob(*)", "Grep(*)", "WebSearch(*)", "AskUserQuestion(*)", "mcp__apollo__people_search", "mcp__apollo__organization_search", "mcp__apollo__people_enrichment", "mcp__apollo__organization_enrichment", "mcp__apollo__organization_job_postings", "mcp__hubspot__hubspot_search_contacts"]
---

# /gtm:sales:prospecting

## Purpose

Build a systematic prospecting strategy anchored to your ICP, then execute it with Apollo.io to produce a prioritized list of qualified prospects with contact data, intent signals, and SPIN-structured outreach sequences. Prospecting without ICP precision is list building; prospecting with ICP precision is pipeline creation.

## Usage

```
/gtm:sales:prospecting
/gtm:sales:prospecting --icp-segment "mid-market SaaS"    # target specific ICP segment
/gtm:sales:prospecting --quota 50                          # number of prospects to find
/gtm:sales:prospecting --intent-signals job-postings       # prioritize intent signal type
```

## Process

1. **Load or build ICP** — read ICP from `gtm-context.json`. If ICP is missing or incomplete, build it yourself from available context (product capabilities, existing customers if any, market positioning), in the shape of `${CLAUDE_PLUGIN_ROOT}/schemas/icp-schema.json`. Read that file first. ICP must specify: company size range, industries, geography, tech stack signals, job titles of buyer and user, pain indicators.

2. **Search Apollo.io for ICP-matched organizations** (if connected) — run `organization_search` with filters derived from ICP:
   - Industry codes matching ICP industries
   - Employee count range from ICP company size
   - Geography from ICP geography
   - Technology stack signals (if ICP specifies tech stack)
   - Return top 200 matching organizations, ranked by fit score

3. **Check job postings for intent signals** (if connected) — run `organization_job_postings` for the top 50 organizations. Analyze hiring patterns for intent signals:
   - Hiring for the role that uses your product → active budget signal
   - Hiring a function you replace → build vs. buy moment
   - Rapid headcount growth → scaling pain likely present
   - Specific technology mentions in job descriptions → tech stack confirmation

4. **Score and rank organizations** — combine ICP fit score + intent signals into a prospect priority score. Tier the list:
   - Tier 1 (hot): ICP fit ≥ 85% + active intent signal → immediate outreach
   - Tier 2 (warm): ICP fit 70-84% OR no intent signal → sequence outreach
   - Tier 3 (cold): ICP fit 50-69% → nurture / monitor

5. **Search for buyer contacts within Tier 1 and Tier 2 companies** (if connected) — run `people_search` filtered by:
   - Job title matching ICP buyer personas (economic buyer + champion)
   - Seniority level appropriate to deal size
   - LinkedIn presence (proxy for reachability)

6. **Enrich top prospects** (if connected) — run `people_enrichment` and `organization_enrichment` on Tier 1 contacts to retrieve: verified email, phone, LinkedIn URL, company funding data, recent news, technology stack confirmation.

7. **Check HubSpot for existing contacts** (if connected) — run `hubspot_search_contacts` to de-duplicate against existing CRM records. Flag any prospects already in pipeline to avoid double-outreach.

8. **Design SPIN outreach sequences** — using SPIN Selling framework, design a 3-touch outreach sequence for each ICP tier:
   - Touch 1 — Situation question: establish context without pitching ("I saw you're hiring [role]...")
   - Touch 2 — Problem question: surface pain ("Companies like yours often struggle with...")
   - Touch 3 — Implication question: amplify urgency ("What does that cost you per quarter?")
   - Follow-up — Need-Payoff question: let buyer articulate value ("What would it mean if...")

9. **Sync to HubSpot** (if connected) — create contact and company records for all Tier 1 prospects with ICP score, intent signals, and assigned sequence.

10. **Write `prospecting-plan.json`** — structured prospecting plan including:
    - Prioritized prospect list by tier with contact data
    - ICP scoring breakdown per prospect
    - Intent signals identified per company
    - Outreach sequences by tier
    - Recommended weekly outreach cadence

11. Pass `outreach-sequences.md` and `prospecting-plan.json` to integrity-agent — outreach copy is sent directly to prospects and must have no unattributed claims or superlatives

## Output Artifacts

- `prospecting-plan.json` — prioritized prospect list with scores, signals, and sequences
- `outreach-sequences.md` — SPIN-structured email and call scripts by tier
- Updates `gtm-context.json.pipeline.prospects[]` with Tier 1 contacts

## SPIN Selling Summary

| Question Type | Purpose | Example Opener |
|--------------|---------|----------------|
| Situation | Establish context | "How are you currently managing...?" |
| Problem | Surface implicit pain | "What challenges do you run into when...?" |
| Implication | Amplify urgency | "How does that impact your team's ability to...?" |
| Need-Payoff | Buyer articulates value | "If you could solve that, what would it mean for...?" |
