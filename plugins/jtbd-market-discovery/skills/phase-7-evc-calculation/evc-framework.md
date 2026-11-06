        Time Savings = 8 hours/month × $50/hour = $400/month

        Component 2: Error Reduction

        Question: How many late arrivals will your solution prevent?

You: Currently late 15% of time (7.2 times/month)
     With accurate departure recommendations, maybe 5% (2.4 times/month)
     Errors avoided: 4.8/month

     Cost per late arrival: $200 (missed meeting value, stress, rescheduling)

Claude: Error Reduction = 4.8 errors/month × $200 = $960/month

        Component 3: Revenue Increase

        Question: Does arriving on time generate revenue?

You: For personal travel, not really. But for work travel, being on time
     means I can take more meetings. Maybe 1 extra meeting every 2 months.

Claude: Revenue Increase = 0.5 meetings/month × $500 value × 20% = $50/month

        (Conservative estimate)

        Component 4: Risk Reduction

        Question: Does your solution reduce risk of accidents or penalties?

You: Getting lost less often reduces stress-related accidents.
     Currently 0.2% monthly risk × $5,000 accident cost = $10 expected value
     Solution reduces to 0.1% = $5 expected value
     Risk reduction: $5/month

Claude: Risk Reduction = $5/month

        Subtotal Calculation

        Time Savings:     $400/month
        Error Reduction:  $960/month
        Revenue Increase: $50/month
        Risk Reduction:   $5/month
        ─────────────────────────────
        Subtotal:        $1,415/month

        Performance Premium

        Question: How differentiated is your solution vs current options?

        - Google Maps/Waze exist (real-time traffic)
        - But they recommend no departure times on their own
        - Your solution combines prediction + real-time

        This seems like medium differentiation (significant improvement).

        Medium differentiation = 20% premium (midpoint of 15-25%)

        Premium = $1,415 × 0.20 = $283/month

        Total EVC Calculation

        Subtotal:              $1,415/month
        Performance Premium:   $283/month
        ─────────────────────────────────
        Total EVC:            $1,698/month
                              $20,376/year per customer

        That's the economic value your solution creates!
```

---

## Using evc_calculator.py

### Claude Code Workflow

```python
from scripts.evc_calculator import EVCCalculator

# Initialize calculator
calc = EVCCalculator()

# Add time savings
calc.add_time_savings(hours_saved=8, hourly_rate=50)

# Add error reduction
calc.add_error_reduction(errors_avoided=4.8, cost_per_error=200)

# Add revenue increase
calc.add_revenue_increase(additional_revenue=50)

# Add risk reduction
calc.add_risk_reduction(probability=0.001, impact=5000)

# Calculate total EVC with medium differentiation
result = calc.calculate_total_evc(differentiation_level='medium')

print(f"Total EVC: ${result['total_evc']:,.2f}/month")
# Output: Total EVC: $1,698/month
```

### Web Fallback

```
Claude: I'll calculate EVC using AI-powered reasoning.

        Based on your inputs:
        - Time: 8 hours/month × $50/hour = $400
        - Errors: 4.8 × $200 = $960
        - Revenue: $50
        - Risk: $5

        Subtotal: $1,415/month
        Premium (20%): $283/month

        Total EVC: $1,698/month = $20,376/year
```

---

## Value Capture Strategy

### Optimal Pricing Range

**Industry standard:** Capture 20-30% of EVC as price.

**Why 20-30%?**
- **< 20%:** Leaving money on table, undervaluing solution
- **20-30%:** Optimal range, attractive ROI for customers (3-5x)
- **> 30%:** Risky, customers may balk at price

**Example: Navigation app**

- Total EVC: $20,376/year
- Optimal price: $4,075-$6,113/year
- **Or: $340-$510/month**

**Customer ROI at $400/month:**
- EVC: $1,698/month
- Price: $400/month
- Net value: $1,298/month
- **ROI: 4.2x** ✅ (customers get $4.20 for every $1 spent)

---

## Segment-Specific EVC

Different segments have different EVC because they:
- Have different frequency (more/fewer trips)
- Value time differently (higher/lower hourly rates)
- Experience different error rates
- Have different risk profiles

### Example: Three Customer Segments

**Segment 1: Business Travelers (Crisis Avoiders)**
- Trips: 60/month (daily + business meetings)
- Hourly rate: $100 (professional)
- Late arrival cost: $500 (missed client meeting)
- **EVC: $3,200/month** = $38,400/year
- Optimal price: $640-$960/month

**Segment 2: Regular Commuters (Balanced Users)**
- Trips: 48/month (daily commute)
- Hourly rate: $50 (average worker)
- Late arrival cost: $150 (productivity loss)
- **EVC: $1,698/month** = $20,376/year (our example)
- Optimal price: $340-$510/month

**Segment 3: Occasional Users (Low Frequency)**
- Trips: 12/month (weekend + occasional)
- Hourly rate: $30 (personal time value)
- Late arrival cost: $50 (minor inconvenience)
- **EVC: $380/month** = $4,560/year
- Optimal price: $76-$114/month

**Strategic Implication:** You could charge 8x more to business travelers than occasional users because you create 8x more value.

---

## Sensitivity Analysis

### Test Assumptions

EVC calculations rely on assumptions. Test how sensitive results are to changes.

**Example: Hourly rate sensitivity**

| Hourly Rate | Time Value | Total EVC | Optimal Price |
|-------------|------------|-----------|---------------|
| $30 | $240 | $1,538 | $308-$461 |
| $50 | $400 | $1,698 | $340-$510 |
| $75 | $600 | $2,098 | $420-$630 |
| $100 | $800 | $2,498 | $500-$750 |

**Insight:** EVC varies significantly with hourly rate. Segment by income/profession.

**Example: Error rate sensitivity**

| Current Error Rate | Errors Avoided | Error Value | Total EVC |
|--------------------|----------------|-------------|-----------|
| 10% | 3.6 | $720 | $1,453 |
| 15% | 4.8 | $960 | $1,698 |
| 20% | 6.0 | $1,200 | $1,943 |

**Insight:** Higher error rates (people who are frequently late) get more value.

---

## Validation Checkpoints

### Reality Check Questions

**1. Does EVC pass the "laugh test"?**

If EVC = $100,000/year for a simple app, something's wrong.

**Sanity check:** Compare to:
- Current solution costs
- Comparable products
- Customer budgets

**2. Can customers actually realize this value?**

Don't count theoretical value they can't capture.

**Bad:** "Saves 5 minutes/trip, but user drives the same route anyway" (no real time savings)
**Good:** "Saves 5 minutes/trip, user leaves 5 min later or arrives 5 min earlier" (real time savings)

**3. Is value quantification credible?**

Can you prove the numbers?

**Strong proof:**
- Time studies (measured actual time)
- Customer interviews (validated error rates)
- Industry benchmarks (standard hourly rates)

**Weak proof:**
- Wild guesses
- "Feels right" estimates
- Wishful thinking

**4. Are all four components included?**

Don't just measure time. Also measure:
- Errors prevented
- Revenue generated
- Risks reduced

Missing components underestimate EVC.

---

## Output from Phase 7

### Deliverable: EVC Analysis Report

```markdown
# Economic Value Analysis
# Job: Get to Destinations on Time
# Solution: Intelligent Navigation + Departure Recommendations
# Date: January 21, 2026

## Executive Summary

**Total EVC:** $20,376/year per customer (median segment)

**Value Components:**
- Time Savings: 59% ($400/month)
- Error Reduction: 57% ($960/month)
- Revenue Increase: 3% ($50/month)
- Risk Reduction: <1% ($5/month)

**Optimal Pricing:** $4,075-$6,113/year ($340-$510/month)

**Customer ROI:** 4.2x at $400/month price point

## Value Breakdown by Component

### 1. Time Savings: $400/month

**Current state:**
- Planning time: 8 min/trip × 48 trips = 6.4 hours/month
- In-transit delays: 10 min/trip average × 48 = 8 hours/month
- Total: 14.4 hours/month

**Future state with solution:**
- Planning time: 3 min/trip × 48 = 2.4 hours/month
- In-transit delays: 5 min/trip × 48 = 4 hours/month
- Total: 6.4 hours/month

**Time saved:** 8 hours/month × $50/hour = **$400/month**

### 2. Error Reduction: $960/month

**Current state:**
- Late arrival rate: 15% (7.2 times/month)
- Cost per late arrival: $200
- Monthly cost: $1,440

**Future state with solution:**
- Late arrival rate: 5% (2.4 times/month)
- Cost per late arrival: $200
- Monthly cost: $480

**Errors prevented:** 4.8/month × $200 = **$960/month**

### 3. Revenue Increase: $50/month

**Additional meetings enabled:** 0.5/month
**Value per meeting:** $500 × 20% margin = $100
**Monthly revenue:** **$50/month**

### 4. Risk Reduction: $5/month

**Accident risk reduction:** 0.1% monthly
**Average accident cost:** $5,000
**Expected value:** **$5/month**

## Performance Differentiation

**vs. Google Maps/Waze:**
- They provide real-time traffic ✓
- They predict no optimal departure time ✗
- They learn nothing from your patterns ✗
- They send no alerts for delays on their own ✗

**Differentiation level:** Medium (20% premium)

**Premium value:** $283/month

## Pricing Strategy

**Value-based pricing (20-30% of EVC):**

| Price Point | Monthly | Annual | Value Capture | Customer ROI |
|-------------|---------|--------|---------------|--------------|
| Low | $340 | $4,075 | 20% | 5.0x |
| Target | $425 | $5,100 | 25% | 4.0x |
| High | $510 | $6,113 | 30% | 3.3x |

**Recommendation:** Target $425/month
- Strong ROI for customers (4x)
- Captures fair share of value (25%)
- Competitive vs alternatives ($10-50/month for nav apps)

## Segment-Specific EVC

| Segment | Monthly EVC | Optimal Price | Population |
|---------|-------------|---------------|------------|
| Business Travelers | $3,200 | $640-$960 | 15% |
| Regular Commuters | $1,698 | $340-$510 | 60% |
| Occasional Users | $380 | $76-$114 | 25% |

**Tiered pricing opportunity:** Different prices for different value received.

---

**Next Phase:** Multi-Dimensional Segmentation (Phase 8)
```

---

## Tips for Success in Phase 7

### 1. Be Conservative with Estimates

**Better to underestimate than overestimate.**

If uncertain, use lower bound:
- Time saved: Use conservative estimate
- Error rate: Don't assume 100% reduction
- Hourly rate: Use median, not high-end

### 2. Validate with Customer Interviews

**Ask customers:**
- "How much time do you currently spend on [task]?"
- "What does it cost you when [error] happens?"
- "How much would you pay for a solution that [delivers value]?"

Real customer data > your assumptions.

### 3. Don't Count the Same Value Twice

**Double-counting error:**
- Time savings: 1 hour saved
- Revenue increase: Meeting enabled by that 1 hour

Pick one. Either time OR revenue, not both.

### 4. Include All Four Components

Many people only calculate time savings and miss:
- Error reduction (often the biggest component!)
- Revenue increase
- Risk reduction

### 5. Test Multiple Differentiation Levels
