# Example 1: Navigation App - "Get to Destinations on Time"

## Overview

This example demonstrates the complete JTBD Market Discovery workflow for a consumer navigation application. It walks through all 10 phases of the methodology, from job identification to final opportunity validation.

**Domain:** Consumer Navigation / Location-Based Services
**Job Performer:** Urban commuter (daily travelers in metropolitan areas)
**Job to Be Done:** Get to destinations on time
**Target Market:** Individual consumers, professionals with time-sensitive schedules

---

## Business Context

### Problem Statement

Urban commuters face consistent challenges arriving on time to destinations due to:
- Traffic unpredictability
- Unfamili with routes
- Inaccurate time estimates
- Last-minute route changes
- Parking availability uncertainty

These challenges result in:
- Missed meetings and appointments
- Increased stress and anxiety
- Wasted time from poor route planning
- Lost opportunities (personal and professional)

### Market Opportunity

The navigation app market is dominated by free solutions (Google Maps, Waze, Apple Maps) that serve basic needs well. However, our discovery process reveals significant underserved needs among commuters who:
- Have high stakes for on-time arrival (professionals, parents, healthcare workers)
- Experience frequent traffic variability
- Value time savings over free alternatives
- Need higher accuracy and reliability

This creates a premium segment opportunity where customers will pay for superior performance.

---

## Workflow Files

This example includes all phases of the discovery process:

### Phase 1-2: Job Definition
- **01-job-statement.md** - Complete job statement with forces diagram
- **02-job-steps.md** - 12 universal job steps across 6 phases

### Phase 3: Need Generation
- **03-customer-needs.md** - 85 outcome-based customer needs

### Phase 4: Time-Task Analysis
- **04-time-task-analysis.md** - Current effort quantification for top 30 needs

### Phase 5: Survey & Data Collection
- **05-survey-data.csv** - 87 realistic survey responses

### Phase 6: Opportunity Scoring
- **06-opportunity-scores.md** - Top 20 opportunities using ODI algorithm

### Phase 7: Economic Value
- **07-evc-calculation.md** - Complete EVC breakdown ($13,752/year)

### Phase 8: Segmentation
- **08-segmentation-analysis.md** - 3 customer segments identified via K-means

### Phase 9: WTP Validation
- **09-wtp-validation.md** - 6-layer validation report (PASS at $60-75/month)

### Phase 10: Output & Integration
- **10-final-output.json** - Complete structured output for downstream integration

---

## Key Findings

### Top 3 Opportunities (Severely Underserved)

1. **Minimize time it takes to estimate departure time**
   - Importance: 9.2/10 | Satisfaction: 3.1/10 | Opportunity: 15.3

2. **Reduce likelihood of arriving late to destinations**
   - Importance: 9.5/10 | Satisfaction: 4.2/10 | Opportunity: 14.8

3. **Minimize effort required to adapt route during trip**
   - Importance: 8.8/10 | Satisfaction: 3.8/10 | Opportunity: 13.8

### Customer Segments

**Segment 1: Crisis Avoiders (30% of market)**
- High-stakes schedules (meetings, appointments, pickups)
- Very high importance ratings (avg 9.1/10)
- Very low satisfaction with current tools (avg 3.2/10)
- Willing to pay $80-100/month for reliability
- **Strategic Priority: PRIMARY TARGET**

**Segment 2: Balanced Users (35% of market)**
- Regular commuters with moderate time sensitivity
- High importance (avg 7.3/10), medium satisfaction (avg 5.8/10)
- Willing to pay $50-65/month for improvements
- **Strategic Priority: SECONDARY TARGET**

**Segment 3: Satisfied Users (35% of market)**
- Casual users, flexible schedules
- Low importance (avg 5.2/10), already satisfied (avg 8.1/10)
- Only willing to pay $20-30/month
- **Strategic Priority: LOW (already served by free alternatives)**

### Economic Value & Pricing

**Economic Value to Customer (EVC):**
- Time savings: $750/month
- Error reduction (late arrivals avoided): $150/month
- Fuel savings: $50/month
- Risk reduction: $5/month
- Performance premium (20%): $191/month
- **Total EVC: $1,146/month ($13,752/year)**

**Optimal Value Capture Range:** 20-30% of EVC = $229-344/month

**Realistic B2C Pricing:** $60-75/month ($720-900/year)
- Represents 21-26% of EVC (within optimal range)
- Validated against competitive benchmarking
- Supported by WTP survey data (median $65/month)
- 3-5x ROI for customers

### Strategic Recommendations

**Product Strategy:**
1. Focus on Crisis Avoiders segment (acute pain, high WTP)
2. Build features addressing top 10 severely underserved needs
3. Emphasize reliability, accuracy, and real-time adaptation
4. Position as premium alternative to free apps

**Pricing Strategy:**
1. Launch at $69/month ($828/year)
2. Target Crisis Avoiders and Balanced Users
3. Offer annual discount ($749/year = 10% off)
4. Freemium model to convert Satisfied Users over time

**Go-to-Market:**
1. Lead with "Never miss an important meeting again"
2. Emphasize time savings ($750/month value)
3. Target professionals, parents, healthcare workers
4. Partner with corporate concierge services

**Next Steps:**
1. Use this data with `/brainstorm` plugin to ideate solutions
2. Create PRD targeting Crisis Avoiders with top 10 needs
3. Design MVP addressing departure time estimation and real-time adaptation
4. Build proof-of-concept with 50 beta users from Crisis Avoiders segment

---

## How to Use This Example

### Learning the Methodology

Read through the files in order (01 through 10) to understand how each phase builds on the previous:
1. Start with job statement to understand the problem
2. Review job steps to see the workflow breakdown
3. Study customer needs generation (ACTION + VARIABLE formula)
4. Examine time-task analysis to quantify current pain
5. Look at survey data structure for your own research
6. Understand opportunity scoring algorithm application
7. Learn EVC calculation methodology
8. See how segmentation reveals distinct customer groups
9. Study WTP validation framework (6 layers)
10. Review final output format for integration

### Applying to Your Product

Use this as a template:
1. Replace navigation job with your target job
2. Follow same 12-step universal framework (adjust as needed)
3. Generate 80-100 needs following ACTION + VARIABLE formula
4. Conduct survey with 50-100 respondents
5. Run scripts in `/scripts` directory for analysis
6. Generate similar reports for your opportunity

### Integration with Other Plugins

The final output (10-final-output.json) integrates with:

**Brainstorm Plugin:**
```
Given this JTBD analysis [attach 10-final-output.json], brainstorm solution concepts
that address the top 3 severely underserved needs for Crisis Avoiders segment.
```

**PRD Plugin:**
```
Create a PRD for a navigation app targeting Crisis Avoiders segment [attach analysis].
Focus on departure time estimation, real-time adaptation, and arrival accuracy.
```

**Design Plugin:**
```
Design the departure time estimation feature [attach need details from analysis]
for Crisis Avoiders who need high reliability for time-sensitive trips.
```

---

## Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| README.md | 200 | Overview and key findings |
| 01-job-statement.md | 120 | Job definition and forces |
| 02-job-steps.md | 280 | 12 universal job steps |
| 03-customer-needs.md | 800 | 85 outcome-based needs |
| 04-time-task-analysis.md | 420 | Current effort quantification |
| 05-survey-data.csv | 88 | 87 survey responses (170 columns) |
| 06-opportunity-scores.md | 340 | Top 20 opportunities ranked |
| 07-evc-calculation.md | 310 | Economic value breakdown |
| 08-segmentation-analysis.md | 450 | 3 customer segments |
| 09-wtp-validation.md | 380 | 6-layer WTP framework |
| 10-final-output.json | 280 | Structured output schema |
| **Total** | **~3,700 lines** | **Complete workflow** |

---

## Data Sources

This example uses synthetic but realistic data based on:
- Urban commuter behavior patterns
- Navigation app usage studies
- Time-use surveys
- Competitive pricing analysis
- SaaS pricing benchmarks

While synthetic, the data demonstrates proper methodology and produces actionable insights.

---

## License

This example is part of the JTBD Market Discovery plugin.
Licensed under MIT License.

**Author:** Luis F. Amadeo (Chief Agentic Officer)
**Date:** January 2026
**Methodology:** Outcome-Driven Innovation (Tony Ulwick)
