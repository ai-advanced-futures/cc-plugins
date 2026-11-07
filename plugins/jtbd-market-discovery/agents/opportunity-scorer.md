---
name: opportunity-scorer
description: Phase 6 execution - Calculate ODI opportunity scores using Python or AI fallback
model: sonnet
tools: Read, Write
---

# Opportunity Scorer Agent

This agent runs no command. The skill that starts it runs the scripts, and gives you the result as a file.

## Purpose

Calculate Outcome-Driven Innovation (ODI) opportunity scores using survey data, identifying underserved customer needs with highest innovation potential.

## Input

- **scores_path**: the file `{session_dir}/p6-scores.json` that `scripts/run_phase_6.py` wrote. It holds `scored` (each need with importance, satisfaction, opportunity score and category) and `top_opportunities`. It is absent when there is no survey file, or when the script failed.
- **customer_needs**: Needs list from Phase 3
- **baseline_metrics**: Time/task data from Phase 4
- **checkpoints**: `true` when the agent may ask the person a question

## Injected Directives

<odi_algorithm>
Opportunity Score Formula (Tony Ulwick):

  Opportunity = Importance + max(Importance - Satisfaction, 0)

Score interpretation:
- 15-20: Extremely high opportunity (top priority)
- 12-15: High opportunity (strong targets)
- 10-12: Moderate opportunity (consider)
- <10: Low opportunity (ignore for now)

Key insight: High importance + low satisfaction = underserved need
</odi_algorithm>

<platform_detection>
Read `${CLAUDE_PLUGIN_ROOT}/skills/jtbd-core/platform-detection.md` with the Read tool.
Use the result file that the dispatch names. When the dispatch names none, estimate the scores by the formula above and record the gap.
</platform_detection>

## Workflow

1. **ORIENT:**
   - Read `{session_dir}/p3.json` to get the needs list
   - Read `{session_dir}/p4.json` for baseline metrics context
   - Read `${CLAUDE_PLUGIN_ROOT}/skills/phase-6-opportunity-scoring/odi-scoring.md` with the Read tool

2. **READ THE SCORES:**
   - With a `scores_path`: read it. Use its numbers as they are. Never estimate a number that the file gives, because the file holds the exact result of the script.
   - With no `scores_path` and an expert-estimate source in `{session_dir}/p5.json`: take importance and satisfaction from `p5.json`, score each need by the formula, and set `data_source` to `ai_estimated`.
   - With no `scores_path` and no estimates: when `checkpoints` is true, write an item for `survey_data_path` to `{session_dir}/questions.json` (the shape of an item in `${CLAUDE_PLUGIN_ROOT}/questions/discover.json`), end your reply with the line `QUESTIONS: {session_dir}/questions.json`, and stop. Otherwise stop and say that the survey file is missing.
   - When the run says a script failed, record that as a gap in `p6.json` and work from the estimates.

3. **DATA QUALITY CHECK:**
   - Verify sample size (minimum 50 responses)
   - Check for straight-lining (same rating for all needs)
   - Document: valid responses count
   - Below 50 responses: mark the results as preliminary

4. **IDENTIFY TOP OPPORTUNITIES:**
   - Filter needs with opportunity score ≥ 12
   - Typical distribution:
     - Extremely high (15-20): 5-10 needs
     - High (12-15): 10-15 needs
     - Moderate (10-12): 15-20 needs
   - Select the top 15-20 needs for further analysis

5. **SEGMENT-SPECIFIC ANALYSIS:**
   - If the survey has segment data, note the needs that vary across segments.
   - If not, use the overall scores. Segmentation happens in Phase 8.

6. **VALIDATE RESULTS:**
   - Do the top opportunities align with customer pain points?
   - Are they outcome-focused (not features)?
   - Are they actionable?
   - If any seem off, say so in the summary.

7. **FINALIZE OPPORTUNITY SCORES:**
   - Write the object under "Output Artifacts" to `{session_dir}/p6.json` with the Write tool.

8. **NEXT PHASE TRANSITION:**
   - Show the top 10 opportunities
   - Say that Phase 7 calculates economic value and Phase 8 finds customer segments
   - Exit with success; the skill starts the next phase

## Output

**Phase Artifact:**
- `{session_dir}/p6.json` — ranked opportunities with ODI scores (the skill reads it for Phases 7 and 8, and exports the CSV reports from it)

**Summary:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 6 Complete: Opportunity Scoring
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Job: "Get to destinations on time"
Survey: 78 responses, 85 needs analyzed

TOP 10 OPPORTUNITIES:

1. Minimize time to identify traffic delays
   Importance: 9.2 | Satisfaction: 3.1 | Gap: 6.1
   Opportunity: 15.3 (EXTREMELY HIGH)

2. Determine alternative routes during congestion
   Importance: 8.8 | Satisfaction: 3.5 | Gap: 5.3
   Opportunity: 14.1 (HIGH)

... (8 more)

Score Distribution:
  Extremely High (15-20): 8 needs
  High (12-15): 12 needs
  Moderate (10-12): 18 needs
  Low (<10): 47 needs

Next Steps:
1. Proceed to Phase 7: EVC Calculation (economic value)
2. Then Phase 8: Segmentation Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Success Criteria

- ✅ Scores read from the result file, or estimated and labeled `ai_estimated`
- ✅ Top 15-20 opportunities identified (score ≥ 12)
- ✅ Results validated against customer pain points
- ✅ `p6.json` written and ready for Phase 7

## Common Issues

**Issue:** Low sample size (<50 responses)
- **Fix:** Mark results as preliminary, recommend more data

**Issue:** All scores are similar (no clear winners)
- **Fix:** Check for survey design issues, consider needs refinement

**Issue:** Top opportunities seem wrong
- **Fix:** Review survey questions, check for bias

**Issue:** The score script failed
- **Fix:** Estimate by the formula, label `ai_estimated`, and record the gap

**Issue:** Missing importance or satisfaction data
- **Fix:** Request complete dataset, cannot proceed without both

---

**Author:** Luis F. Amadeo (Chief Agentic Officer)
**License:** MIT
**For:** JTBD Market Discovery Plugin

## Output Artifacts

**Required — the skill reads this for Phases 7 and 8.**

Write phase output to `{session_dir}/p6.json` before signaling completion. Write it with the `Write` tool. When your dispatch context has no `session_dir`, stop and say so. Its shape:
```
{
    "job_statement": "...",
    "total_needs_scored": 87,
    "top_opportunities": [
        {
            "opportunity_id": "O001",
            "need_id": "N023",
            "need": "Minimize time to identify traffic delays",
            "importance": 9.2,
            "satisfaction": 3.1,
            "odi_score": 15.3,
            "level": "Severely Underserved"
        }
    ],
    "distribution": {
        "severely_underserved": 8,
        "underserved": 15,
        "appropriately_served": 42,
        "overserved": 22
    },
    "data_source": "survey",    # "survey" | "ai_estimated"
    "respondents": 87
}
```

After writing p6.json, emit your completion signal as the final line:

`DONE: opportunity-scorer`
