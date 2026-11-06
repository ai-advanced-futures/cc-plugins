# Opportunity Scores: Get to Destinations on Time

## ODI Opportunity Algorithm

**Formula (Additive):**
```
Opportunity Score = Importance + max(Importance - Satisfaction, 0)
```

**Score Range:** 0-20
- **15-20:** Severely Underserved (acute pain)
- **12-15:** Underserved (significant opportunity)
- **10-12:** Appropriately Served (incremental improvements)
- **<10:** Overserved or Low Importance (don't focus here)

---

## Top 20 Opportunities

Based on survey data from 87 respondents (file 05-survey-data.csv):

| Rank | Need | Need ID | Importance | Satisfaction | Gap | Opp Score | Category |
|------|------|---------|------------|--------------|-----|-----------|----------|
| 1 | Minimize time to estimate departure time | 031 | 9.2 | 3.1 | 6.1 | **15.3** | Severely Underserved |
| 2 | Reduce likelihood of arriving late | 035 | 9.5 | 4.2 | 5.3 | **14.8** | Severely Underserved |
| 3 | Minimize error in travel time estimation | 029 | 9.1 | 3.9 | 5.2 | **14.3** | Severely Underserved |
| 4 | Ensure accuracy of traffic predictions | 033 | 8.9 | 4.0 | 4.9 | **13.8** | Severely Underserved |
| 5 | Minimize time to receive reroute suggestions | 061 | 8.8 | 3.8 | 5.0 | **13.8** | Severely Underserved |
| 6 | Reduce likelihood of unexpected traffic | 055 | 8.7 | 4.1 | 4.6 | **13.3** | Severely Underserved |
| 7 | Minimize delay before traffic alerts | 054 | 8.5 | 4.3 | 4.2 | **12.7** | Underserved |
| 8 | Ensure effectiveness of reroutes | 068 | 8.4 | 4.4 | 4.0 | **12.4** | Underserved |
| 9 | Minimize discrepancy in predicted vs actual time | 069 | 8.3 | 4.5 | 3.8 | **12.1** | Underserved |
| 10 | Reduce likelihood of underestimating travel time | 030 | 8.2 | 4.6 | 3.6 | **11.8** | Appropriately Served |
| 11 | Minimize likelihood of missing turns | 045 | 8.0 | 5.2 | 2.8 | **10.8** | Appropriately Served |
| 12 | Minimize effort to factor in parking time | 034 | 7.9 | 5.3 | 2.6 | **10.5** | Appropriately Served |
| 13 | Minimize time to identify route options | 022 | 7.8 | 5.5 | 2.3 | **10.1** | Appropriately Served |
| 14 | Reduce frequency of lane confusion | 046 | 7.7 | 5.6 | 2.1 | **9.8** | Appropriately Served |
| 15 | Ensure clarity of turn instructions | 048 | 7.6 | 5.8 | 1.8 | **9.4** | Appropriately Served |
| 16 | Minimize time to decide between routes | 038 | 7.4 | 6.0 | 1.4 | **8.8** | Appropriately Served |
| 17 | Reduce likelihood of second-guessing route | 039 | 7.2 | 6.2 | 1.0 | **8.2** | Appropriately Served |
| 18 | Minimize anxiety about route choice | 042 | 7.0 | 6.5 | 0.5 | **7.5** | Appropriately Served |
| 19 | Minimize time to confirm destination details | 005 | 7.2 | 7.0 | 0.2 | **7.4** | Appropriately Served |
| 20 | Reduce likelihood of incorrect destination entry | 002 | 7.1 | 7.2 | -0.1 | **7.1** | Overserved |

---

## Strategic Analysis by Category

### Severely Underserved (Scores 15-20)

**6 needs identified** - These are the "must-have" features for Crisis Avoiders

**Common themes:**
- Time estimation accuracy (needs 029, 031, 033)
- Real-time adaptation (needs 061, 054, 055)
- Late arrival prevention (need 035)

**Strategic implication:**
Product must excel in these 6 areas to justify premium pricing. These are table-stakes for Crisis Avoiders segment.

**Estimated value creation:**
- Combined baseline cost: $1,226/month (from file 04)
- 80% improvement = $981/month value
- Supports $60-75/month pricing (6-8% of value)

---

### Underserved (Scores 12-15)

**3 needs identified** - Important but less acute

**Common themes:**
- Reroute effectiveness
- Arrival time accuracy
- Traffic delay handling

**Strategic implication:**
Secondary features that differentiate from basic free apps. Nice-to-have for Balanced Users, less critical for Crisis Avoiders.

**Estimated value creation:**
- Combined baseline cost: $313/month
- 60% improvement = $188/month value

---

### Appropriately Served (Scores 10-12)

**9 needs identified** - Incremental improvements

**Common themes:**
- Navigation execution (turns, lanes)
- Route planning efficiency
- Interface clarity

**Strategic implication:**
Don't invest heavily here. Free apps (Google Maps, Waze) already serve these needs reasonably well. Feature parity sufficient.

---

### Overserved (Scores <10)

**Low-priority or well-served by existing solutions**

**Strategic implication:**
Ignore for MVP. May become relevant for feature expansion later.

---

## Segment-Specific Opportunity Analysis

### Crisis Avoiders (30%, n=26)

**Top 5 Opportunities:**
1. Minimize time to estimate departure time: **17.2** (Imp 9.8, Sat 2.6)
2. Reduce likelihood of arriving late: **16.9** (Imp 9.9, Sat 3.0)
3. Minimize error in travel time estimation: **16.4** (Imp 9.7, Sat 2.7)
4. Ensure accuracy of traffic predictions: **15.8** (Imp 9.4, Sat 2.8)
5. Minimize time to receive reroute suggestions: **15.6** (Imp 9.3, Sat 2.9)

**Insight:** Crisis Avoiders have much higher importance ratings (+0.6 to +0.9 vs overall) and much lower satisfaction (-0.5 to -1.2 vs overall), creating severely underserved opportunities.

**WTP Prediction:** $80-100/month based on acute pain

---

### Balanced Users (35%, n=30)

**Top 5 Opportunities:**
1. Minimize time to estimate departure time: **14.9** (Imp 8.8, Sat 3.2)
2. Reduce likelihood of arriving late: **14.3** (Imp 9.1, Sat 3.8)
3. Minimize error in travel time estimation: **13.7** (Imp 8.7, Sat 4.0)
4. Ensure accuracy of traffic predictions: **13.2** (Imp 8.5, Sat 3.8)
5. Reduce likelihood of unexpected traffic: **12.8** (Imp 8.4, Sat 3.8)

**Insight:** Balanced Users have moderate pain (not as acute as Crisis Avoiders) but still significant underserved needs.

**WTP Prediction:** $50-65/month based on moderate pain

---

### Satisfied Users (35%, n=31)

**Top 5 Opportunities:**
1. Minimize time to estimate departure time: **10.9** (Imp 5.8, Sat 5.1)
2. Reduce likelihood of arriving late: **10.5** (Imp 5.5, Sat 5.0)
3. Ensure accuracy of traffic predictions: **9.8** (Imp 5.3, Sat 5.5)
4. Minimize error in travel time estimation: **9.7** (Imp 5.2, Sat 5.5)
5. Reduce likelihood of unexpected traffic: **9.5** (Imp 5.1, Sat 5.6)

**Insight:** Satisfied Users have low importance ratings and are already reasonably satisfied with free alternatives.

**WTP Prediction:** $20-30/month (won't pay premium)

---

## Opportunity Landscape Visualization

```
         High Importance (8-10)
                │
    ┌───────────┼───────────┐
    │           │           │
    │  SEVERELY │           │
    │  UNDERSERVED│         │
    │  (Top 6)  │           │
    │  •••••••  │           │
    │           │           │
────┼───────────┼───────────┼──── Satisfaction
Low │           │  •••      │ High
(1-4)│           │(Underserved)│(7-10)
    │           │           │
    │           │           │
    └───────────┼───────────┘
                │
         Low Importance (1-7)
```

**Strategic Sweet Spot:** Upper-left quadrant (High Importance, Low Satisfaction)
- 6 needs in "Severely Underserved" zone
- Target for MVP features

---

## Feature Prioritization Matrix

### Tier 1: Must-Have (MVP Features)
**Needs:** 029, 031, 033, 035, 054, 055, 061
**Why:** Severely underserved, high value creation
**Impact:** Directly addresses Crisis Avoiders' acute pain

**Key Features:**
1. **Smart Departure Time Calculator**
   - Addresses needs 031, 029, 030
   - Accounts for parking, destination delays, personal patterns
   - Learns from historical accuracy

2. **Proactive Traffic Intelligence**
   - Addresses needs 033, 054, 055
   - Predictive alerts before delays occur
   - Real-time accuracy monitoring

3. **Adaptive Route Management**
   - Addresses needs 061, 068
   - Instant reroute suggestions
   - "Time-to-beat" dashboard

---

### Tier 2: Nice-to-Have (V1.1)
**Needs:** 068, 069, 030
**Why:** Underserved but less acute
**Impact:** Differentiates from basic free apps

**Key Features:**
1. **Arrival Confidence Score**
   - "95% confident you'll arrive by 2:05 PM"
   - Historical accuracy tracking

2. **Reroute Effectiveness Validation**
   - "This reroute will save you 8 minutes"
   - Learn which reroutes actually help

---

### Tier 3: Feature Parity (V2.0)
**Needs:** 045, 046, 048, 022, 038, 039
**Why:** Appropriately served by competitors
**Impact:** Table-stakes, not differentiators

**Key Features:**
1. Standard turn-by-turn navigation
2. Lane guidance
3. Voice instructions
4. Route alternatives display

---

## Competitive Opportunity Gap Analysis

### vs Google Maps (Free)
- Google serves needs 11-20 well (Appropriately Served)
- Google underserves needs 1-10 (our opportunity)
- **Gap:** Accuracy, proactive alerts, reliability

### vs Waze (Free)
- Waze serves need 055 (unexpected traffic) reasonably well
- Waze underserves needs 029-033 (time estimation)
- **Gap:** Predictive intelligence, learning

### vs Premium Navigation (e.g., Sygic, TomTom)
- Premium apps focus on offline maps, speed cameras
- Don't address top opportunities (time accuracy)
- **Gap:** AI-powered prediction vs offline features

**Strategic Positioning:**
"Google Maps tells you the route. We guarantee you arrive on time."

---

## ROI Calculation for Customers

**Value Created (Top 6 Needs):**
- Baseline cost: $1,226/month (from file 04)
- 80% improvement: $981/month value delivered
- Annual: $11,772/year

**Pricing:**
- $69/month ($828/year)
- **ROI: 14.2x** ($11,772 / $828)
- Or: Customer keeps $10,944/year in time savings

**Pitch:**
"Save 15+ hours per month and never miss an important meeting again. Worth $12,000/year. Costs $828/year. 14x ROI."

---

## Next Steps

With opportunities scored and prioritized:

1. **EVC Calculation** (File 07) - Quantify total economic value
2. **Segmentation** (File 08) - Validate Crisis Avoiders as primary target
3. **WTP Validation** (File 09) - Confirm $60-75/month pricing
4. **Feature Roadmap** - Build Tier 1 features (needs 029, 031, 033, 035, 054, 055, 061)

See subsequent files for complete analysis.
