---
name: sales-prospecting
description: Build an ICP-driven prospecting plan using Apollo.io data and SPIN-based outreach sequences
---

# Prospecting

> **Delegation note:** Raw prospect identification (finding ICP-matched contacts) is delegated to `sales:prospect-research` (Anthropic plugin) when available. This skill owns SPIN-based outreach sequencing, Ring 0 personalization, and Truth Tier compliance of outreach messages.

## Purpose

Turn your ICP definition into a prioritized, enriched prospect list with a personalized outreach sequence grounded in SPIN selling — not generic cold email.

## Prospecting Protocol

### Step 1: ICP → Apollo.io Search Parameters
From `icp-schema.json`, extract:
- Industry (Apollo: industry filter)
- Company size (Apollo: employee_count range)
- Role (Apollo: title keywords)
- Geography (Apollo: location filter)
- Intent signals: look for job postings as buying signals (company hiring SDRs → growing sales team → may need sales tools)

### Step 2: Enrich and Score Accounts
When the tools `mcp__apollo__people_enrichment` and `mcp__apollo__organization_enrichment` are in the session, use them to add the items below. If they are not, ask the person for these data, or use public web sources:
- Revenue, funding stage, tech stack
- Seniority of contact
- Social presence

Score each account: ICP fit (firmographic match) + Intent (job postings, tech signals) + Timing (funding event, leadership change)

### Step 3: Build SPIN Outreach Sequence
Email 1 (Situation): Acknowledge their context with a specific observation
Email 2 (Problem): Name the problem they likely have (use customer language from Ring 0 knowledge)
Email 3 (Implication): Quantify the cost of inaction
Email 4 (Need-Payoff): Describe the outcome they could achieve

Each email: < 150 words. One idea. One ask.

## Output
`prospecting-plan.json` with target accounts, enrichment data, and outreach sequence.
