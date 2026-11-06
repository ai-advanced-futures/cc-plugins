---
description: Phase 1. Find and rank acquisition targets that fit the strategy of the buyer.
argument-hint: "[focus or market]"
---
# /corporate-development:discover

**Phase 1: Target Discovery**

**Previously Phase 0** - Renumbered after adding Phase 0: Acquisition Readiness

Identify, qualify, and source target companies for potential M&A opportunities based on strategic criteria.

## When to use

- Starting a new M&A investigation
- Expanding your acquisition pipeline with fresh leads
- Screening companies against strategic criteria (market, revenue, growth, profitability)
- Building a qualified target list before detailed assessment

## What it does

1. **Strategic Criteria Collection** - Gathers your strategic requirements: markets, revenue range, growth criteria, profitability thresholds
2. **Target Sourcing** - Searches available databases and sources to identify potential acquisition targets
3. **Initial Qualification** - Screens targets against your strategic criteria
4. **Pipeline Creation** - Creates pipeline.json with qualified targets ranked by strategic fit
5. **Deal Sourcing Documentation** - Records all discovered targets and their sourcing method

## Required Input

```bash
/corporate-development:discover
```

Interactive prompts will guide you through providing:
- Strategic focus areas
- Market/segment preferences
- Revenue range expectations
- Growth rate requirements
- Profitability thresholds
- Geographic preferences
- Technology stack requirements

## Interactive Flow

The command walks you through these prompts:

```
Enter strategic focus areas (comma-separated): SaaS, developer tools
Enter target market segments: Enterprise, Mid-market
What revenue range are you targeting? (format: $1M-$10M): $5M-$50M
Minimum annual growth rate (%)? 20
Profitability requirement? (yes/no): yes
Geographic focus? (US/Europe/Global): US
Key technology preferences? (comma-separated): Python, React, Kubernetes
```

After you provide criteria, the command:
- Searches available deal sources
- Applies qualification filters
- Ranks targets by fit score
- Creates visualization of opportunity pipeline

## Outputs

**pipeline.json** - Main discovery output
```json
{
  "discovery_date": "2026-02-03",
  "strategic_criteria": {
    "markets": ["SaaS", "developer tools"],
    "revenue_range": "$5M-$50M",
    "min_growth_rate": 20,
    "profitability_required": true,
    "geography": "US"
  },
  "targets": [
    {
      "id": "target_001",
      "company_name": "Example Inc",
      "estimated_revenue": "$25M",
      "growth_rate": 35,
      "strategic_fit_score": 8.5,
      "source": "PitchBook",
      "sourcing_method": "keyword_search",
      "next_step": "assess"
    }
  ],
  "summary": {
    "total_discovered": 15,
    "qualified_targets": 12,
    "high_priority": 4
  }
}
```

**discovery_summary.md** - Human-readable discovery report with:
- Strategic criteria applied
- Number of targets discovered and qualified
- Top targets with fit scores
- Sourcing methods used
- Recommended next actions

## Discovery Workflow

The discover command implements a multi-stage qualification process:

1. **Sourcing Stage** - Uses multiple data sources:
   - PitchBook for revenue/growth data
   - Crunchbase for market positioning
   - Custom databases
   - Market reports

2. **Initial Qualification** - Screens against must-have criteria:
   - Revenue within range
   - Growth meets threshold
   - Market alignment
   - Geographic preference

3. **Fit Scoring** - Ranks by strategic fit (0-10):
   - Market alignment (0-3 points)
   - Revenue/growth match (0-3 points)
   - Strategic value (0-2 points)
   - Technology fit (0-2 points)

4. **Pipeline Staging** - Categorizes targets:
   - **Hot Prospects** (fit score 8-10): Schedule assess immediately
   - **Strong Candidates** (fit score 6-7): Plan assess within 2 weeks
   - **Monitor** (fit score 4-5): Keep in watch list
   - **Pass** (below 4): Archive with reason

## Strategic Decision Gates

Targets must pass these gates to enter qualified pipeline:

```
Revenue Check
    ↓ PASS: Within range
    ↓ FAIL: Archive, note reason
Growth Check
    ↓ PASS: Meets threshold
    ↓ FAIL: Archive, note reason
Market Alignment
    ↓ PASS: In target markets
    ↓ FAIL: Archive, note reason
Final Fit Score
    ↓ Score ≥ 6: Add to qualified targets
    ↓ Score < 6: Add to monitor list
```

## Next Steps

After discover completes successfully:

1. **Review Pipeline** - Examine top targets in pipeline.json
2. **Run Assess** - Execute `/corporate-development:assess` for your top candidates
   ```bash
   /corporate-development:assess --target target_001
   ```
3. **Iterate Discovery** - Run discover again with adjusted criteria if needed

## Related Skills

- `/corporate-development:readiness` - Phase 0: Acquisition Readiness Assessment
- `/corporate-development:assess` - Phase 2: Target assessment and fit analysis
- `/corporate-development:audit` - Phase 3: Operational due diligence
- Target sourcing and qualification best practices

## Integrations

- PitchBook API for company data
- Crunchbase for market research
- Custom deal flow databases
- Excel export capability
