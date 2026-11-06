---
description: Unified revenue funnel health — MQL→SQL→SAL handoff logic, bottleneck analysis, and revenue math
allowed-tools: ["Read(*)", "Write(*)", "Agent", "Glob(*)", "Grep(*)", "WebSearch(*)", "AskUserQuestion(*)", "mcp__google-analytics__run_report", "mcp__google-analytics__get_metadata", "mcp__hubspot__hubspot_search_deals"]
---

# /gtm:funnel

## Purpose

Analyze the complete revenue funnel from top-of-funnel acquisition through closed-won deals. This command bridges marketing and sales data to validate MQL→SQL→SAL handoff logic, identify the single highest-leverage bottleneck across the entire funnel, compute revenue math, and produce a unified funnel health report that both marketing and sales leadership can act on.

## Usage

```
/gtm:funnel
/gtm:funnel --period 90d             # analysis window (default: 30d)
/gtm:funnel --model "freemium"       # funnel model: freemium | demo | trial | PLG
/gtm:funnel --revenue-target 1000000 # ARR target for gap analysis
```

## Process

1. **Load MQL and SQL criteria** — read `mql-criteria.json` (from marketing-agent) and `sql-criteria.json` (from sales-agent). If either is missing, prompt user to run `/gtm:marketing:launch` or `/gtm:sales:pipeline` first, or provide manual definitions via `AskUserQuestion`.

2. **Validate MQL/SQL consistency** — check that MQL and SQL definitions are aligned:
   - SQL threshold must be higher specificity than MQL threshold
   - No MQL criteria should contradict SQL criteria
   - Confirm that both definitions share the same ICP segment scope
   - Flag any gaps or contradictions as "definition debt" requiring resolution

3. **Pull GA4 conversion data** (if connected) — run `run_report` to retrieve:
   - Sessions → signups by channel and landing page
   - Signup → activation conversion rate
   - GA4 metadata via `get_metadata` to understand available dimensions and metrics

4. **Pull HubSpot pipeline data** (if connected) — run `hubspot_search_deals` to retrieve:
   - Total deals by stage
   - MQL → SQL conversion rate (leads entering pipeline vs. accepted by sales)
   - SQL → SAL conversion rate (accepted vs. actively worked)
   - SAL → Closed Won conversion rate
   - Average time in each stage
   - Deal value distribution

5. **Run bottleneck detector** — calculate conversion rates at every funnel transition:
   ```
   Visitors → Signups → Activated → MQL → SQL → SAL → Closed Won
   ```
   Identify the single stage with the largest relative conversion gap vs. benchmark. This is the primary constraint. Additional bottlenecks are ranked and listed but one primary is designated for focused action.

6. **Compute revenue math** — model forward-looking ARR from current funnel inputs:
   ```
   Monthly Visitors × Visitor→MQL rate × MQL→Won rate × ACV = Monthly New ARR
   Monthly New ARR × 12 = Run Rate ARR
   ```
   If a revenue target is provided, compute the required inputs (visitors, MQL volume, or win rate improvement) to reach the target.

7. **Define SAL handoff criteria** — specify the exact conditions under which sales accepts a lead from marketing (SAL = Sales Accepted Lead). The SAL definition prevents blame between teams:
   - What marketing commits to deliver with each SAL
   - What sales commits to do within X hours of SAL
   - What happens to leads that fail SAL criteria (return to nurture vs. disqualify)
   - SLA: maximum response time from SAL to first sales contact

8. **Write output artifacts:**
   - `funnel-metrics.json` — full funnel data with conversion rates, volumes, and benchmarks
   - `funnel-health.md` — unified health report with bottleneck analysis and recommendations
   - `handoff-sla.md` — formal MQL→SQL→SAL handoff definition and SLA
   - `revenue-math.md` — revenue model with scenarios and sensitivity analysis

## Output Artifacts

- `funnel-metrics.json` — structured funnel data (volumes, rates, benchmarks)
- `funnel-health.md` — bottleneck analysis and prioritized recommendations
- `handoff-sla.md` — formal marketing-sales handoff definition and SLA
- `revenue-math.md` — ARR model with current baseline and target scenarios

## Revenue Math Model

```
                    Current   Target   Gap
Monthly Visitors       5,000   10,000  +5,000
Visitor → MQL            2.1%    2.1%     –
Monthly MQLs             105     210    +105
MQL → SQL               38%     38%      –
Monthly SQLs              40      80     +40
SQL → Closed Won         22%     22%     –
Monthly New Logos          9      18      +9
ACV                   $12,000  $12,000    –
Monthly New ARR       $108k    $216k   +$108k
Projected ARR         $1.3M    $2.6M   +$1.3M
```

The bottleneck detector identifies which single input — if improved — moves the ARR needle most.
