---
name: lenses-strategic-positioning
description: Runs when the lens executor or the skill analyze needs the strategic positioning lens. It finds the business model, the moats and the weak points of a competitor.
user-invocable: false
---

# Strategic Positioning Analysis Lens

## Purpose

Understand how competitors position in the market and identify their sustainable advantages and vulnerabilities because strategic context determines long-term competitive dynamics.

## Input Required

- `intelligence-data.json` - Competitive data
- `competitive-ecosystem.json` - Competitor classifications

## Framework Components

### 1. Business Model Analysis

**Revenue Model:**
- Subscription (monthly/annual)
- Usage-based
- Transaction-based
- Freemium + premium
- Enterprise licensing

**Pricing Strategy:**
- Premium positioning
- Value positioning
- Low-cost leader
- Penetration pricing

**Go-to-Market:**
- Sales-led (enterprise)
- Product-led (self-serve)
- Partner-led (channel)
- Hybrid

### 2. Target Market Analysis

**Ideal Customer Profile:**
- Company size (SMB/Mid-Market/Enterprise)
- Industry focus
- Use case focus
- Geographic focus

**Segment Strategy:**
- Horizontal (cross-industry)
- Vertical (industry-specific)
- Niche (specific use case)

### 3. Competitive Moats Assessment

Based on Hamilton Helmer's 7 Powers:

| Moat Type | Description | Durability |
|-----------|-------------|------------|
| Network Effects | Value increases with users | Very High |
| Switching Costs | Cost/pain of leaving | High |
| Scale Economies | Cost advantages at scale | High |
| Brand | Recognition and trust | Medium |
| Cornered Resource | Exclusive access | Medium |
| Counter-Positioning | Incumbent can't copy | Medium |
| Process Power | Embedded capabilities | Low-Medium |

For each competitor, assess:
- Which moats do they have?
- How strong is each moat?
- Are moats growing or eroding?

### 4. Strategic Vulnerabilities

Identify weaknesses:
- **Dependency risks:** Single customer, platform, technology
- **Execution gaps:** Slow innovation, poor support
- **Market risks:** Segment shifts, disruption exposure
- **Financial risks:** Funding, profitability
- **Organizational:** Leadership, culture, talent

## Process

### 1. Analyze Each Competitor

For each Tier 1-2 competitor:
- Document business model
- Map target market
- Assess moats (score 1-5 each)
- Identify vulnerabilities
- Determine strategic intent

### 2. Comparative Positioning

Create positioning map:
- X-axis: Target market breadth
- Y-axis: Solution depth
- Plot all competitors

### 3. Strategic Implications

For each competitor:
- What is their theory of winning?
- Where are they investing?
- What might they do next?
- How might they respond to you?

## Output Format

Generate `strategic-analysis.json`:

```json
{
  "competitors": {
    "competitor_a": {
      "business_model": {
        "revenue_model": "subscription",
        "pricing_strategy": "premium",
        "pricing_range": "$500-2000/month",
        "go_to_market": "sales-led",
        "confidence": "high"
      },
      "target_market": {
        "company_size": "enterprise",
        "industries": ["financial services", "healthcare"],
        "use_cases": ["compliance reporting", "analytics"],
        "geographic": "north_america",
        "confidence": "high"
      },
      "moats": {
        "network_effects": {
          "score": 2,
          "evidence": "Limited user-to-user value",
          "confidence": "medium"
        },
        "switching_costs": {
          "score": 4,
          "evidence": "Deep integrations, data lock-in",
          "confidence": "high"
        },
        "scale_economies": {
          "score": 3,
          "evidence": "Some fixed cost leverage",
          "confidence": "medium"
        },
        "brand": {
          "score": 4,
          "evidence": "Strong enterprise reputation",
          "confidence": "high"
        },
        "total_moat_score": 13
      },
      "vulnerabilities": [
        {
          "type": "execution",
          "description": "Slow product iteration, 6-month release cycles",
          "exploitability": "high",
          "confidence": "medium"
        },
        {
          "type": "market",
          "description": "Over-indexed on enterprise, missing SMB growth",
          "exploitability": "medium",
          "confidence": "high"
        }
      ],
      "strategic_intent": {
        "theory_of_winning": "Become default enterprise standard through deep integration",
        "current_investments": ["AI features", "Partner ecosystem"],
        "likely_next_moves": ["SMB tier launch", "Acquisition for AI capability"],
        "confidence": "medium"
      }
    }
  },
  "positioning_map": {
    "x_axis": "target_market_breadth",
    "y_axis": "solution_depth",
    "positions": {
      "your_product": {"x": 0.6, "y": 0.7},
      "competitor_a": {"x": 0.3, "y": 0.9},
      "competitor_b": {"x": 0.8, "y": 0.4}
    },
    "white_space": ["high breadth + high depth"]
  },
  "summary": {
    "strongest_moat": {"competitor": "competitor_a", "moat": "switching_costs"},
    "biggest_vulnerability": {"competitor": "competitor_a", "vulnerability": "slow iteration"},
    "strategic_opportunity": "Win in mid-market where Competitor A is weak"
  }
}
```

## Philosophy

<moats_are_real>
Not all advantages are moats.
True moats compound over time.
Claimed moats need evidence.
</moats_are_real>

<vulnerabilities_are_opportunities>
Every competitor has weaknesses.
Execution gaps are exploitable.
Strategic misalignment creates openings.
</vulnerabilities_are_opportunities>

## Cascading Outputs

This lens informs:
- **Synthesis:** Strategic opportunities and threats
- **Recommendations:** Competitive positioning strategy

## Completion Protocol

After writing all output files:

**Write strategic-summary.json** to `data_dir` (from dispatch context):
{
  "lens": "strategic-positioning",
  "completed_at": "{ISO 8601 timestamp}",
  "competitors_analyzed": N,
  "headline": "Strongest moat: {competitor} ({moat_type}); biggest vulnerability: {competitor} ({reason})",
  "key_findings": [
    "Your positioning: {descriptor}",
    "Strongest competitor moat: {competitor} — {moat_type} (depth: {High|Medium|Low})",
    "Most vulnerable competitor: {competitor} — {reason}",
    "Best expansion opportunity: {segment|geography}"
  ],
  "confidence": "{HIGH|MEDIUM|LOW|SPECULATIVE}",
  "warnings": [],
  "data_file": "strategic-analysis.json"
}

**Return to caller:** DONE: lens-strategic
