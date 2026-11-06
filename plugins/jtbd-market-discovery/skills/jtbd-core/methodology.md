# JTBD Core Methodology

**Framework:** Outcome-Driven Innovation (ODI) - Tony Ulwick
**Version:** 1.0.0
**Last Updated:** 2026-01-21

---

## Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
JTBD Market Discovery - Analysis Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Job: "Get to destinations on time"
Survey: 78 responses, 85 customer needs analyzed

TOP 5 OPPORTUNITIES:

1. Minimize time to identify traffic delays
   Importance: 9.2 | Satisfaction: 3.1 | Opportunity: 15.3
   EVC: $450/customer/year
   Segment: Daily Commuters (n=35)
   Forces: PUSH (8/10), PULL (9/10), Switch Likelihood: +11

2. Determine alternative routes during congestion
   Importance: 8.8 | Satisfaction: 3.5 | Opportunity: 14.1
   EVC: $380/customer/year
   Segment: Daily Commuters (n=35)
   Forces: PUSH (8/10), PULL (9/10), Switch Likelihood: +10

3. Reduce uncertainty about arrival time
   Importance: 9.0 | Satisfaction: 4.2 | Opportunity: 12.8
   EVC: $320/customer/year
   Segment: Business Travelers (n=23)
   Forces: PUSH (7/10), PULL (8/10), Switch Likelihood: +8

4. Minimize fuel consumption during travel
   Importance: 7.5 | Satisfaction: 5.1 | Opportunity: 9.9
   EVC: $280/customer/year
   Segment: Cost-Conscious (n=20)
   Forces: PUSH (6/10), PULL (7/10), Switch Likelihood: +5

5. Determine parking availability at destination
   Importance: 8.2 | Satisfaction: 4.5 | Opportunity: 11.9
   EVC: $200/customer/year
   Segment: Urban Drivers (n=28)
   Forces: PUSH (7/10), PULL (6/10), Switch Likelihood: +4

SEGMENTS:

- Daily Commuters (45%): High need for real-time traffic
- Business Travelers (29%): High need for arrival certainty
- Cost-Conscious (26%): High need for efficiency optimization

PRICING:

- Daily Commuters: $15-25/month (WTP validated, 90% confidence)
- Business Travelers: $30-50/month (WTP validated, 85% confidence)
- Cost-Conscious: $10-15/month (WTP validated, 80% confidence)

RECOMMENDATION:

Target Daily Commuters first with real-time traffic solution.
Opportunity #1 has highest score (15.3), highest EVC ($450/year),
and strongest switching forces (+11). Price at $20/month.

Next steps:
1. Create PRD focusing on top 5 opportunities
2. Design UX for real-time traffic detection
3. Validate MVP with 10 target customers
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## What This Skill Does

The JTBD Market Discovery skill guides you through a comprehensive, data-driven process for discovering and validating market opportunities using **Jobs To Be Done (JTBD)** theory and **Outcome-Driven Innovation (ODI)** methodology.

**Core Capabilities:**

1. **Identify Jobs To Be Done**
   - Discover stable, outcome-focused jobs customers need to accomplish
   - Validate job statements with customers
   - Keep the thinking on outcomes, not on solutions or products

2. **Decompose Jobs Into Steps**
   - Break jobs into 8-15 steps using Universal Job Steps framework
   - Cover all 6 phases: UNDERSTAND → PLAN → EXECUTE → ASSESS → REVISE → CONCLUDE
   - Prepare the steps for need generation (80-100 needs)

3. **Generate Customer Needs**
   - Create 80-100 customer needs using ACTION + VARIABLE formula
   - Ensure outcome-focused, measurable, stable needs
   - Systematic coverage of entire job lifecycle

4. **Survey Customers**
   - Collect importance and satisfaction ratings (1-10 scale)
   - Survey 50+ customers who actually have the job
   - Ensure statistical significance and data quality

5. **Calculate Opportunity Scores**
   - Formula: `Importance + max(Importance - Satisfaction, 0)`
   - Identify underserved needs (high importance, low satisfaction)
   - Score range: 0-20 (15-20 = extremely high opportunity)

6. **Calculate Economic Value**
   - Quantify dollar value of serving needs better
   - Four value dimensions: Time, Errors, Revenue, Risk
   - Economic Value to Customer (EVC) framework

7. **Analyze Switching Forces**
   - Christensen's Four Forces: Push, Pull, Anxiety, Habit
   - Calculate switch likelihood by segment
   - Identify barriers to adoption

8. **Segment Customers**
   - Multi-dimensional segmentation (needs + circumstances + behavioral)
   - K-means clustering using scikit-learn
   - Find real segments with distinct opportunity profiles

9. **Validate Willingness-to-Pay**
   - 6-layer validation framework
   - Statistical outliers, comparative benchmarking, Van Westendorp
   - Value economics, confidence scoring, segment-specific

10. **Prioritize Innovations**
    - Integrate opportunity scores, EVC, forces, and WTP
    - Identify highest-value targets with strong market pull
    - Data-driven innovation roadmap

---

## Why This Matters

**Traditional product development fails because:**
- ❌ Focuses on solutions/features, not customer jobs
- ❌ Asks "what features should we build?" instead of "what jobs are underserved?"
- ❌ Relies on opinions and intuition, not data
- ❌ Segments by demographics, not needs
- ❌ Guesses at pricing instead of validating willingness-to-pay

**JTBD + ODI succeeds because:**
- ✅ Focuses on stable jobs that stay the same when technology changes
- ✅ Uses systematic framework to generate comprehensive needs (80-100)
- ✅ Collects quantitative data from 50+ customers
- ✅ Calculates opportunity scores to reveal underserved needs
- ✅ Validates economic value and willingness-to-pay
- ✅ Segments customers by needs, not demographics
- ✅ Integrates multiple methodologies for robust validation

**Real Results:**
- Bosch Power Tools: Identified 14 high-opportunity needs, launched #1 circular saw
- Cordis: Found unmet needs in angioplasty, created new product category
- Arm & Hammer: Discovered 12 underserved odor-elimination needs, expanded toothpaste line

---

## Methodology Stack

This skill integrates a comprehensive methodology stack:

### 1. Outcome-Driven Innovation (ODI) - Tony Ulwick

**Core Framework:**
- Universal Job Steps (6 phases)
- ACTION + VARIABLE formula for needs
- Opportunity scoring: `Importance + max(Importance - Satisfaction, 0)`
- 80-100 customer needs per job

**Output:**
- Ranked list of underserved needs (opportunity scores 15-20)
- Segment-specific opportunity profiles
- Innovation priorities based on data

### 2. Economic Value to Customer (EVC)

**Value Dimensions:**
- **Time:** Hours saved × hourly rate
- **Errors:** Errors reduced × cost per error
- **Revenue:** Additional revenue enabled
- **Risk:** Risk reduction × impact of adverse event

**Output:**
- Dollar value per customer per need
- ROI calculations for product investments
- Value-based pricing foundation

### 3. Christensen's Forces

**Four Forces of Progress:**
- **PUSH:** Problems with current solution (motivates search)
- **PULL:** Attraction to new solution (motivates switch)
- **ANXIETY:** Concerns about new solution (resists switch)
- **HABIT:** Comfort with current solution (resists switch)

**Formula:**
```
Switch Likelihood = (PUSH + PULL) - (ANXIETY + HABIT)
```

**Output:**
- Switch likelihood scores by segment
- Identification of switching barriers
- Force-based messaging strategy

### 4. Multi-Dimensional Segmentation

**Three Dimensions:**
- **Needs-based:** Cluster by importance/satisfaction ratings
- **Circumstances-based:** When/where/why job is done differently
- **Behavioral:** Observable patterns (tools used, spending, frequency)

**Algorithm:**
- K-means clustering (scikit-learn)
- Elbow method for optimal cluster count
- Segment validation (observable, actionable, substantial)

**Output:**
- 3-5 customer segments with distinct opportunity profiles
- Segment sizing and targeting recommendations
- Segment-specific innovation strategies

### 5. Willingness-to-Pay (WTP) Validation

**6-Layer Framework:**

1. **Statistical Outliers:** Remove impossible/unrealistic price points
2. **Comparative Benchmarking:** Compare to similar products/services
3. **Van Westendorp:** Psychological pricing boundaries (too cheap/expensive)
4. **Value Economics:** EVC-based price ceiling
5. **Confidence Scoring:** Weight by respondent certainty
6. **Segment-Specific:** Validate separately for each segment

**Output:**
- Validated price ranges with confidence intervals
- Optimal price point recommendations
- Segment-specific pricing strategies

---

## Integration with Other Skills

This skill is designed to work with downstream product development skills:

### Brainstorming → JTBD Discovery → PRD → Design → Execution

**Workflow:**

1. **brainstorm skill:** Refine rough product ideas
   - Output: Validated product concept with problem/solution

2. **jtbd-market-discovery skill:** (THIS SKILL)
   - Input: Product concept
   - Output: Underserved needs, validated opportunities, target segments

3. **prd skill:** Create Product Requirements Document
   - Input: Underserved needs from JTBD
   - Output: Detailed PRD with features mapped to needs

4. **design skill:** Design solution architecture
   - Input: PRD with need-feature mapping
   - Output: Technical architecture, UX flows

5. **execution planning skills:** Create implementation plan
   - Input: Design specifications
   - Output: Phase-by-phase development plan

**Structured Data Handoff:**

This skill outputs structured JSON that downstream skills can consume:

```json
{
  "job_statement": "Get to destinations on time",
  "top_opportunities": [
    {
      "need": "Minimize time to identify traffic delays",
      "importance": 9.2,
      "satisfaction": 3.1,
      "opportunity": 15.3,
      "evc": 450.00,
      "segment": "Daily Commuters"
    },
    // ... more opportunities
  ],
  "segments": [
    {
      "name": "Daily Commuters",
      "size": 45,
      "top_needs": ["Minimize time to identify traffic delays", ...],
      "wtp_range": [15, 25]
    },
    // ... more segments
  ]
}
```

**Chaining:**

The skill will ask before auto-chaining to other skills:

```
Claude: I've identified 12 high-opportunity needs for [JOB].

        Would you like me to:
        1. Continue with detailed analysis (EVC, Forces, WTP)
        2. Chain to PRD skill to create requirements
        3. Export results for manual review

        What would you prefer?
```

---

## What You'll Get

### Deliverables

By the end of this process, you'll have:

1. **Job Statement**
   - Validated, outcome-focused job definition
   - Job-market sizing (frequency, importance)

2. **Job Steps Map**
   - 8-15 steps across 6 universal phases
   - Visual job map for communication

3. **Customer Needs List**
   - 80-100 needs generated from job steps
   - Organized by ACTION + VARIABLE formula

4. **Survey Results**
   - 50+ responses with importance/satisfaction ratings
   - Cleaned dataset (outliers removed, quality checked)

5. **Opportunity Scores**
   - Ranked list of underserved needs (15-20 = extremely high)
   - Segment-specific opportunity profiles
   - Top 10-15 innovation targets

6. **Economic Value Analysis**
   - Dollar value per customer per need
   - Four dimensions: Time, Errors, Revenue, Risk
   - ROI projections for product investments

7. **Forces Analysis**
   - PUSH/PULL/ANXIETY/HABIT by segment
   - Switch likelihood calculations
   - Barriers to adoption identified

8. **Customer Segments**
   - 3-5 segments with distinct needs profiles
   - Segment sizes and characteristics
   - Targeting recommendations

9. **Willingness-to-Pay**
   - Validated price ranges per segment
   - Optimal price point recommendations
   - Confidence intervals

10. **Innovation Roadmap**
    - Prioritized list of product/feature opportunities
    - Mapped to segments and economic value
    - Ready for PRD or design phase

## How It Works

### Phase-by-Phase Breakdown

This skill guides you through 7 phases using **Socratic dialogue**. I'll ask questions, you'll provide answers, and together we'll build a comprehensive market discovery analysis.

**Phase 1: Job Identification (30-45 minutes)**
- Identify the market/product area
- Define the main job customers are trying to accomplish
- Validate job statement with customers (if available)
- Output: Validated job statement

**Phase 2: Job Decomposition (45-60 minutes)**
- Break job into steps using Universal Job Steps framework
- Cover all 6 phases: UNDERSTAND → PLAN → EXECUTE → ASSESS → REVISE → CONCLUDE
- Validate sequence with customers
- Output: 8-15 job steps

**Phase 3: Need Generation (60-90 minutes)**
- For each job step, identify VARIABLES
- Combine with ACTIONS to create customer needs
- Target: 80-100 needs total (5-10 per step)
- Output: List of 80-100 needs

**Phase 4: Survey Design (30-45 minutes)**
- Structure needs into survey format
- Add screening and demographic questions
- Set up importance and satisfaction scales
- Output: Ready-to-field survey

**Phase 5: Data Collection (1-2 weeks)**
- Field survey to 50+ customers
- Monitor response rates and data quality
- Clean data (remove straight-liners, speeders)
- Output: Clean dataset ready for analysis

**Phase 6: Opportunity Analysis (2-3 hours)**
- Calculate opportunity scores (ODI)
- Run segmentation analysis (k-means)
- Analyze switching forces (Christensen)
- Calculate economic value (EVC)
- Output: Integrated opportunity analysis

**Phase 7: Validation & Prioritization (1-2 hours)**
- Validate willingness-to-pay (6 layers)
- Integrate all data sources
- Prioritize innovation targets
- Create recommendations
- Output: Innovation roadmap

---

## Learning Approach

This skill uses **learning by doing** with **inline examples**:

### Socratic Dialogue

I'll ask questions to guide your thinking:

```
Claude: Let's identify the main job. Think about what outcome
        your customers are trying to achieve, not the solution
        they use.

        For example:
        - BAD: "Use a navigation app" (solution-focused)
        - GOOD: "Get to destinations on time" (outcome-focused)

        What job are your customers trying to accomplish?

You: Help their team stay productive when people are out

Claude: Good start! Let's make it more outcome-focused.
        Is the goal to:
        1. Ensure critical work continues despite absences
        2. Minimize workload for remaining team members
        3. Maintain project timelines when people are out

        Which outcome matters most?
```

### Examples Throughout

Every concept includes real examples:

```
Claude: Now let's generate customer needs for Step 3: "Plan the stops"

        Formula: CUSTOMER NEED = ACTION + VARIABLE

        Examples:
        - "Minimize" (ACTION) + "time required for stops" (VARIABLE)
          → "Minimize time required for stops"

        - "Determine" (ACTION) + "parking availability" (VARIABLE)
          → "Determine parking availability at stops"

        What VARIABLES are involved in planning stops?
```

### Validation Checkpoints

At each phase, I'll validate your work:

```
Claude: Let me check your job steps against the quality criteria:

        ✅ Specific (not vague)
        ✅ Actionable (can be done)
        ✅ Sequential (logical order)
        ⚠️  Solution-agnostic (Step 5 mentions "GPS" - let's revise)
        ✅ Consistent granularity

        Let's revise Step 5 to be solution-agnostic...
```

---

## Educational Content

Throughout the process, I'll provide:

1. **Framework Explanations**
   - Why we use Universal Job Steps
   - How ACTION + VARIABLE formula works
   - Why opportunity scoring reveals underserved needs

2. **Real-World Examples**
   - Navigation job decomposition
   - Team coverage need generation
   - Project visibility opportunity analysis

3. **Common Pitfalls**
   - Solution-focused vs outcome-focused
   - Vague vs specific job steps
   - Feature-focused vs need-focused

4. **Best Practices**
   - Survey design principles
   - Data quality checks
   - Segmentation validation

5. **Method Integration**
   - How ODI + EVC work together
   - When to use Forces vs Opportunity Scores
   - How to combine quantitative + qualitative

---

## Privacy & Data Handling

### Data You Provide

This skill may process:
- Job statements and descriptions
- Customer need lists
- Survey responses (importance/satisfaction ratings)
- Demographic data for segmentation
- Pricing and willingness-to-pay data

### How Data Is Used

**During session:**
- Analyzed to calculate opportunity scores
- Used for segmentation clustering
- Integrated across methodologies (ODI, EVC, Forces)
- Generated into structured output (JSON, CSV)

**After session:**
- Not stored permanently by this skill
- Not shared with third parties
- Not used to train models (standard Claude policy)

### Data Privacy Best Practices

**Anonymization:**
- Use aggregate data only (no individual respondent identification)
- Remove personally identifiable information (PII) before analysis
- Use respondent IDs instead of names

**Confidentiality:**
- Don't include proprietary product details in examples
- Genericize company-specific information
- Use pseudonyms for competitive intelligence

**Compliance:**
- Follow GDPR, CCPA, and other data protection regulations
- Obtain informed consent from survey respondents
- Provide opt-out mechanisms

---

## References & Resources

### Academic Sources

1. **Tony Ulwick** - "Jobs to be Done: Theory to Practice"
   - Foundational ODI methodology
   - Universal Job Steps framework
   - Opportunity algorithm

2. **Clayton Christensen** - "Competing Against Luck"
   - Jobs To Be Done theory
   - Four Forces of Progress
   - Hiring/firing framework

3. **Anthony Ulwick** - "What Customers Want"
   - Comprehensive ODI guide
   - Case studies (Bosch, Cordis)
   - Survey methodology

### Methodological Resources

- **Strategyn.com** - ODI consulting firm, case studies
- **JTBD.info** - Jim Kalbach's JTBD resources
- **ReWired Group** - Bob Moesta's JTBD frameworks

### This Plugin

- **references/odi-methodology.md** - Complete ODI framework documentation
- **references/universal-job-steps.md** - 6 phases with examples
- **references/need-generation-guide.md** - ACTION verb library
- **templates/job-statement-template.md** - Guided job discovery
- **templates/job-steps-worksheet.md** - Step decomposition
- **templates/forces-diagram-template.md** - Switching forces analysis
- **templates/survey-instructions.md** - Survey design guide

---

**Author:** Luis F. Amadeo (Chief Agentic Officer)
**License:** MIT
**Framework:** Outcome-Driven Innovation (ODI) - Tony Ulwick
**For:** JTBD Market Discovery Plugin v1.0
