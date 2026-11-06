
## What Happens in This Phase

**Goal:** Quantify the current time and effort required to accomplish your top 30-40 customer needs.

**Duration:** 30-60 minutes

**Key Principle:** Establish baseline metrics **before** introducing any solution. This creates the foundation for calculating value improvements later.

**Why This Matters:**

You can't measure improvement without knowing the starting point. Time-task analysis quantifies:
- **Current time** per task (minutes/hours)
- **Frequency** (per day/week/month)
- **Error rates** (% of time things go wrong)
- **Rework time** (when errors occur)
- **Annual cost** (time × frequency × rate)

This data becomes critical for:
1. **Economic Value Calculation (Phase 7)** - Quantifying time/error savings
2. **Prioritization** - High-effort needs are prime improvement targets
3. **ROI Justification** - Proving value to stakeholders
4. **Solution Design** - Understanding where effort concentrates

**Example:**

Without time-task analysis:
- ❌ "Navigation would be useful" (vague, no numbers)

With time-task analysis:
- ✅ "Current approach takes 5 min per trip × 60 trips/month = 5 hours/month"
- ✅ "At $50/hour, that's $250/month in time costs"
- ✅ "10% error rate (late arrivals) costs $200/month in missed opportunities"
- ✅ "Total current cost: $450/month = $5,400/year"

Now you can calculate ROI: If a solution costs $120/year and saves $5,400/year, that's 45x ROI.

---

## What to Measure

### Focus on Top Needs Only

**Measure the top needs, not all 80-100.** Measuring all of them costs much time and is not needed.

**Do measure top 30-40 needs** based on:
- Highest perceived importance
- Most frequent occurrence
- Highest frustration level
- Known pain points

**How to select:**

```
Claude: We generated 85 needs. Let's identify which ones to measure.

        Question: Which needs occur most frequently in your day-to-day?

You: Estimating departure time, planning the route, monitoring progress, adjusting for changes

Claude: Good start. Let's focus on the EXECUTE phase needs since that's where you spend most time.

        From your 12 job steps, let's prioritize:
        - Step 1: Estimate departure time (10 needs) → Measure top 5
        - Step 4: Plan the route (10 needs) → Measure top 5
        - Step 6: Travel to destination (12 needs) → Measure top 8
        - Step 7: Monitor progress (8 needs) → Measure top 5
        - Step 8: Adjust for changes (10 needs) → Measure top 5

        That's 28 needs to measure. Sound manageable?
```

### Core Metrics Per Need

For each need, estimate:

1. **Current Time** - How long does this task take now? (minutes or hours)
2. **Frequency** - How often does this occur? (per day/week/month)
3. **Error Rate** - What % of time do things go wrong? (0-100%)
4. **Rework Time** - When errors occur, how long to fix? (minutes or hours)
5. **Hourly Rate** - What's the value of time spent? ($/hour)

---

## Guided Estimation Process

### Example: Need #1 - "Minimize time to estimate departure time"

Let me guide you through quantifying this need.

```
Claude: Let's quantify "Minimize time it takes to estimate departure time"

        Current Time Per Task

        Question: When you need to estimate departure time, how long does it currently take?

        Think about:
        - Looking up the destination
        - Checking traffic conditions
        - Considering weather
        - Doing mental math

        How many minutes?

You: Maybe 5 minutes if traffic is normal, 10-15 if I have to check multiple sources

Claude: Let's use a realistic average.

        Current Time: 8 minutes (blended average)

        Is that reasonable? (We can adjust later if needed)

You: Yes, 8 minutes sounds about right

Claude: Frequency

        Question: How often do you need to estimate departure time?

        Think about:
        - Daily commute (2x per day?)
        - Weekend trips
        - Appointments
        - Social events

        How many times per month?

You: Twice a day for work, so 40 times per month. Plus weekends maybe 8 more times. So 48 total.

Claude: Perfect!

        Frequency: 48 times per month

        Error Rate

        Question: What percentage of the time do you underestimate or overestimate significantly?

        "Significantly" means:
        - Underestimate: Arrive >10 minutes late
        - Overestimate: Arrive >20 minutes early (wasted time)

        What % of trips?

You: I'm late maybe 10% of the time. I'm way too early maybe 5%. So 15% error rate.

Claude: Error Rate: 15%

        Rework Time

        Question: When you underestimate, what's the cost?

        Think about:
        - Stress during rushed travel
        - Missed meeting time
        - Apologies and rescheduling

        Let's focus on time cost: How much time is wasted dealing with being late?

You: If I'm late, I usually have to apologize, wait for the next opening, or reschedule. Maybe 20 minutes wasted on average.

Claude: Rework Time: 20 minutes when errors occur

        Hourly Rate

        Question: What's your hourly rate?

        For personal time: What do you value your time at?
        For work time: What's your actual hourly rate?

You: For work trips, $75/hour. For personal, maybe $50/hour is fair.

Claude: Let's use a blended rate.

        Hourly Rate: $60/hour (weighted average)

        Current Cost Calculation

        Monthly Time Cost:
        - Time per task: 8 minutes = 0.133 hours
        - Frequency: 48 times/month
        - Total time: 0.133 × 48 = 6.4 hours/month
        - Cost: 6.4 hours × $60/hour = $384/month

        Monthly Error Cost:
        - Error rate: 15%
        - Errors per month: 48 × 0.15 = 7.2 errors
        - Rework time: 20 minutes = 0.333 hours
        - Total rework: 7.2 × 0.333 = 2.4 hours/month
        - Cost: 2.4 hours × $60/hour = $144/month

        Total Current Cost for Need #1:
        - Time: $384/month
        - Errors: $144/month
        - Total: $528/month = $6,336/year

        That's the current cost of this single need!
```

**Key Insight:** Just **one need** costs $6,336/year. Multiply across 30-40 needs to see total opportunity.

---

## Effort Categorization

After quantifying needs, categorize by effort level:

### High-Effort Needs

**Criteria:**
- Takes >1 hour per occurrence, OR
- Occurs very frequently (>20x/month), OR
- Has high error rate (>20%), OR
- Annual cost >$3,000

**Example: Navigation domain**
- Need #1: Estimate departure time ($6,336/year) → **High effort**
- Need #25: Plan the route ($4,800/year) → **High effort**
- Need #60: Identify need for adjustment ($180/year) → Low effort

**Strategic Priority:** High-effort needs are your **primary targets** for innovation. Solving these creates massive value.

### Medium-Effort Needs

**Criteria:**
- Takes 15-60 minutes per occurrence, OR
- Occurs occasionally (5-20x/month), OR
- Has moderate error rate (10-20%), OR
- Annual cost $1,000-$3,000

**Example:**
- Need #17: Plan required stops ($2,400/year) → Medium effort
- Need #52: Check travel progress ($1,800/year) → Medium effort

**Strategic Priority:** Medium-effort needs are **secondary targets**. Bundle multiple into one solution.

### Low-Effort Needs

**Criteria:**
- Takes <15 minutes per occurrence, AND
- Occurs infrequently (<5x/month), AND
- Has low error rate (<10%), AND
- Annual cost <$1,000

**Example:**
- Need #81: Note lessons learned ($120/year) → Low effort
- Need #85: Conclude the trip ($0/year) → Low effort

**Strategic Priority:** Low-effort needs seldom justify dedicated solutions. Address them if it's "free" (no additional cost).

---

## Annual Cost Summary

After measuring 30-40 needs, create a summary:

### Example: Navigation App - Top 30 Needs

| Need ID | Need Statement | Annual Cost | Effort Level |
|---------|---------------|-------------|--------------|
| 1 | Minimize time to estimate departure time | $6,336 | High |
| 25 | Minimize time to plan the route | $4,800 | High |
| 40 | Minimize total travel time | $8,400 | High |
| 52 | Minimize time to check progress | $2,880 | Medium |
| 4 | Minimize likelihood of underestimating departure | $2,400 | Medium |
| 60 | Minimize time to identify need for adjustment | $1,920 | Medium |
| 44 | Minimize likelihood of getting lost | $1,200 | Medium |
| 30 | Minimize likelihood of selecting suboptimal route | $960 | Low |
| ... | ... | ... | ... |

**Totals:**
- **High-effort needs (8):** $42,000/year
- **Medium-effort needs (14):** $21,000/year
- **Low-effort needs (8):** $4,000/year
- **Grand Total (30 needs):** $67,000/year

**Insight:** The current "cost" of getting to destinations on time is **$67,000/year** in wasted time and errors.

This becomes your **value creation opportunity**. If you can eliminate 50% of that waste, you create $33,500/year in value per customer.

---

## Estimation Techniques

### Technique 1: Personal Experience

**For jobs you do yourself:**

```
Claude: Since you personally do this job, let's use your direct experience.

        Think about the last 5 times you [estimated departure time].

        Question: How long did it take each time?

You: The quick trips took 3-4 minutes. The complex ones took 15 minutes.

Claude: So we have a range: 3-15 minutes.

        What's the typical scenario? (The one that happens 70% of the time)

You: Usually it's straightforward, so 5 minutes

Claude: Current Time: 5 minutes (typical case)

        We can note the range (3-15) for later sensitivity analysis.
```

### Technique 2: Customer Interviews

**For jobs others do:**

```
Claude: You mentioned you interviewed 3 customers about their travel habits.

        Question: What did they say about time to plan routes?

You: One said "about 10 minutes", another said "5 minutes usually", the last one said "depends, but probably 8 minutes on average"

Claude: Average: (10 + 5 + 8) / 3 = 7.7 minutes

        Current Time: 8 minutes (rounded)

        That's based on real customer data, which is better than guessing!
```

### Technique 3: Time Studies

**For observable tasks:**

```
Claude: Can you observe yourself or others doing this task?

You: Yes, I can track it next week

Claude: Perfect! Track these for 5-10 instances:
        - Start time
        - End time
        - Any interruptions (subtract those)
        - Whether errors occurred

        Then we'll calculate the average.
```

### Technique 4: Proxy Metrics

**When direct measurement is hard:**

```
Claude: "Monitor travel progress" is hard to measure directly - you do it continuously while driving.

        Let's use proxy metrics instead.

        Question: How many times do you glance at your phone/nav device during a trip?

You: Maybe 5-10 times per trip?

Claude: And each glance takes how long?

You: 2-3 seconds

Claude: Total time: 8 glances × 2.5 seconds = 20 seconds per trip

        Current Time: 0.33 minutes (20 seconds)

        That's a conservative estimate. We can always refine later.
```

---

## Handling Uncertainty

### Uncertainty Level 1: Single Point Estimate

**Use when:** You're confident in the estimate (±20%)

**Example:** "Route planning takes 8 minutes" → Use 8 minutes

### Uncertainty Level 2: Range Estimate

**Use when:** Moderate uncertainty (±50%)

**Example:** "Route planning takes 5-12 minutes"

**Approach:** Use midpoint for base case (8.5 minutes), track range for sensitivity analysis

### Uncertainty Level 3: Scenario-Based

**Use when:** High variance by scenario

**Example:**
- **Simple trips:** 5 minutes (30% of trips)
- **Moderate trips:** 10 minutes (50% of trips)
- **Complex trips:** 20 minutes (20% of trips)

**Weighted average:** (5 × 0.30) + (10 × 0.50) + (20 × 0.20) = 10.5 minutes

---

## Output from Phase 4

### Deliverable: Time-Task Analysis Spreadsheet

**Format:**

```csv
Need ID, Need Statement, Current Time (min), Frequency (per month), Error Rate (%), Rework Time (min), Hourly Rate ($/hr), Monthly Time Cost ($), Monthly Error Cost ($), Total Monthly Cost ($), Annual Cost ($), Effort Level

1, Minimize time to estimate departure time, 8, 48, 15%, 20, 60, 384, 144, 528, 6336, High
25, Minimize time to plan the route, 10, 40, 10%, 30, 60, 400, 120, 520, 6240, High
40, Minimize total travel time, 35, 48, 5%, 15, 60, 1680, 72, 1752, 21024, High
...
```

### Example Summary Report

```markdown
# Time-Task Analysis Summary
# Job: Get to Destinations on Time
# Date: January 21, 2026
# Needs Analyzed: 30 of 85

## Top 10 High-Effort Needs (by Annual Cost)

1. **Minimize total travel time** - $21,024/year
2. **Minimize time to estimate departure time** - $6,336/year
3. **Minimize time to plan the route** - $6,240/year
4. **Minimize wasted time during travel** - $4,800/year
5. **Minimize time spent in congested traffic** - $3,840/year
6. **Minimize time to check travel progress** - $2,880/year
7. **Minimize likelihood of underestimating departure** - $2,400/year
8. **Minimize stress during travel** - $2,160/year (quantified via productivity loss)
9. **Minimize time to identify need for adjustment** - $1,920/year
10. **Minimize time to implement adjustment** - $1,680/year

## Cost by Job Phase

- **UNDERSTAND:** $9,600/year (15%)
- **PLAN:** $14,400/year (23%)
- **EXECUTE:** $38,400/year (61%)
- **ASSESS:** $960/year (2%)
- **REVISE:** $0/year (0% - rarely done)
- **CONCLUDE:** $0/year (0% - trivial)

**Total Current Annual Cost:** $63,360/year

## Strategic Insights

1. **EXECUTE phase dominates effort** (61% of total cost)
   - Primary target for innovation
   - Focus on real-time execution support

2. **Top 3 needs account for 53% of total cost**
   - Concentrated opportunity
   - High ROI if solved well

3. **Error costs are 23% of total**
   - Underestimating departure time
   - Selecting suboptimal routes
   - Getting lost

4. **Planning phase significant** (23% of total)
   - Pre-trip preparation matters
   - Opportunities in decision support

---

**Next Phase:** Survey Deployment (Phase 5)
```

---

## Tips for Success in Phase 4

### 1. Be Realistic, Not Pessimistic or Optimistic

**Bad (pessimistic):** "Planning takes 30 minutes because sometimes it's really complex"
**Bad (optimistic):** "Planning takes 2 minutes because I'm usually fast"
**Good (realistic):** "Planning typically takes 8 minutes, with a range of 5-15 depending on complexity"

Use **typical case**, not best or worst case.

### 2. Include Hidden Time

Don't forget:
- **Context switching** (stopping other work to do this task)
- **Mental preparation** (gathering thoughts before starting)
- **Follow-up** (checking results, verifying completion)
- **Interruptions** (having to restart due to distractions)

**Example:**
- Visible time: 5 minutes to plan route
- Hidden time: 2 minutes to stop what you're doing, find phone, open app, return to previous task
- **Total time:** 7 minutes

### 3. Measure Frequency Accurately

**Bad:** "I do this all the time" (vague)
**Good:** "Twice per workday (10x/week) + weekends (4x/week) = 14x/week × 4.3 weeks = 60x/month"

Break frequency into components:
- Weekday frequency × weekdays per month
- Weekend frequency × weekends per month
- Special occasions × occurrences per month

### 4. Don't Ignore Low-Probability, High-Impact Events

**Example:** Getting lost

- **Frequency:** 1x per year (very rare)
- **Impact:** 30 minutes wasted + $50 gas + stress
- **Annual cost:** 1 × (0.5 hours × $60 + $50) = $80/year

Even though rare, high-impact events should be measured.

### 5. Use Hourly Rate Appropriate to Context

**Work trips:** Use actual hourly rate ($75/hr for professional)
**Personal trips:** Use reasonable personal time value ($30-50/hr)
**Mixed:** Use weighted average based on trip purpose distribution

**Example:**
- 70% work trips: $75/hr
- 30% personal trips: $40/hr
- **Blended rate:** (0.70 × $75) + (0.30 × $40) = $64.50/hr

---

## Common Questions

**Q: Do I need to measure all 80-100 needs?**

A: No. Measure top 30-40 needs (highest frequency, highest perceived importance). The other needs can be estimated later if needed.

**Q: What if I don't know the error rate?**

A: Make a conservative estimate. Example: "I'd guess about 10% of the time things go wrong." You can refine this later with actual data from the survey.

**Q: Can I skip needs that are hard to quantify?**

A: Try to quantify them with proxies. Example: "Minimize stress" is hard to measure directly, but you can proxy it with "time lost to stress-induced mistakes" or "productivity reduction during/after stressful trips."

**Q: What if current time is zero because there's no current solution?**

A: Then measure the **impact of not doing it**. Example: "Minimize likelihood of being late" - if there's no departure planning tool, people are late 20% of the time. That late arrival costs $200 each time. So annual cost = frequency × 0.20 × $200.

**Q: Should I measure time for REVISE phase needs?**

A: Only if people actually do them. Many people skip "note lessons learned" or "analyze what went wrong." If it's skipped, the current time is zero (which itself is interesting data).

---

## Ready for Phase 5?

Once you've quantified the top 30-40 needs, we'll move to **Phase 5: Survey Deployment** to collect importance and satisfaction ratings from 50+ customers.

To continue:

```
> "I'm ready for Phase 5"
```

Or to pause and export your time-task analysis:

```
> "Save my time-task data and pause"
```

---

**Phase 4 Complete!**

---

# Phase 5: Survey Deployment
