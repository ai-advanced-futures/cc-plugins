---
description: Build MEDDPICC-scored pipeline playbooks with stage-by-stage exit criteria and objection handling
allowed-tools: ["Read(*)", "Write(*)", "Agent", "Glob(*)", "Grep(*)", "WebSearch(*)", "AskUserQuestion(*)", "mcp__hubspot__hubspot_search_contacts", "mcp__hubspot__hubspot_get_company", "mcp__hubspot__hubspot_get_pipeline_stages"]
---

# /gtm:sales:pipeline

## Purpose

Build a rigorous pipeline management system using MEDDPICC as the qualification and scoring framework. This command produces stage-by-stage exit criteria, discovery question sets, objection handling playbooks, and a MEDDPICC scorecard that gives sales reps and managers a shared language for assessing deal health. Deals that cannot score at least 5/7 MEDDPICC dimensions by Stage 3 should be disqualified or returned to nurture.

## Usage

```
/gtm:sales:pipeline
/gtm:sales:pipeline --stages "Discovery,Demo,Proposal,Legal,Closed Won"  # custom stage names
/gtm:sales:pipeline --deal-size enterprise   # enterprise | mid-market | smb
```

## Process

1. **Load pipeline stage definitions** — pull live stage names and properties from HubSpot (if connected) via `hubspot_get_pipeline_stages`. If HubSpot is not connected, ask the user via `AskUserQuestion` to provide their stage names and typical deal duration per stage. Use these as the foundation for the playbook.

2. **Apply MEDDPICC framework** — map each MEDDPICC dimension to the pipeline stage where it must be confirmed:

   | Dimension | Definition | Must Confirm By |
   |-----------|-----------|-----------------|
   | **M**etrics | Quantified business impact (ROI, time saved, revenue gained) | Stage 2 (Discovery) |
   | **E**conomic Buyer | Name and title of the person who controls the budget | Stage 2 (Discovery) |
   | **D**ecision Criteria | Explicit criteria the buyer will use to make the purchase decision | Stage 3 (Demo/Eval) |
   | **D**ecision Process | Steps, approvers, and timeline from verbal yes to signed contract | Stage 3 (Demo/Eval) |
   | **P**ain | Specific, quantified business pain this deal solves | Stage 1 (Qualification) |
   | **I**dentify Champion | Internal advocate with influence and personal motivation to help | Stage 2 (Discovery) |
   | **C**ompetition | Competitors being evaluated, their strengths, our differentiation | Stage 3 (Demo/Eval) |
   | **C**onfirm | Validation checkpoint — all prior dimensions re-confirmed before close | Stage N-1 (Proposal) |

3. **Define SQL criteria** — specify the minimum MEDDPICC score to advance a lead from MQL to SQL (Sales Qualified Lead). Recommended threshold: M + E + P confirmed = SQL. Document this as a shared marketing-sales definition.

4. **Build stage-by-stage exit criteria** — for each pipeline stage, define:
   - What the rep must have confirmed (MEDDPICC dimensions)
   - What the buyer must have done (actions indicating real engagement)
   - What documents or artifacts must exist
   - What must be true before the rep moves the deal to the next stage

5. **Build discovery question sets** — for each pipeline stage, provide 5-10 discovery questions designed to surface the required MEDDPICC dimensions. Questions should follow SPIN logic (Situation → Problem → Implication → Need-Payoff).

6. **Build objection handling playbooks** — for each stage, document the 5 most common objections and a structured response for each:
   - Acknowledge the objection without flinching
   - Isolate whether it is a true objection or a concern
   - Respond with evidence, reframe, or a question to surface the real issue
   - Confirm resolution before moving forward

7. **Pull existing deal context from HubSpot** (if connected) — run `hubspot_search_contacts` and `hubspot_get_company` to pull open deals and assess current MEDDPICC coverage. Flag deals with critical gaps (e.g., no economic buyer identified after Stage 2).

8. **Write output artifacts:**
   - `pipeline-playbook.json` — full structured playbook with exit criteria, questions, and objections per stage
   - `meddpicc-scorecard.md` — printable/shareable scoring template reps fill out per deal
   - `sql-criteria.json` — shared SQL definition (written to `gtm-context.json.pipeline.sql_criteria`)

9. **Pass to integrity-agent** — validate any benchmark claims, win rate statistics, or industry comparisons cited in the playbook.

## Output Artifacts

- `pipeline-playbook.json` — stage playbooks with exit criteria, questions, objection handling
- `meddpicc-scorecard.md` — per-deal scoring template
- `sql-criteria.json` — formal SQL definition shared with marketing

## Why MEDDPICC

MEDDPICC is the qualification framework of record for B2B SaaS. It replaces gut-feel pipeline reviews with a structured, repeatable scoring system. Deals that cannot satisfy MEDDPICC dimensions are not qualified deals — they are assumptions waiting to fail.
