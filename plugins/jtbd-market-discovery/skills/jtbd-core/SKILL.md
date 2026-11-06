---
name: jtbd-core
description: JTBD core methodology reference — ODI framework, universal job steps, opportunity scoring formula, and methodology stack
---

# JTBD Core Methodology

This skill provides the foundational Jobs To Be Done (JTBD) methodology reference used throughout the JTBD Market Discovery plugin.

## Core Frameworks

### Outcome-Driven Innovation (ODI) — Tony Ulwick

**Opportunity Formula:** `Importance + max(Importance - Satisfaction, 0)`
- Score 15-20: Extremely high opportunity (massively underserved)
- Score 12-15: High opportunity
- Score 10-12: Moderate opportunity
- Score < 10: Low opportunity (well-served)

**Universal Job Steps (6 phases):**
1. UNDERSTAND — gather information needed to do the job
2. PLAN — organize resources and sequence actions
3. EXECUTE — carry out the core job steps
4. ASSESS — evaluate progress and outcomes
5. REVISE — adjust plan based on assessment
6. CONCLUDE — complete the job and wrap up

### Customer Need Formula

`CUSTOMER NEED = ACTION + VARIABLE`

**ACTION verbs:** Minimize, Maximize, Reduce, Increase, Determine, Identify, Prevent, Ensure, Optimize, Assess, Calculate

**Examples:**
- "Minimize time to identify traffic delays"
- "Determine parking availability at destination"
- "Avoid likelihood of arriving late to meetings"

### Economic Value to Customer (EVC)

Four value dimensions:
- **Time:** Hours saved × hourly rate
- **Errors:** Errors avoided × cost per error
- **Revenue:** Additional revenue enabled × margin
- **Risk:** Probability reduction × cost of adverse event

### Christensen's Forces

`Switch Likelihood = (PUSH + PULL) - (ANXIETY + HABIT)`

- **PUSH:** Pain with current solution
- **PULL:** Attraction to new solution
- **ANXIETY:** Fear of switching
- **HABIT:** Comfort with status quo

### WTP 6-Layer Validation

1. Statistical outlier detection (IQR method)
2. Comparative benchmarking vs. market
3. Van Westendorp PSM (if 4Q data available)
4. Value economics reality check (EVC-based ceiling)
5. Confidence scoring (sample size, consistency)
6. Segment-specific benchmarks (B2B vs B2C)

## Platform Notes

**Claude Code:** Full Python/scikit-learn analysis, K-means clustering, all 6 WTP layers
**Claude.ai Web:** AI-powered estimation (~80% accuracy), graceful fallbacks

## Usage

This skill is the methodology foundation. Use `/jtbd-market-discovery:discover` to run the full 10-phase workflow.
