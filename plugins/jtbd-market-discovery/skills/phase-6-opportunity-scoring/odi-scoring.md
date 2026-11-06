
## What Happens in This Phase

**Goal:** Calculate opportunity scores for all 80-100 needs and identify which ones are most underserved.

**Duration:** 10-20 minutes (mostly automated)

**Key Principle:** Opportunity = Importance + Gap (where Gap = max(Importance - Satisfaction, 0))

**Why This Matters:**

Survey data alone doesn't tell you where opportunities exist. You need to **combine** importance and satisfaction:

**High Importance + Low Satisfaction = High Opportunity** 🎯

Examples:
- Need rated 9/10 importance, 3/10 satisfaction → **Opportunity score: 15/20** (severely underserved)
- Need rated 5/10 importance, 8/10 satisfaction → **Opportunity score: 5/20** (overserved)
- Need rated 8/10 importance, 8/10 satisfaction → **Opportunity score: 8/20** (appropriately served)

The ODI opportunity algorithm reveals which needs matter most AND are served worst by current solutions.

---

## The ODI Opportunity Algorithm

### Formula (Additive)

```
Opportunity Score = Importance + max(Importance - Satisfaction, 0)
```

**Where:**
- **Importance:** Average rating across all respondents (1-10)
- **Satisfaction:** Average rating across all respondents (1-10)
- **Gap:** Importance - Satisfaction (a negative gap counts as 0)

**Score range:** 0-20
- **15-20:** Extremely high opportunity (severely underserved)
- **12-15:** High opportunity (underserved)
- **10-12:** Moderate opportunity
- **<10:** Low opportunity (appropriately served or overserved)

### Why This Formula Works

**Component 1: Importance**

Every need starts with its importance score. This ensures high-importance needs rank higher than low-importance needs, even if satisfaction is similar.

**Component 2: Gap (capped at zero)**

Add the gap between importance and satisfaction, but only if it's positive. This rewards underserved needs.

**Examples:**

**Example 1: Severely Underserved**
- Importance: 9.2
- Satisfaction: 3.1
- Gap: 9.2 - 3.1 = 6.1
- **Opportunity: 9.2 + 6.1 = 15.3** ✅ Top target

**Example 2: Appropriately Served**
- Importance: 8.5
- Satisfaction: 7.8
- Gap: 8.5 - 7.8 = 0.7
- **Opportunity: 8.5 + 0.7 = 9.2** ↔️ Adequate

**Example 3: Overserved**
- Importance: 5.0
- Satisfaction: 9.0
- Gap: 5.0 - 9.0 = -4.0 → max(0, -4.0) = 0
- **Opportunity: 5.0 + 0 = 5.0** ❌ No opportunity

### Alternative: Multiplicative Algorithm

```
Opportunity Score = Importance × (Importance - Satisfaction)
```

**When to use:**
- Emphasizes importance more heavily
- Penalizes low-importance needs more severely
- Creates wider spread in scores

**Recommendation:** Start with additive (standard ODI). Use multiplicative only if you want to heavily weight importance.

---

## Running the Analysis

### Using opportunity_scorer.py (Claude Code)

```
Claude: Let's calculate opportunity scores using your survey data.

        I'll run the opportunity_scorer.py script.

        *Executes Python script*

You: [Script runs]

Claude: Analysis complete!

        Top 20 Opportunities (sorted by score):

        1. Minimize likelihood of underestimating departure time
           Importance: 9.3 | Satisfaction: 2.8 | Gap: 6.5 | Opportunity: 15.8

        2. Minimize total travel time
           Importance: 9.1 | Satisfaction: 4.2 | Gap: 4.9 | Opportunity: 14.0

        3. Minimize time spent in congested traffic
           Importance: 8.9 | Satisfaction: 3.6 | Gap: 5.3 | Opportunity: 14.2

        ... (showing all 20)

        Categories:
        - Severely Underserved (gap > 5): 8 needs
        - Underserved (gap > 1): 22 needs
        - Appropriately Served (gap -1 to 1): 35 needs
        - Overserved (gap < -1): 20 needs
```

### Web Fallback (Claude.ai)

```
Claude: I'll calculate opportunity scores using AI-powered analysis.

        Based on your survey data:
        - 87 respondents
        - 85 needs

        Calculating average importance and satisfaction per need...
        Applying ODI opportunity formula...

        *Performs calculations*

        Top 20 Opportunities:

        1. Minimize likelihood of underestimating departure time
           Score: 15.8 (Importance: 9.3, Satisfaction: 2.8)

        ... (continues)
```

---

## Opportunity Score Interpretation

### Score Bands

**15-20: Extremely High Opportunity** 🔥
- **What it means:** Customers desperately want this, current solutions fail badly
- **Strategic priority:** Primary innovation targets
- **Action:** Build solutions focused on these needs
- **Example:** "Minimize likelihood of underestimating departure time" (15.8)

**12-15: High Opportunity** 🎯
- **What it means:** Significant unmet needs, clear improvement opportunity
- **Strategic priority:** Secondary targets or bundle with primary
- **Action:** Address in version 1 or version 2 of solution
- **Example:** "Minimize time spent in congested traffic" (14.2)

**10-12: Moderate Opportunity** ↔️
- **What it means:** Needs are important, satisfaction is decent
- **Strategic priority:** Nice-to-have improvements
- **Action:** Address if low-cost, otherwise defer
- **Example:** "Minimize time to plan route" (10.8)

**<10: Low Opportunity** ↓
- **What it means:** Either not important, or already well-served
- **Strategic priority:** Not worth targeting
- **Action:** Ignore unless part of broader solution
- **Example:** "Minimize time to conclude trip" (5.2)

### Gap Analysis

**Gap > 5: Severely Underserved**
- Customers rate importance very high (8-10)
- But satisfaction is very low (1-4)
- **Massive opportunity for innovation**
- Current solutions are fundamentally broken

**Gap 1-5: Underserved**
- Importance exceeds satisfaction by moderate amount
- **Good opportunity for incremental innovation**
- Current solutions work but have clear deficiencies

**Gap -1 to 1: Appropriately Served**
- Importance and satisfaction are aligned
- **No opportunity** (market is satisfied)
- Innovate here only to disrupt

**Gap < -1: Overserved**
- Satisfaction exceeds importance
- **Negative opportunity** (customers care little)
- Current solutions over-deliver on low-priority needs

---

## Complete Navigation Example

### Top 20 Opportunities (Full Results)

| Rank | Need | Importance | Satisfaction | Gap | Opportunity | Category |
|------|------|------------|--------------|-----|-------------|----------|
| 1 | Minimize likelihood of underestimating departure time | 9.3 | 2.8 | 6.5 | **15.8** | Severely Underserved |
| 2 | Minimize time spent in congested traffic | 8.9 | 3.6 | 5.3 | **14.2** | Severely Underserved |
| 3 | Minimize total travel time | 9.1 | 4.2 | 4.9 | **14.0** | Underserved |
| 4 | Minimize uncertainty about traffic conditions | 8.8 | 4.0 | 4.8 | **13.6** | Underserved |
| 5 | Minimize stress during travel | 8.5 | 4.3 | 4.2 | **12.7** | Underserved |
| 6 | Minimize likelihood of getting lost | 8.2 | 4.5 | 3.7 | **11.9** | Underserved |
| 7 | Minimize time to estimate departure time | 8.0 | 4.2 | 3.8 | **11.8** | Underserved |
| 8 | Minimize uncertainty about arrival time | 8.3 | 4.8 | 3.5 | **11.8** | Underserved |
| 9 | Minimize likelihood of selecting suboptimal route | 7.9 | 4.6 | 3.3 | **11.2** | Underserved |
| 10 | Minimize time to plan the route | 7.8 | 4.7 | 3.1 | **10.9** | Underserved |
| 11 | Minimize number of wrong turns made | 7.6 | 5.1 | 2.5 | **10.1** | Moderate |
| 12 | Minimize wasted time during travel | 7.5 | 5.2 | 2.3 | **9.8** | Moderate |
| 13 | Minimize effort to monitor progress | 7.2 | 5.4 | 1.8 | **9.0** | Moderate |
| 14 | Minimize time to check travel progress | 6.9 | 5.8 | 1.1 | **8.0** | Appropriate |
| 15 | Minimize fuel consumption | 6.5 | 6.2 | 0.3 | **6.8** | Appropriate |
| 16 | Minimize number of stops required | 5.8 | 6.5 | 0 | **5.8** | Overserved |
| 17 | Minimize time to prepare items | 5.5 | 7.0 | 0 | **5.5** | Overserved |
| 18 | Minimize effort to note lessons learned | 4.2 | 6.8 | 0 | **4.2** | Overserved |
| 19 | Minimize time to conclude trip | 3.8 | 7.5 | 0 | **3.8** | Overserved |
| 20 | Minimize time documenting trip | 2.9 | 6.5 | 0 | **2.9** | Overserved |

**Key Insights:**

1. **Top cluster: Real-time execution support** (needs #1-5)
   - All about avoiding being late and dealing with uncertainty
   - Gap averages 5.1 (severely underserved)
   - Primary innovation target

2. **Secondary cluster: Planning and preparation** (needs #7, 9-10)
   - Estimating departure, route planning
   - Gap averages 3.4 (underserved)
   - Supporting innovation target

3. **Overserved cluster: Peripheral needs** (needs #16-20)
   - Documentation, preparation minutiae
   - Gap < 0 (current solutions over-deliver)
   - Skip innovation here

---

## Visualization

### Opportunity Landscape (Importance vs. Satisfaction)

```
Satisfaction
↑
10│                    ○ ○ ○        [Overserved]
  │              ○ ○ ○ ○
  │          ○ ○ ○
8 │      ○ ○                        [Appropriately Served]
  │  ○ ○ ○
  │○ ○
6 │
  │
  │
4 │    ①②③④⑤                       [OPPORTUNITY ZONE]
  │    ⑥⑦⑧⑨⑩                       [Severely Underserved]
2 │
  │
  └────────────────────────────────→ Importance
   2    4    6    8   10

Legend:
① Top opportunity (rank 1)
○ Other needs
Numbers 1-10 = Top 10 opportunities
```

**Reading the chart:**
- **Bottom right:** High importance, low satisfaction = **Opportunity zone** 🎯
- **Top right:** High importance, high satisfaction = Well-served (maintain)
- **Top left:** Low importance, high satisfaction = Overserved (reduce investment)
- **Bottom left:** Low importance, low satisfaction = Not worth addressing

---

## Strategic Prioritization

### Priority Matrix

**High Opportunity + High Effort = Top Priority**

Combine opportunity scores (Phase 6) with effort quantification (Phase 4):

| Need | Opportunity | Annual Cost | Priority |
|------|-------------|-------------|----------|
| Underestimate departure time | 15.8 | $6,336 | **P0** 🔥 |
| Time in congested traffic | 14.2 | $3,840 | **P0** 🔥 |
| Total travel time | 14.0 | $21,024 | **P0** 🔥 |
| Traffic condition uncertainty | 13.6 | $2,880 | **P1** 🎯 |
| Stress during travel | 12.7 | $2,160 | **P1** 🎯 |
| Getting lost | 11.9 | $1,200 | **P2** |
| Estimate departure time | 11.8 | $6,336 | **P0** 🔥 |

**Priority levels:**
- **P0:** High opportunity + high cost = Must solve
- **P1:** High opportunity + medium cost = Should solve
- **P2:** Moderate opportunity or low cost = Nice to have

### Target Selection Criteria

**Choose top 5-10 needs that:**
1. ✅ Score > 12 (high opportunity)
2. ✅ Annual cost > $2,000 (high effort)
3. ✅ Cluster together thematically
4. ✅ Are addressable by one coherent solution

**Example: Navigation app focus**

**Selected targets (5 needs):**
1. Minimize likelihood of underestimating departure time (15.8)
2. Minimize time spent in congested traffic (14.2)
3. Minimize total travel time (14.0)
4. Minimize uncertainty about traffic conditions (13.6)
5. Minimize time to estimate departure time (11.8)

**Theme:** Real-time execution + pre-trip planning

**Solution concept:** Intelligent departure time recommendation + real-time traffic-aware routing

---

## Output from Phase 6

### Deliverable: Opportunity Scorecard

```markdown
# Opportunity Scorecard
# Job: Get to Destinations on Time
# Date: January 21, 2026
# Survey: 87 respondents, 85 needs

## Executive Summary

**Top Opportunity:** Minimize likelihood of underestimating departure time (15.8/20)

**Market Characterization:**
- 8 severely underserved needs (opportunity > 14)
- 22 underserved needs (opportunity 10-14)
- 35 appropriately served needs (opportunity 7-10)
- 20 overserved needs (opportunity < 7)

**Strategic Focus:** Real-time execution support during travel (61% of total opportunity)

## Top 10 Opportunities

1. Minimize likelihood of underestimating departure time - **15.8**
2. Minimize time spent in congested traffic - **14.2**
3. Minimize total travel time - **14.0**
4. Minimize uncertainty about traffic conditions - **13.6**
5. Minimize stress during travel - **12.7**
6. Minimize likelihood of getting lost - **11.9**
7. Minimize time to estimate departure time - **11.8**
8. Minimize uncertainty about arrival time - **11.8**
9. Minimize likelihood of selecting suboptimal route - **11.2**
10. Minimize time to plan the route - **10.9**

**Average opportunity score:** 13.5 (high opportunity cluster)

## Opportunity by Job Phase

- **UNDERSTAND:** 10.2 average (moderate opportunity)
- **PLAN:** 10.8 average (moderate opportunity)
- **EXECUTE:** 13.1 average (high opportunity) ← **Primary target**
- **ASSESS:** 8.5 average (low opportunity)
- **REVISE:** 6.2 average (low opportunity)
- **CONCLUDE:** 4.5 average (low opportunity)

**Insight:** 78% of high-opportunity needs are in EXECUTE phase.

---

**Next Phase:** Economic Value Calculation (Phase 7)
```

---

## Tips for Success in Phase 6

### 1. Don't Cherry-Pick Opportunities

**Bad:** "I like need #15 because it fits my product idea"
**Good:** "Top 3 opportunities are #1, #2, #3. Let me design solutions for those."

Let data drive decisions, not pre-existing solutions.

### 2. Look for Opportunity Clusters

Individual needs are interesting, but **clusters reveal themes**.

**Example:** Top 5 needs all relate to "uncertainty and delays during execution"
→ This reveals the **core job pain point**

### 3. Validate Opportunity Scores

**Sanity checks:**
- Do top opportunities align with customer complaints you've heard?
- Do overserved needs match areas where you suspected over-engineering?
- Are there any surprises? (Good! That's why you surveyed.)

If results seem wrong, check data quality first.

### 4. Don't Ignore Appropriately Served Needs

**Opportunity score 8-10** doesn't mean "ignore it."

It means: "Current solutions are adequate, but improvements still matter."

**Strategy:** Bundle these with high-opportunity needs.

### 5. Share Results Broadly

Opportunity scorecards are powerful communication tools:
- Show executives where market gaps exist
- Align product teams on priorities
- Justify innovation investments with data

---

## Common Questions

**Q: What if all my needs have similar opportunity scores?**

A: Two possibilities:
1. Survey respondents are too homogeneous (need more diverse sample)
2. All needs are genuinely important and underserved (rare but possible)

Look at the absolute gaps. Even if scores are similar, gaps reveal which needs are most broken.

**Q: Should I target needs with highest opportunity or highest effort cost?**

A: **Both.** Ideal targets are high opportunity AND high cost. That's where you create maximum value.

Formula: `Priority = Opportunity Score × Annual Cost`

**Q: What if top opportunities aren't addressable by my solution?**

A: Then either:
1. Expand your solution scope
2. Partner with others to address them
3. Accept that you're targeting secondary opportunities (still valuable, just not optimal)

**Q: How do I explain opportunity scores to non-technical stakeholders?**

A: Use simple language:
- "Score 15 = customers desperately want this, current options fail badly"
- "Score 8 = customers are satisfied with current options"
- "Higher scores = bigger opportunities to create value"

**Q: Can opportunity scores change over time?**

A: Yes! As market conditions change:
- New competitors may improve satisfaction (scores drop)
- Customer needs may evolve (importance shifts)
- New circumstances may emerge (different needs matter)

Re-survey every 12-18 months to track changes.

---

## Ready for Phase 7?

Once you've identified your top 5-10 opportunities, we'll move to **Phase 7: Economic Value Calculation** to quantify the dollar value of serving those needs better.

To continue:

```
> "I'm ready for Phase 7"
```

Or to pause and review opportunity scores:

```
> "Save opportunity scorecard and pause"
```

---

**Phase 6 Complete!**

---

# Phase 7: Economic Value Calculation

## What Happens in This Phase

**Goal:** Quantify the dollar value of serving your top 5-10 opportunities better than current solutions.

**Duration:** 30-45 minutes

**Key Principle:** Economic Value to Customer (EVC) = All benefits a solution creates, measured in dollars.

**Why This Matters:**

Opportunity scores tell you WHAT to build. EVC tells you HOW MUCH VALUE it creates.

**Example:**
- Opportunity score 15.8 = "Customers really want this"
- EVC $13,500/year = "We can create $13,500/year in value per customer"
- Optimal pricing = 20-30% of EVC = $2,700-$4,050/year

EVC answers critical questions:
- How much should we charge?
- What's the ROI for customers?
- Is this opportunity economically viable?
- Which segment should we target?

---

## The EVC Framework

### Four Value Components

**1. Time Savings**
```
Value = Hours saved × Hourly rate
```

**Example:** Navigation app saves 15 hours/month × $50/hour = $750/month

**2. Error Reduction**
```
Value = Errors avoided × Cost per error
```

**Example:** Prevent 0.5 late arrivals/month × $200/arrival = $100/month

**3. Revenue Increase**
```
Value = Additional revenue × Margin
```

**Example:** Salesperson makes 2 extra calls/month × $500 revenue × 20% margin = $200/month

**4. Risk Reduction**
```
Value = Probability reduction × Risk cost
```

**Example:** Reduce 5% accident risk × $5,000 cost = $250/month expected value

**Total EVC = Sum of all four components + Performance Premium**

### Performance Differentiation Premium

Add a premium for superior performance vs. alternatives:

- **Low differentiation (5-10%):** Minor improvements
- **Medium differentiation (15-25%):** Significant improvements (most common)
- **High differentiation (30-50%):** Breakthrough innovation

**Formula:**
```
Total EVC = (Time + Errors + Revenue + Risk) × (1 + Premium %)
```

---

## Guided EVC Calculation

### Navigation App Example

Let me walk through a complete EVC calculation.

```
Claude: Let's calculate EVC for your navigation solution.

        We'll focus on the top 5 opportunities:
        1. Minimize likelihood of underestimating departure time
        2. Minimize time spent in congested traffic
        3. Minimize total travel time
        4. Minimize uncertainty about traffic conditions
        5. Minimize time to estimate departure time

        Component 1: Time Savings

        Question: How much time will your solution save per month?

        Think about:
        - Pre-trip planning time reduced
        - In-transit time saved (avoiding traffic)
        - Rework time saved (fewer late arrivals)

You: Current planning takes 8 min/trip × 48 trips = 6.4 hours/month
     With smart recommendations, maybe 3 min/trip = 2.4 hours/month
     Savings: 4 hours/month

     Traffic avoidance could save 5 min/trip × 48 = 4 hours/month

     Total time savings: 8 hours/month

Claude: Excellent quantification.

