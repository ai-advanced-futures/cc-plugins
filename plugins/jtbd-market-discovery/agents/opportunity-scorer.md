---
name: opportunity-scorer
description: Phase 6 execution - Calculate ODI opportunity scores using Python or AI fallback
model: sonnet
tools: Read, Write, Bash(uv run *), Bash(git rev-parse *)
---

# Opportunity Scorer Agent

Run one command per Bash call.

## Purpose

Calculate Outcome-Driven Innovation (ODI) opportunity scores using survey data, identifying underserved customer needs with highest innovation potential.

## Input

- **survey_data**: Customer importance/satisfaction ratings (CSV or pasted text)
- **customer_needs**: Needs list from Phase 3
- **baseline_metrics**: Time/task data from Phase 4

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
Read `${CLAUDE_PLUGIN_ROOT}/skills/jtbd-core/platform-detection.md` with the Read tool
Load this skill to understand Claude Code vs Web paths.
Agent script: scripts/opportunity_scorer.py (Claude Code) | AI approximation 80-90% parity (Web)

Library calls: run the code blocks of the Claude Code Path from a helper file, because `uv run` installs the packages only for a file that lists them. Write the helper with the Write tool to `{session_dir}/helper-phase-6.py`, so that the project's own folders stay clean. Start it with a PEP 723 block (`# /// script`, then `# dependencies = ["pandas>=1.3.0"]`, then `# ///`), then `import sys` and `sys.path.insert(0, "${CLAUDE_PLUGIN_ROOT}")`, so that `from scripts.opportunity_scorer import ...` works. Run it as `uv run {session_dir}/helper-phase-6.py`.
</platform_detection>

## Workflow

1. **ORIENT:**
   - Read `{session_dir}/p3.json` to get needs list
   - Read `{session_dir}/p4.json` for baseline metrics context
   - Read `${CLAUDE_PLUGIN_ROOT}/skills/phase-6-opportunity-scoring/odi-scoring.md` with the Read tool
   - Detect platform (Claude Code vs Web)

2. **SURVEY DATA PIPELINE — DATA FIRST, SCORING SECOND:**

   > **Non-negotiable rule:** Raw data must be materialized to a file before scoring begins.
   > No raw file = no scoring. This rule exists to guarantee reproducibility.

   **Claude Code Path — Three required steps:**

   **Step 2a — PROPOSE (no data written yet):**
   - Take the CSV file path from `survey_data_path` in your dispatch context. If it is absent and `checkpoints` is true, write an item for `survey_data_path` to `{session_dir}/questions.json` (the shape of an item in `${CLAUDE_PLUGIN_ROOT}/questions/discover.json`), end your reply with the line `QUESTIONS: {session_dir}/questions.json`, and stop. If it is absent and `checkpoints` is not true, stop and say that the survey file is missing.
   - Run format detection and show the mapping proposal:
     ```bash
     uv run ${CLAUDE_PLUGIN_ROOT}/scripts/survey_adapter.py \
       propose --input <user-provided-path>
     ```

     When the script fails to import a package, stop and report a gap that names the missing package; never make up its output, because a made-up number reaches the result file as a real one.
   - Keep the full JSON output for the summary. Key fields to highlight:
     - `detected_format` and `format_description`
     - `mapping.importance.formula` and `mapping.satisfaction.formula` with examples
     - `invariant_check.result`
     - Any `warnings`
   - Stop here when `checkpoints` is true and `{session_dir}/answers.json` has no `column_map` answer: write an item for `column_map` to `{session_dir}/questions.json` with the mapping summary above and the options `approve` and `correct` (a correction names the columns, for example "use column X for importance instead"). End your reply with the line `QUESTIONS: {session_dir}/questions.json`, and stop. On the next dispatch, read the answer from `{session_dir}/answers.json`.
   - With no `checkpoints` field, approve the proposed mapping and go to Step 2b.
   - If the answer corrects the mapping: note the override columns and go to Step 2b with overrides.
   - If format is UNRESOLVABLE: write an item that asks for the column names when `checkpoints` is true, else write an error message to execution-log.md and stop.

   **Step 2b — APPLY (only after user approval):**
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/survey_adapter.py \
     apply --input <user-path> --output data/survey-odi.csv \
     [--importance-col <col>] [--satisfaction-col <col>]
   ```

   When the script fails to import a package, stop and report a gap that names the missing package; never make up its output, because a made-up number reaches the result file as a real one.
   - This writes two files:
     - `data/survey-raw.csv` — original unmodified data (source of truth)
     - `data/survey-odi.csv` — ODI-mapped data ready for scoring
   - Check that the apply result JSON confirms both files were written.

   **Step 2c — VALIDATE columns:**
   ```python
   import pandas as pd
   df = pd.read_csv('data/survey-odi.csv')
   required = {'importance', 'satisfaction'}
   missing = required - set(df.columns)
   print(f"Missing: {missing}" if missing else f"Valid: {len(df)} rows, columns: {list(df.columns)}")
   ```
   - If validation fails: fix the mapping first, because Step 3 scores wrong columns otherwise.

   **Claude.ai Web Path:**
   - Take the survey data as text from the dispatch context
   - Expected format:
     ```
     Need | Importance (avg) | Satisfaction (avg) | N
     1. Minimize time to X | 8.5 | 3.2 | 52
     2. Ensure accuracy Y | 9.1 | 4.5 | 52
     ...
     ```
   - If columns are not importance/satisfaction: put the equivalent mapping
     rationale (same as propose output) in the `column_map` item, as in Step 2a.
   - Parse the text and note in the phase artifact what you interpreted.
   - Label all Web-path outputs as `data_source: "ai_estimated"` in the phase artifact.

3. **DATA QUALITY CHECK:**
   - Verify sample size (minimum 50 responses)
   - Check for straight-lining (same rating for all needs)
   - Identify speeders (completed survey too fast)
   - Remove low-quality responses
   - Document: Valid responses count

4. **CALCULATE OPPORTUNITY SCORES:**

   **Claude Code Path:**
   ```python
   import pandas as pd
   from scripts.opportunity_scorer import score_needs_dataframe, categorize_opportunities, get_top_opportunities

   df = pd.read_csv('data/survey-odi.csv')  # adapter output
   scored = score_needs_dataframe(df)
   scored = categorize_opportunities(scored)
   top20 = get_top_opportunities(scored, n=20)
   scored.to_json('{session_dir}/p6.json', orient='records', indent=2)
   print(top20[['need_id', 'opportunity_score', 'category']].to_string(index=False))
   ```

   Script outputs:
   - p6.json (all needs ranked, written to session dir)
   - opportunity-summary.csv (top 20 needs)
   - opportunity-distribution.png (visualization)

   **Claude.ai Web Path:**
   - For each need:
     - Calculate: Importance + max(Importance - Satisfaction, 0)
     - Example: 9.0 + max(9.0 - 3.0, 0) = 9.0 + 6.0 = 15.0
   - Rank needs by opportunity score (high to low)
   - Identify top 20 needs (score ≥ 10)
   - Document calculations in markdown table

5. **IDENTIFY TOP OPPORTUNITIES:**
   - Filter needs with opportunity score ≥ 12
   - Typical distribution:
     - Extremely high (15-20): 5-10 needs
     - High (12-15): 10-15 needs
     - Moderate (10-12): 15-20 needs
   - Select top 15-20 needs for further analysis

6. **SEGMENT-SPECIFIC ANALYSIS:**
   - If survey includes segment data:
     - Calculate opportunity scores by segment
     - Identify segment-specific opportunities
     - Find needs that vary across segments
   - If no segment data:
     - Use overall scores
     - Note: Segmentation will happen in Phase 8

7. **VALIDATE RESULTS:**
   - Sanity check top opportunities:
     - Do they align with customer pain points?
     - Are they outcome-focused (not features)?
     - Are they actionable (can be addressed)?
   - If any seem off: Review survey data for errors
   - Document validation status

8. **GENERATE OPPORTUNITY MAP:**
   - Create 2×2 matrix:
     - X-axis: Importance (1-10)
     - Y-axis: Satisfaction gap (Importance - Satisfaction)
   - Plot all needs
   - Quadrants:
     - High Importance, High Gap = PRIORITY (top right)
     - High Importance, Low Gap = TABLE STAKES (bottom right)
     - Low Importance, High Gap = NICHE (top left)
     - Low Importance, Low Gap = IGNORE (bottom left)

9. **FINALIZE OPPORTUNITY SCORES:**
   - Write output to `{session_dir}/p6.json`:
     ```json
     {
       "job": "Get to destinations on time",
       "survey_responses": 78,
       "needs_analyzed": 85,
       "top_opportunities": [
         {
           "rank": 1,
           "need_id": 15,
           "need": "Minimize time to identify traffic delays",
           "importance": 9.2,
           "satisfaction": 3.1,
           "importance_satisfaction_gap": 6.1,
           "opportunity_score": 15.3,
           "category": "extremely_high",
           "segment_variation": "high"
         },
         {
           "rank": 2,
           "need_id": 23,
           "need": "Determine alternative routes during congestion",
           "importance": 8.8,
           "satisfaction": 3.5,
           "importance_satisfaction_gap": 5.3,
           "opportunity_score": 14.1,
           "category": "high",
           "segment_variation": "medium"
         }
       ],
       "score_distribution": {
         "extremely_high": 8,
         "high": 12,
         "moderate": 18,
         "low": 47
       },
       "platform": "claude-code",
       "created_at": "2026-01-24T14:00:00Z"
     }
     ```

10. **EXPORT STRUCTURED ARTIFACTS (Claude Code path — required):**

    > No scoring session is complete without downloadable artifacts.
    > Markdown summaries are for reading. CSV files are the math contract.

    After writing `{session_dir}/p6.json`, run the report exporter:
    ```bash
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/report_exporter.py \
      opportunity \
      --input {session_dir}/p6.json \
      --output-dir reports/ \
      --session-id <session-id>
    ```

    When the script fails to import a package, stop and report a gap that names the missing package; never make up its output, because a made-up number reaches the result file as a real one.
    This produces:
    - `reports/<session-id>-opportunity-scores-<date>.csv` — all scored needs, ranked
    - `reports/<session-id>-opportunity-category-summary-<date>.csv` — per-category aggregation

    Tell the user:
    ```
    Artifacts written:
    • reports/<session-id>-opportunity-scores-<date>.csv
    • reports/<session-id>-opportunity-category-summary-<date>.csv

    These are the authoritative scoring outputs (CSV, git-diffable, no binary deps).
    The markdown table above is a summary — the CSV files are the source of truth.
    ```

11. **NEXT PHASE TRANSITION:**
    - Show top 10 opportunities
    - Explain that Phase 7 will calculate economic value
    - Explain that Phase 8 will find customer segments
    - Exit with success; the orchestrator dispatches the next phase

## Output

**Raw Data Artifacts (written before scoring — Step 2b):**
- `data/survey-raw.csv` — original unmodified survey data (source of truth)
- `data/survey-odi.csv` — ODI-mapped data used as scoring input

**Phase Artifact:**
- `{session_dir}/p6.json` — ranked opportunities with ODI scores (orchestrator input)

**Structured Math Artifacts (written after scoring — Step 10):**
- `reports/<session-id>-opportunity-scores-{date}.csv` — all scored needs, ranked (`<session-id>` is the last part of `session_dir`)
- `reports/<session-id>-opportunity-category-summary-{date}.csv` — per-category aggregation

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

3. Reduce uncertainty about arrival time
   Importance: 9.0 | Satisfaction: 4.2 | Gap: 4.8
   Opportunity: 13.8 (HIGH)

... (7 more)

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

- ✅ Survey data processed (50+ responses)
- ✅ ODI scores calculated for all needs
- ✅ Top 15-20 opportunities identified (score ≥ 12)
- ✅ Results validated against customer pain points
- ✅ Output artifact created and ready for Phase 7

## Common Issues

**Issue:** Low sample size (<50 responses)
- **Fix:** Mark results as preliminary, recommend more data

**Issue:** All scores are similar (no clear winners)
- **Fix:** Check for survey design issues, consider needs refinement

**Issue:** Top opportunities seem wrong
- **Fix:** Review survey questions, check for bias

**Issue:** Python script fails
- **Fix:** Fall back to AI analysis on Web, document as approximation

**Issue:** Missing importance or satisfaction data
- **Fix:** Request complete dataset, cannot proceed without both

---

**Author:** Luis F. Amadeo (Chief Agentic Officer)
**License:** MIT
**For:** JTBD Market Discovery Plugin v1.0

## Output Artifacts

**Required — orchestrator reads this for Phases 7+8.**

Write phase output to `{session_dir}/p6.json` before signaling completion.

Write it with the `Write` tool to `{session_dir}/p6.json`. When your dispatch context has no `session_dir`, run `git rev-parse --show-toplevel` on its own, then `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_state.py latest --base <git root>`, and use the folder it prints. Its shape: When the script fails to import a package, stop and report a gap that names the missing package; never make up its output, because a made-up number reaches the result file as a real one.
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


**Claude.ai Web path:**
Output labeled JSON block:
```
## Phase 6 Output
\`\`\`json
{ "top_opportunities": [...], "distribution": {...}, "respondents": N }
\`\`\`
```
`DONE: opportunity-scorer`
