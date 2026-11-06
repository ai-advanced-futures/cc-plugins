
Calculate EVC with low, medium, and high premiums:
- Shows range of possible pricing
- Helps calibrate differentiation claims
- Useful for sensitivity analysis

---

## Common Questions

**Q: What if I can't quantify all four components?**

A: Calculate what you can. Even 1-2 components provide useful pricing guidance. Just acknowledge what's missing.

**Q: Should I use average or median values?**

A: **Median** is usually better because averages are skewed by outliers. If one customer has 10x value, that value is a poor base to price for everyone.

**Q: How do I handle one-time vs ongoing value?**

A: Separate them:
- One-time value: Implementation/switching benefits
- Ongoing value: Monthly/annual recurring value

Price based on ongoing value (recurring revenue).

**Q: What if my EVC is lower than current solution prices?**

A: Three options:
1. Recalculate (maybe you missed value components)
2. Accept that market is overpriced (opportunity to undercut)
3. Target different segment with higher EVC

**Q: Can EVC justify free products?**

A: Yes! If you monetize differently (ads, data, network effects), EVC shows value you need to capture indirectly.

Example: Google Maps creates $20K/year value, charges $0, monetizes with ads and data.

---

## Ready for Phase 8?

Once you've calculated EVC for your top opportunities, we'll move to **Phase 8: Multi-Dimensional Segmentation** to find customer groups with distinct needs profiles.

To continue:

```
> "I'm ready for Phase 8"
```

Or to pause and refine EVC:

```
> "Save EVC analysis and pause"
```

---

**Phase 7 Complete!**

---

# Phase 8: Multi-Dimensional Segmentation

## What Happens in This Phase

**Goal:** Discover customer segments with distinct needs profiles using K-means clustering.

**Duration:** 20-30 minutes (mostly automated)

**Key Principle:** Segment by needs importance, not demographics. Different customers care about different outcomes.

**Why This Matters:**

One-size-fits-all products fail. Segments reveal:
- Which needs matter to whom
- Which segments to target first
- How to differentiate positioning
- Pricing tiers by segment value

**Example:**
- Segment 1: Crisis Avoiders (importance 9.2, satisfaction 2.8) → High-value target
- Segment 2: Satisfied Users (importance 5.1, satisfaction 8.2) → Low-value target
- Segment 3: Balanced (importance 7.5, satisfaction 6.0) → Medium-value target

---

## Needs-Based Clustering

### Using segmentation_engine.py (Claude Code)

```python
from scripts.segmentation_engine import SegmentationEngine

# Load survey data
engine = SegmentationEngine(survey_data)

# Find optimal number of segments
optimal = engine.find_optimal_k(k_range=(2, 6))
print(f"Optimal k: {optimal['optimal_k']}")  # e.g., 3 segments

# Perform clustering
segments = engine.cluster(k=optimal['optimal_k'])

# Generate profiles
profiles = engine.generate_segment_profiles()
names = engine.suggest_segment_names(profiles)

for profile, name in zip(profiles, names):
    print(f"{name}: {profile['size']} customers, gap {profile['gap']:.1f}")
```

### Navigation Example: 3 Segments

**Segment 1: Crisis Avoiders (30% of customers)**
- Avg importance: 9.1/10
- Avg satisfaction: 3.2/10
- Gap: 5.9 (severely underserved)
- Top needs: Minimize underestimating departure, bypass traffic, reduce stress
- **Target priority:** P0 (highest value creation)

**Segment 2: Satisfied Users (25% of customers)**
- Avg importance: 5.3/10
- Avg satisfaction: 8.1/10  
- Gap: -2.8 (overserved)
- Top needs: Minimize fuel consumption, reduce stops
- **Target priority:** P3 (low value opportunity)

**Segment 3: Balanced Users (45% of customers)**
- Avg importance: 7.4/10
- Avg satisfaction: 5.9/10
- Gap: 1.5 (moderately underserved)
- Top needs: Minimize travel time, plan route efficiently
- **Target priority:** P1 (secondary target)

---

## Segment Profiles

For each segment, document:

1. **Size & Demographics:** % of total, age/location patterns
2. **Top Needs:** 5 highest-importance needs for this segment
3. **Opportunity Scores:** Average across all needs
4. **EVC:** Dollar value per customer in this segment
5. **Characteristics:** Behavioral patterns, circumstances
6. **Go-to-Market:** How to reach them, messaging themes

**Output Format:**

```markdown
## Segment: Crisis Avoiders

**Size:** 30% of market (26 of 87 respondents)

**Profile:**
- High-frequency travelers (60+ trips/month)
- Professional roles (executives, sales, consultants)
- Urban/suburban locations
- High time value ($75-100/hour)

**Top 5 Needs:**
1. Minimize likelihood of underestimating departure time (imp: 9.8, sat: 2.1)
2. Minimize time in congested traffic (imp: 9.5, sat: 2.8)
3. Minimize uncertainty about traffic (imp: 9.2, sat: 3.0)
4. Minimize stress during travel (imp: 8.9, sat: 2.5)
5. Minimize likelihood of getting lost (imp: 8.7, sat: 3.2)

**Avg Opportunity Score:** 14.8 (extremely high)

**EVC:** $3,200/month = $38,400/year

**Optimal Price:** $640-960/month (20-30% of EVC)

**Characteristics:**
- Always stressed about being late
- Use multiple navigation apps
- Plan trips meticulously but still arrive late 20% of time
- Willing to pay premium for reliability

**Go-to-Market:**
- Target: LinkedIn ads to professionals
- Messaging: "Never be late again - guaranteed arrival time predictions"
- Positioning: Premium reliability for high-stakes travel
```

---

## Strategic Segmentation Decisions

### Which Segment to Target First?

**Decision matrix:**

| Segment | Opportunity | EVC/Year | Size | Ease to Reach | Priority |
|---------|-------------|----------|------|---------------|----------|
| Crisis Avoiders | 14.8 | $38,400 | 30% | Hard (niche) | **P0** |
| Balanced Users | 11.2 | $20,400 | 45% | Easy (broad) | **P1** |
| Satisfied Users | 6.1 | $4,800 | 25% | N/A | **P3** |

**Recommendation:** Start with Crisis Avoiders
- Highest willingness to pay ($960/month sustainable)
- Clearest pain points (severely underserved)
- Beachhead for expansion to Balanced Users

### Differentiated Value Propositions

**Crisis Avoiders:**
- "Guaranteed on-time arrival with AI-powered departure recommendations"
- Emphasize: Reliability, stress reduction, professional image

**Balanced Users:**
- "Smart navigation that saves you time and hassle"
- Emphasize: Efficiency, convenience, time savings

**Satisfied Users:**
- Target later, not at first (happy with current solutions)
- Potential future upsell after establishing market presence

---

**Phase 8 Complete!**

---

# Phase 9: Willingness-to-Pay Validation

## What Happens in This Phase

**Goal:** Validate that customers will actually pay your proposed price using a 6-layer framework.

**Duration:** 15-20 minutes

**Key Principle:** WTP must be grounded in economic reality. Use multiple validation layers to ensure pricing is realistic.

**Why This Matters:**

EVC says what value you create ($20K/year). But will customers pay $5K/year?

6-Layer validation provides:
- Statistical validation (outlier removal)
- Market positioning (vs. competitors)
- Economic validation (vs. EVC)
- Confidence scoring (data quality)
- Segment-specific benchmarks
- Psychological price points (Van Westendorp)

---

## The 6-Layer Framework

### Layer 1: Statistical Outlier Detection

Remove extreme WTP responses using IQR method:
- Q1 (25th percentile), Q3 (75th percentile)
- IQR = Q3 - Q1
- Remove: WTP < Q1 - 1.5×IQR or WTP > Q3 + 1.5×IQR

**Example:** 
- Raw WTP range: $50-$2,000/month
- After outlier removal: $200-$800/month
- Clean median: $425/month

### Layer 2: Comparative Benchmarking

Compare to current market pricing:
- Google Maps: $0 (ad-supported)
- Waze: $0 (ad-supported)
- Premium nav apps: $10-50/month
- **Your price:** $425/month

**Assessment:** Significant premium justified by unique value (departure predictions)

### Layer 3: Value Economics Check

**Rule:** WTP should be 20-30% of EVC

- EVC: $20,376/year
- Validated WTP: $5,100/year (25% of EVC) ✅
- Range: $4,075-$6,113 (20-30%)

**Result:** PASS (within optimal range)

### Layer 4: Confidence Scoring

Assess data quality:
- Sample size: 87 respondents (>50) ✅
- Consistency: CV = 0.35 (acceptable) ✅
- Segment alignment: WTP aligns with EVC by segment ✅

**Confidence:** High

### Layer 5: Segment-Specific Benchmarks

Validate each segment separately:

| Segment | EVC/Year | WTP Median | Capture % | Pass? |
|---------|----------|------------|-----------|-------|
| Crisis Avoiders | $38,400 | $960/month | 30% | ✅ |
| Balanced Users | $20,400 | $425/month | 25% | ✅ |
| Occasional | $4,560 | $95/month | 25% | ✅ |

### Layer 6: Van Westendorp PSM (Optional)

If you collected 4 price questions:
- "Too expensive" threshold: $800/month
- "Too cheap" threshold: $150/month
- **Acceptable range:** $200-700/month
- **Optimal price point:** $425/month

---

## Using wtp_validator.py

```python
from scripts.wtp_validator import WTPValidator

# Initialize with WTP data and EVC
validator = WTPValidator(wtp_data=wtp_series, evc=20376)

# Run all validation layers
result = validator.validate_all_layers(
    benchmarks={'google_maps': 0, 'premium_nav': 50},
    segments=segment_wtp_data
)

if result['overall_passed']:
    print(f"✅ WTP validated: ${result['validated_wtp_range']}")
    print(f"Confidence: {result['confidence']}")
else:
    print(f"❌ WTP validation failed: {result['recommendation']}")
```

---

**Phase 9 Complete!**

---

# Phase 10: Output & Integration

## What Happens in This Phase

**Goal:** Export structured data and integrate findings with downstream workflows (PRD, brainstorm, design).

**Duration:** 10-15 minutes

**Output:** Complete opportunity analysis package ready for product development.

---

## Structured Output Format

```json
{
  "job": "Get to Destinations on Time",
  "date": "2026-01-21",
  "summary": {
    "top_opportunity": "Minimize likelihood of underestimating departure time",
    "opportunity_score": 15.8,
    "total_evc_year": 20376,
    "recommended_price_month": 425,
    "target_segment": "Crisis Avoiders",
    "market_size_pct": 30
  },
  "top_opportunities": [
    {
      "rank": 1,
      "need": "Minimize likelihood of underestimating departure time",
      "importance": 9.3,
      "satisfaction": 2.8,
      "gap": 6.5,
      "opportunity_score": 15.8,
      "annual_cost": 6336
    }
  ],
  "segments": [
    {
      "name": "Crisis Avoiders",
      "size_pct": 30,
      "avg_importance": 9.1,
      "avg_satisfaction": 3.2,
      "gap": 5.9,
      "evc_month": 3200,
      "optimal_price_month": 800,
      "top_needs": [...]
    }
  ],
  "recommendations": {
    "primary_target": "Crisis Avoiders",
    "solution_focus": "Real-time execution support + departure prediction",
    "pricing_strategy": "Tiered by segment ($95-960/month)",
    "go_to_market": "LinkedIn targeting professionals, emphasize reliability"
  }
}
```

---

