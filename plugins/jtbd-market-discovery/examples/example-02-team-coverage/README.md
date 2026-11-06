# Example 2: Team Coverage Tool - "Ensure Adequate Team Coverage"

## Overview

This example demonstrates how the JTBD Market Discovery methodology applies to **B2B SaaS** contexts, with different dynamics than B2C consumer apps (see Example 1: Navigation).

**Domain:** HR Technology / Workforce Management
**Job Performer:** HR Manager, Team Lead, Operations Manager
**Job to Be Done:** Ensure adequate team coverage for critical periods
**Target Market:** B2B (companies with 20-500 employees, distributed teams)

---

## Why This Example Matters

**Key Differences from Navigation Example (B2C):**

| Dimension | Navigation (B2C) | Team Coverage (B2B) |
|-----------|------------------|---------------------|
| **Buyer** | End user (individual) | Manager/company (not end user) |
| **Budget Source** | Personal income | Corporate expense |
| **Decision Process** | Impulse / trial-based | Committee / ROI-driven |
| **Value Metric** | Time saved (personal) | Productivity + risk (organizational) |
| **Pricing Psychology** | Price sensitive (free alternatives) | ROI-focused (prove business case) |
| **Sales Cycle** | Minutes to days | Weeks to months |
| **Churn Drivers** | Personal preference | Contract renewal / budget cuts |
| **WTP Validation** | Stated vs actual WTP gap | Procurement pricing benchmarks |

---

## Business Context

### Problem Statement

HR managers and team leads struggle to ensure adequate coverage during:
- Employee absences (vacation, sick leave, parental leave)
- Peak demand periods (seasonal, project deadlines)
- Critical operational windows (24/7 support, on-call rotations)
- Distributed team coordination (timezones, remote work)

These challenges result in:
- Coverage gaps → SLA violations → revenue loss
- Overtime costs and employee burnout
- Last-minute scrambling and stress
- Compliance violations (labor laws, union rules)
- Manual spreadsheet chaos

### Market Opportunity

Unlike navigation (where free alternatives dominate), team coverage software has:
- **Clear ROI:** Measurable SLA improvement, overtime reduction
- **No perfect free alternative:** Spreadsheets don't scale, error-prone
- **Compliance necessity:** Labor law requirements create must-have need
- **B2B budget:** Corporate expense, not personal
- **Multiple stakeholders:** HR, Ops, Finance all benefit

This creates viable **B2B SaaS opportunity** at $30-80/employee/month.

---

## Key Findings (Summary)

### Job Structure
- **14 job steps** across 6 universal phases (vs 12 for navigation)
- More complex than navigation due to:
  - Multi-stakeholder coordination
  - Compliance constraints
  - Predictive planning (not just reactive routing)

### Customer Needs
- **87 outcome-based needs** (similar scale to navigation)
- Different pain profile:
  - Less about personal anxiety (navigation)
  - More about organizational risk (coverage gaps)

### Top 3 Opportunities

1. **Minimize likelihood of coverage gaps during critical periods**
   - Importance: 9.4/10 | Satisfaction: 3.2/10 | Opportunity: 15.6

2. **Reduce time required to identify potential absence conflicts**
   - Importance: 9.1/10 | Satisfaction: 3.5/10 | Opportunity: 14.7

3. **Minimize effort to ensure compliance with labor regulations**
   - Importance: 8.9/10 | Satisfaction: 3.8/10 | Opportunity: 14.0

### Customer Segments (3 identified via K-means)

**Segment 1: Compliance-Focused (25%, n=22)**
- Regulatory-heavy industries (healthcare, finance)
- High importance on compliance needs (9.5/10)
- Willing to pay $70-90/employee/month
- **PRIMARY TARGET**

**Segment 2: Efficiency-Driven (40%, n=35)**
- Tech companies, professional services
- Balance automation with control
- Willing to pay $50-70/employee/month
- **SECONDARY TARGET**

**Segment 3: Manual Managers (35%, n=30)**
- Small businesses, low-tech industries
- Prefer spreadsheets, change-resistant
- Only willing to pay $20-30/employee/month
- **LOW PRIORITY** (not ready for SaaS)

### Economic Value & Pricing

**EVC Analysis (per employee/month):**
- Time savings: $300/month (20 hours × $15/hour manager time)
- Error reduction (coverage gaps): $450/month (0.5 gaps × $900 SLA penalty)
- Overtime reduction: $200/month (10 hours × $20/hour overtime rate)
- Risk reduction (compliance): $50/month (audit risk reduction)
- Performance premium (20%): $200/month
- **Total EVC: $1,200/month per employee**

**WTP Validation:**
- **Compliance-Focused:** $70-90/employee/month (5.8-7.5% of EVC) ✅
- **Efficiency-Driven:** $50-70/employee/month (4.2-5.8% of EVC) ✅
- **Manual Managers:** $20-30/employee/month (1.7-2.5% of EVC) ⚠️

**Critical Difference from Navigation:**
- B2B pricing validation PASSES (corporate ROI justifies price)
- B2C pricing validation FAILED (personal budget + free alternatives)

**Validated Pricing Strategy:**
- **Professional Tier:** $60/employee/month (target: Efficiency-Driven)
- **Enterprise Tier:** $80/employee/month (target: Compliance-Focused)
- Minimum: 20 employees ($1,200-1,600/month contract)
- Annual contracts (reduce churn)

---

## Why B2B Pricing Works (vs B2C Failure)

### Factor 1: Different Buyer

**B2C (Navigation):**
- Individual pays from personal budget
- Compares to free alternatives
- "I can just leave earlier" (free substitute)
- Emotional purchase decision

**B2B (Team Coverage):**
- Company pays from productivity budget
- Compares to current solution (spreadsheets + manual work)
- "Coverage gaps cost us $900 each" (measurable cost)
- ROI-driven purchase decision

### Factor 2: Procurement Dynamics

**B2C:**
- Price sensitivity: High
- "Why pay when Google Maps is free?"
- Needs 10-20x better to justify premium

**B2B:**
- ROI focus: "Does it save more than it costs?"
- $60/employee saves $300/employee in time + $450 in errors = $750 savings
- 12x ROI justifies price easily

### Factor 3: Value Attribution

**B2C:**
- Hard to prove: "Would I have arrived on time anyway with Google Maps?"
- Attribution problem kills perceived value

**B2B:**
- Easy to measure: Coverage gap rate before/after
- Dashboard shows: "17 gaps avoided this month = $15,300 saved"
- Clear attribution to tool

### Factor 4: Switching Costs

**B2C:**
- Low switching cost from free app
- High switching cost TO paid app ($69/month ongoing)

**B2B:**
- High switching cost from spreadsheets (implementation)
- But one-time cost, then continuous benefit
- Plus: implementation included in annual contract

---

## Structure Reference

**Full workflow files available in Example 1 (Navigation).**

To apply this example to your B2B product:

1. **Job Statement** (like navigation/01-job-statement.md)
   - Define B2B job performer (manager, not end user)
   - Forces diagram emphasizes organizational pain
   - Circumstances include compliance, coordination, multi-stakeholder

2. **Job Steps** (like navigation/02-job-steps.md)
   - Typically 12-15 steps for B2B (more complex)
   - UNDERSTAND → PLAN → EXECUTE → ASSESS → REVISE
   - Include stakeholder coordination steps

3. **Customer Needs** (like navigation/03-customer-needs.md)
   - 80-100 needs following ACTION + VARIABLE formula
   - Organizational outcomes (not personal anxiety)
   - Compliance and risk reduction needs common

4. **Time-Task Analysis** (like navigation/04-time-task-analysis.md)
   - Quantify manager/admin time (not end-user time)
   - Include error costs (SLA violations, compliance fines)
   - Calculate ROI per employee/month

5. **Survey Data** (like navigation/05-survey-data.csv)
   - Survey HR managers (buyers), not employees (end users)
   - 50-100 respondents from target companies
   - Include company size, industry, compliance requirements

6. **Opportunity Scoring** (like navigation/06-opportunity-scores.md)
   - ODI algorithm same as B2C
   - Interpretation different (organizational impact)

7. **EVC Calculation** (like navigation/07-evc-calculation.md)
   - Calculate per-employee value
   - Include organizational benefits (productivity, risk, compliance)
   - Performance premium: 15-25% (B2B SaaS typical)

8. **Segmentation** (like navigation/08-segmentation-analysis.md)
   - Segment by industry, company size, compliance needs
   - Different WTP by segment (Compliance > Efficiency > Manual)

9. **WTP Validation** (like navigation/09-wtp-validation.md)
   - Survey pricing benchmarks: $30-100/employee/month for HR tech
   - Test against ROI (does price < value created?)
   - Procurement process validation (can it pass budget approval?)

10. **Final Output** (like navigation/10-final-output.json)
    - B2B-specific fields: contract_value, seats, annual_terms
    - Integration with CRM, HRIS systems

---

## B2B WTP Validation (6-Layer Framework)

### Layer 1: Statistical Outlier Detection
- Survey pricing range: $30-120/employee/month
- Median: $65/employee/month
- Remove outliers (startups saying $200+, skeptics saying $5)
- Clean median: $60/employee/month ✅

### Layer 2: Competitive Benchmarking
- Workforce management tools: $50-150/employee/month
- HR software: $20-80/employee/month
- Our positioning: $60-80/employee/month (mid-market)
- Competitive: ✅ PASS

### Layer 3: Value Economics Check
- EVC: $1,200/employee/month
- WTP: $60-80/employee/month
- Value capture: 5-6.7% of EVC
- **Under-capturing but strategically acceptable** ✅

Why under-capturing is OK for B2B:
- Land-and-expand model (start low, add modules)
- Competitive pricing (need to win deals)
- Volume play (need 1,000+ customers)

### Layer 4: Confidence Scoring
- Sample: 87 HR managers from target companies
- Response consistency: High (B2B buyers more rational)
- Company size alignment: 20-500 employees
- Confidence: ⭐⭐⭐ HIGH ✅

### Layer 5: Segment-Specific Benchmarks
- Compliance-Focused: $70-90 (aligns with enterprise HR tech)
- Efficiency-Driven: $50-70 (aligns with mid-market SaaS)
- Manual Managers: $20-30 (too low to target)
- Segment WTP validated ✅

### Layer 6: Procurement Process Test
**Critical B2B question:** "Will this pass budget approval?"

Test with 10 target customers:
- Present pricing: $60/employee/month ($14,400/year for 20 employees)
- Ask: "Would this pass your budget approval process?"
- Result: 7/10 said yes with proof of ROI
- ✅ PASS procurement test

**Overall B2B Validation:** ✅✅✅ **PASSED** (6/6 layers)

**Key Difference from B2C Navigation:**
- B2B validation PASSES because ROI is clear and measurable
- B2C validation FAILED because free alternatives + perception gap

---

## Go-to-Market Strategy

### Phase 1: Target Compliance-Focused (25% of market)

**Why start here:**
- Highest pain (regulatory requirements)
- Highest WTP ($70-90/employee/month)
- Easiest to prove ROI (compliance = measurable)
- Sticky once implemented (switching cost high)

**Channels:**
- Industry conferences (SHRM, HR Tech)
- Compliance officer networks
- Healthcare/finance trade publications
- LinkedIn targeting (HR + compliance keywords)

**Sales Process:**
- Inbound leads → Demo → Pilot (30 days)
- Pilot proves coverage gap reduction
- Convert to annual contract
- Expand to adjacent teams

### Phase 2: Expand to Efficiency-Driven (40% of market)

**After proving ROI with 20+ Compliance-Focused customers:**
- Use case studies and testimonials
- Lower price point ($50-60/employee/month)
- Self-service onboarding
- Shorter sales cycle

### Phase 3: Ignore Manual Managers (35% of market)

**Don't target initially:**
- Too low WTP ($20-30/employee/month)
- Change-resistant (prefer spreadsheets)
- High churn risk
- Let them discover via word-of-mouth later

---

## Key Lessons: B2B vs B2C

### What Changed:
- ✅ **Buyer** (company vs individual)
- ✅ **Budget** (corporate vs personal)
- ✅ **Value metric** (organizational ROI vs personal time)
- ✅ **Competitive landscape** (no perfect free alternative)

### What Stayed the Same:
- ✅ **JTBD methodology** (same 10 phases)
- ✅ **ODI algorithm** (same opportunity scoring)
- ✅ **Segmentation approach** (K-means clustering)
- ✅ **WTP validation** (6-layer framework)

### Critical Insight:

**The JTBD methodology is domain-agnostic.**

- Revealed navigation needs B2B2C model (not B2C)
- Revealed team coverage works as B2B SaaS
- Methodology correctly identifies viable business models

---

## Integration with Other Examples

### Use Navigation Example (01) For:
- Complete workflow structure (all 11 files)
- Socratic dialogue examples
- B2C / freemium pricing dynamics
- Consumer psychology and free alternatives

### Use Team Coverage Example (02) For:
- B2B SaaS pricing validation
- Organizational value metrics
- Multi-stakeholder needs
- ROI-driven purchase decisions
- Compliance and risk factors

### Apply Both To:
- Your specific job/domain
- Adjust for B2C vs B2B context
- Follow same 10-phase methodology
- Adapt pricing validation for your market

---

## Files to Create (If Doing Full Team Coverage Workflow)

If you want to create complete team coverage example following navigation structure:

1. **01-job-statement.md** - Define "Ensure adequate team coverage" job
2. **02-job-steps.md** - 14 steps (UNDERSTAND coverage needs → REVISE staffing plans)
3. **03-customer-needs.md** - 87 needs (organizational outcomes)
4. **04-time-task-analysis.md** - Manager time + gap costs
5. **05-survey-data.csv** - 87 HR managers surveyed
6. **06-opportunity-scores.md** - Top 20 opportunities
7. **07-evc-calculation.md** - $1,200/employee/month value
8. **08-segmentation-analysis.md** - 3 segments (Compliance/Efficiency/Manual)
9. **09-wtp-validation.md** - $60-80/employee validated
10. **10-final-output.json** - B2B-specific schema

**Estimated effort:** ~2,500 lines, 2-3 hours

**Recommendation:** Use navigation example structure as template, adapt for B2B context.

---

## License

This example is part of the JTBD Market Discovery plugin.
Licensed under MIT License.

**Author:** Luis F. Amadeo (Chief Agentic Officer)
**Date:** January 2026
**Methodology:** Outcome-Driven Innovation (Tony Ulwick)
