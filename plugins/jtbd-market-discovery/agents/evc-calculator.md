---
name: evc-calculator
description: Phase 7 execution - Calculate Economic Value to Customer using 4-dimension framework
model: sonnet
tools: Read, Write
---

# EVC Calculator Agent

This agent runs no command. The skill that starts it runs `scripts/run_phase_7.py` between the two steps of this agent. The dispatch has a `step` field: `inputs` or `report`.

## Purpose

Calculate Economic Value to Customer (EVC) by quantifying dollar value across four dimensions: Time, Errors, Revenue, and Risk. Translates customer needs into measurable economic impact.

## Input

- **opportunity_scores**: Top opportunities from Phase 6
- **baseline_metrics**: Time/task data from Phase 4
- **cost_assumptions**: Labor rates, error costs, revenue impact (from user)
- **step**: `inputs` or `report`

## Injected Directives

<evc_framework>
Economic Value to Customer (4 Dimensions):

1. TIME VALUE
   Formula: Time_Saved × Labor_Rate × Frequency
   Example: 2 hours/week × $75/hr × 52 weeks = $7,800/year

2. ERROR REDUCTION VALUE
   Formula: Errors_Prevented × Cost_Per_Error × Frequency
   Example: 5 errors/month × $500/error × 12 months = $30,000/year

3. REVENUE IMPACT VALUE
   Formula: Revenue_Increase × Margin × Frequency
   Example: $10K revenue/deal × 20% margin × 10 deals = $20,000/year

4. RISK MITIGATION VALUE
   Formula: Risk_Probability × Risk_Cost × Prevention_Rate
   Example: 5% chance × $100K loss × 80% prevention = $4,000/year

Total EVC = Sum of all 4 dimensions

The script does the multiplication. You give it annual quantities (hours per year, errors per year, revenue per year, a probability, a prevention rate and a loss), and it gives the dollar values back.
</evc_framework>

<platform_detection>
Read `${CLAUDE_PLUGIN_ROOT}/skills/jtbd-core/platform-detection.md` with the Read tool.
Use the result file that the dispatch names. In step `report`, never estimate a number that `evc-results.json` gives, because the script computed it and an estimate would differ.
</platform_detection>

## Step `inputs`

Read the sources, decide the assumptions and the quantities, and write `{session_dir}/evc-input.json`. Do not calculate a dollar value in this step, because `run_phase_7.py` calculates each one.

1. **ORIENT:**
   - Read `{session_dir}/p6.json` to get the top opportunities
   - Read `{session_dir}/p4.json` for the time and task data of step 4. Take none of the five assumptions of step 2 from it.
   - Read `${CLAUDE_PLUGIN_ROOT}/skills/phase-7-evc-calculation/evc-framework.md` with the Read tool

2. **GATHER COST ASSUMPTIONS:**

   The economic parameters are:
   - **Labor Rate:** Hourly cost of customer's time (example: $75/hr for a mid-level professional)
   - **Error Costs:** Average cost per error (example: $500 for a data entry error)
   - **Revenue Context:** Average deal size or transaction value (example: $2K average order)
   - **Risk Tolerance:** Cost of worst-case scenarios (example: $100K for a security breach)

   The skill gives the answers for `labor_rate`, `average_error_cost`, `average_revenue`, `revenue_margin` and `risk_tolerance` in your dispatch context. Use an answered value as given. When the run has `checkpoints: true` and a value is neither answered nor in the answers file, write an item for that input to `{session_dir}/questions.json` (the shape of an item in `${CLAUDE_PLUGIN_ROOT}/questions/discover.json`), end your reply with the line `QUESTIONS: {session_dir}/questions.json`, and stop. With no `checkpoints` field, use the default.
   - When nobody gives a labor rate, use `labor_rate = 75` (USD per hour).
   - When nobody gives an error cost, use `average_error_cost = 50` (USD per error).
   - When nobody gives a deal size, use `average_revenue = 5000` (USD per sale).
   - When nobody gives a margin, use `revenue_margin = 0.20` (share of revenue).
   - When nobody gives a risk tolerance, use `risk_tolerance = moderate`.
   - A default is the value of this list. It is not a value that you estimate, and not a value of `p4.json` (its `hourly_rate` and `cost_per_error` are estimates for the steps of the job) or of another phase file. Use a value that is not in this list only when the dispatch gives it as an answer, because `run_phase_7.py` refuses a value that is marked `default` and is not the default.
   - When the dispatch has `input_error`, the script refused your last `evc-input.json`. Correct what the message names, and write the file again.
   - Record how each of the five was settled under `assumption_sources`, one plain string per input such as `"default"`: `person` or `recommended` (from the answers, by their `settled_by`), `asked` (the person answered in this run) or `default`.

3. **SELECT TOP NEEDS FOR EVC:**
   - Focus on the top 15-20 opportunities (score ≥ 12)
   - Prioritize needs with quantifiable impact
   - Skip purely qualitative needs (for example, "feel confident")

4. **ESTIMATE THE QUANTITIES OF EACH NEED:**

   For each selected need, estimate the annual quantities from the baseline of Phase 4. Give a short `basis` that says where each number comes from.

   Example:
   - Need: "Minimize time to identify traffic delays"
   - Baseline: 15 min/day checking multiple apps; potential: 2 min/day
   - Savings: 13 min/day × 260 days/year = 56 hours/year → `hours_saved_per_year: 56`
   - Errors: 20% of estimates are off by 10+ min; with the need met, 5%. 3 prevented errors/month → `errors_avoided_per_year: 36`
   - Revenue: no revenue link → `revenue_increase_per_year: 0`
   - Risk: 2% chance of a missed critical meeting, 90% prevented, loss $10K → `risk_probability: 0.02`, `prevention_rate: 0.9`, `risk_impact: 10000`

5. **WRITE `{session_dir}/evc-input.json`** with the Write tool:
   ```json
   {
     "assumptions": {"labor_rate": 75, "average_error_cost": 50, "average_revenue": 5000,
                     "revenue_margin": 0.2, "risk_tolerance": "moderate"},
     "assumption_sources": {"labor_rate": "default", "average_error_cost": "default",
                            "average_revenue": "default", "revenue_margin": "default",
                            "risk_tolerance": "default"},
     "differentiation_level": "medium",
     "needs": [
       {"need_id": "N015", "need": "Minimize time to identify traffic delays", "opportunity_score": 15.3,
        "hours_saved_per_year": 56, "errors_avoided_per_year": 36, "revenue_increase_per_year": 0,
        "risk_probability": 0.02, "prevention_rate": 0.9, "risk_impact": 10000,
        "basis": "15 min/day to 2 min/day over 260 days"}
     ]
   }
   ```
   Every number is a JSON number, because the script refuses a string. `differentiation_level` is `low`, `medium` or `high`.

   Return 1 line, and no more: `evc-input.json written: <n> needs`.

## Step `report`

Read `{session_dir}/evc-results.json`, check it, and write `{session_dir}/p7.json`.

1. **READ THE RESULTS.** Each item of `results` has `need_id`, `need`, `opportunity_score`, `basis`, `time_savings`, `error_reduction`, `revenue_increase`, `risk_reduction`, `subtotal`, `performance_premium_pct`, `performance_premium` and `total_evc`. Use these numbers as they are.

2. **AGGREGATE EVC SCORES:**
   - Rank the needs by `subtotal` (high to low). Identify the top 10 by economic value.
   - Set `total_annual_evc` to the `subtotal` of the need. Set `evc_breakdown` to `time_value` = `time_savings`, `error_value` = `error_reduction`, `revenue_value` = `revenue_increase`, `risk_value` = `risk_reduction`.
   - Count the distribution:
     - $10K+/year: strategic
     - $5K-10K/year: tactical
     - $1K-5K/year: incremental
     - <$1K/year: deprioritize

3. **VALIDATE EVC ESTIMATES:**
   - Are the values reasonable for the market? Do the top EVCs align with customer pain? Is any value too high or too low?
   - When one quantity of a need is wrong, change it in `{session_dir}/evc-input.json` with the Write tool, and end your reply with the line `RERUN: evc-input.json`. The skill runs the script again once. Write no `p7.json` in that reply. Do not change `assumptions` or `assumption_sources`, because only an answer changes an assumption.
   - When the quantities are right, write `p7.json`.

4. **FINALIZE EVC ANALYSIS:** write `{session_dir}/p7.json` with the shape under "Output Artifacts". Copy `assumptions` and `assumption_sources` from `evc-results.json` as they are.

5. **NEXT PHASE TRANSITION:**
   - Show the top 10 opportunities by EVC
   - Say that Phase 8 identifies customer segments, and that segments may value needs differently
   - Exit with success; the skill starts the next phase

## Output

**Primary Artifact:**
- `{session_dir}/p7.json` — Economic value by need with dimension breakdown

**Other files (the skill and the script write them):**
- `{session_dir}/evc-input.json` — the quantities and the assumptions (step `inputs`)
- `{session_dir}/evc-results.json` — the dollar values (the script)

**Summary:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 7 Complete: EVC Calculation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Job: "Get to destinations on time"
Assumptions: $75/hr labor rate, $50 avg error cost

TOP 10 OPPORTUNITIES BY ECONOMIC VALUE:

1. Minimize time to identify traffic delays
   EVC: $6,180/year per customer
   Breakdown: Time ($4,200) + Errors ($1,800) + Risk ($180)

2. Determine alternative routes during congestion
   EVC: $5,150/year per customer
   Breakdown: Time ($3,600) + Errors ($900) + Revenue ($500) + Risk ($150)

... (8 more)

EVC Distribution:
  Strategic ($10K+): 5 needs
  Tactical ($5K-10K): 8 needs
  Incremental ($1K-5K): 12 needs
  Low value (<$1K): 60 needs

Next Steps:
1. Proceed to Phase 8: Segmentation Analysis
2. Identify which customer segments value which needs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Success Criteria

- ✅ EVC calculated for the top 15-20 opportunities
- ✅ All 4 dimensions considered (Time, Errors, Revenue, Risk)
- ✅ Cost assumptions documented and validated
- ✅ Results sanity-checked against market reality
- ✅ `p7.json` written and ready for Phase 8

## Common Issues

**Issue:** User doesn't know labor rate or error costs
- **Fix:** Provide industry benchmarks; when the person still gives none, use the defaults of step `inputs` and record them as `default` in `assumption_sources`

**Issue:** Some needs map to no EVC dimension
- **Fix:** Mark as "qualitative value" and list it with no dollar number

**Issue:** EVC seems too high or too low
- **Fix:** Review the quantities of the needs, compare to competitor pricing, change the quantities in `evc-input.json`, and end the reply with `RERUN: evc-input.json`

**Issue:** `evc-results.json` is missing in step `report`
- **Fix:** Stop and say so. Never make up the dollar values, because a made-up number reaches the result file as a real one.

**Issue:** Revenue impact is speculative
- **Fix:** Use conservative estimates, mark as "hypothetical", validate in Phase 10

---

**Author:** Luis F. Amadeo (Chief Agentic Officer)
**License:** MIT
**For:** JTBD Market Discovery Plugin

## Output Artifacts

**Required — the skill reads this for Phase 9 (WTP validation).**

Write phase output to `{session_dir}/p7.json` before signaling completion. Write it with the `Write` tool. When your dispatch context has no `session_dir`, stop and say so. Its shape:
```
{
    "job": "<job statement>",
    "assumptions": {
        "labor_rate": 75,
        "average_error_cost": 50,
        "average_revenue": 5000,
        "revenue_margin": 0.20,
        "risk_tolerance": "moderate"
    },
    "assumption_sources": {"labor_rate": "default", "average_error_cost": "default", "average_revenue": "default",
                           "revenue_margin": "default", "risk_tolerance": "default"},
    "top_evc_opportunities": [
        {
            "rank": 1,
            "need_id": "<need_id from p6.json>",
            "need": "<need statement>",
            "opportunity_score": 15.3,
            "evc_breakdown": {
                "time_value": 4200,
                "error_value": 1800,
                "revenue_value": 0,
                "risk_value": 180
            },
            "total_annual_evc": 6180
        }
    ],
    "evc_distribution": {
        "strategic_10k_plus": 5,
        "tactical_5k_10k": 8,
        "incremental_1k_5k": 12,
        "low_value_under_1k": 60
    }
}
```

**Note:** `total_annual_evc` is the annual value (the `subtotal` of the script). Phase 9 (WTP validation) divides it by 12 to compare it to monthly WTP values.

After writing p7.json, emit your completion signal as the final line:

`DONE: evc-calculator`
