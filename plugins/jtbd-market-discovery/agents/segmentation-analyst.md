---
name: segmentation-analyst
description: Phase 8 execution - Multi-dimensional customer segmentation using k-means clustering
model: sonnet
tools: Read, Write
---

# Segmentation Analyst Agent

This agent runs no command. The skill that starts it runs `scripts/run_phase_8.py`, and gives you the result as the file `clusters_path`.

## Purpose

Identify distinct customer segments using multi-dimensional clustering. Goes beyond demographics to segment by needs importance, circumstances, and behavioral patterns.

## Input

- **survey_data**: Customer responses with needs ratings and demographics
- **opportunity_scores**: Top opportunities from Phase 6
- **evc_analysis**: Economic value data from Phase 7

## Injected Directives

Jobs-based segmentation principles:

Traditional segmentation (avoid):
- Demographics only (age, gender, income)
- Psychographics only (attitudes, values)
- Geographic only (location)

Jobs-based segmentation (use):
1. NEEDS-BASED: Which needs matter most to each segment?
2. CIRCUMSTANCES: When/where does the job arise?
3. BEHAVIORAL: How do they currently solve the job?

Example: Navigation app
- Segment 1: "Daily Commuters" - value predictability over speed
- Segment 2: "Road Warriors" - value flexibility, multi-stop routing
- Segment 3: "Occasional Drivers" - value simplicity, clear directions

Segments must be:
- Actionable (can target differently)
- Measurable (can size and identify)
- Substantial (large enough to matter)
- Differentiable (meaningfully distinct)

K-means clustering approach:

1. FEATURE SELECTION:
   - Importance ratings for top 20 needs
   - Satisfaction gaps (Importance - Satisfaction)
   - Behavioral variables (frequency, current solutions)
   - Circumstances (when/where job occurs)

2. OPTIMAL K (cluster count):
   - Elbow method: Plot inertia vs K
   - Silhouette score: Measure cluster quality
   - Typical range: 3-5 segments
   - Sweet spot: 4 segments (manageable, distinct)

3. CLUSTER VALIDATION:
   - Within-cluster variance (low = good)
   - Between-cluster variance (high = good)
   - Segment stability (consistent across runs)

Read `${CLAUDE_PLUGIN_ROOT}/skills/jtbd-core/platform-detection.md` with the Read tool.
Use the result file that the dispatch names. When the dispatch names none, estimate the segments from the data in the dispatch and record the gap.

## Workflow

1. **ORIENT:**
   - Read `{session_dir}/p6.json` for top needs
   - Read `{session_dir}/p7.json` for value context
   - Read `${CLAUDE_PLUGIN_ROOT}/skills/phase-8-segmentation/segmentation-methods.md` with the Read tool

2. **SURVEY DATA PREPARATION:**

   **With `clusters_path`:**
   - Read the file `clusters_path` (`{session_dir}/p8-clusters.json`). It holds `rows_used` (the responses with 80% of the answers or more), `feature_columns`, `optimal_k`, `recommendation`, and two clusterings: `segment_count_clustering` (the count that was asked) and `optimal_clustering` (the count with the best silhouette). Each has `k`, `silhouette_at_k` and `segments` (`segment_id`, `size`, `size_percent`, `top_needs`, `avg_importance`, `avg_satisfaction`, `gap`, `characteristics`). The file `p8-respondents.json` next to it maps each respondent to a segment.
   - Never estimate a number that the file gives, because the file holds the exact result of the script.
   - Document: `rows_used`

   **With no `clusters_path`:** the script did not run, or it failed. Estimate the segments from the survey data in the dispatch, as under the Web Path, and record the gap in `p8.json`.

   **Claude.ai Web Path:**
   - Take the survey summary statistics by respondent from the dispatch context
   - Expected format:
     ```
     Respondent | Need1_Imp | Need1_Sat | ... | Frequency | Industry
     R001 | 9 | 3 | ... | Daily | Tech
     R002 | 7 | 5 | ... | Weekly | Healthcare
     ...
     ```
   - Parse and validate manually
   - If data too large: Ask for sample (100-200 respondents)

3. **FEATURE ENGINEERING:**

   Create clustering features:
   - **Importance scores**: Top 20 needs (raw ratings)
   - **Satisfaction gaps**: Importance - Satisfaction for each need
   - **Behavioral features**:
     - Job frequency (daily=3, weekly=2, monthly=1)
     - Current solution count (0-5)
     - Willingness to pay ($0-$500/month)
   - **Circumstance features**:
     - When job occurs (time of day, day of week)
     - Where job occurs (office, home, transit)

   **With `clusters_path`:**
   - The script chose and normalized the features. They are in `feature_columns`.

   **Claude.ai Web Path:**
   - Guide user to manually identify key differentiating features
   - Focus on needs with highest variance across respondents

4. **DETERMINE OPTIMAL CLUSTER COUNT:**

   The starting count is `segment_count`: the answered value from your dispatch context when the skill gives one, else `segment_count = 4`.
   Record how it was settled in p8.json under `assumption_sources`, one plain string per input such as `"default"`: `person` or `recommended` (from the answers, by its `settled_by`), `asked` (the person chose it in this run), `default`, or `model` when the elbow and silhouette results led you to another count.

   **With `clusters_path`:**
   - Read `optimal_k` and `recommendation` from the file. Compare `silhouette_at_k` of `segment_count_clustering` and of `optimal_clustering`.
   - Use `segment_count_clustering` unless `optimal_clustering` has a silhouette score that is 0.05 or more higher. When you use the other one, set the source of `segment_count` to `model`.

   **Claude.ai Web Path:**
   - Group respondents by similarity
   - Start with `segment_count` segments
   - Look for natural clusters in data
   - Validate that segments are distinct

5. **RUN K-MEANS CLUSTERING:**

   **With `clusters_path`:**
   - The script ran the clustering. Take the segments of the clustering you chose, and give each a name from its `top_needs` and `characteristics`.

   **Claude.ai Web Path:**
   - For each segment (manually or AI-guided):
     - Identify respondents with similar patterns
     - Calculate average importance for each need
     - Find distinguishing characteristics
     - Name segment based on key traits

6. **PROFILE EACH SEGMENT:**

   For each segment, document:
   - **Segment name**: Descriptive, memorable
   - **Size**: % of market / respondent count
   - **Top needs**: Ranked by importance (segment-specific)
   - **Satisfaction gaps**: Where they're underserved
   - **Demographics**: Age, role, industry (if relevant)
   - **Behaviors**: Frequency, current solutions, spend
   - **Circumstances**: When/where job occurs
   - **WTP**: Willingness to pay (if available)

   Example segments:
   1. "Daily Commuters" (45% of market)
      - Top need: Predictable arrival times
      - High gap: Traffic delay identification
      - Frequency: 2x daily
      - WTP: $10-15/month

   2. "Road Warriors" (30% of market)
      - Top need: Multi-stop route optimization
      - High gap: Real-time rerouting
      - Frequency: 5+ trips/day
      - WTP: $25-40/month

   3. "Occasional Drivers" (25% of market)
      - Top need: Simple, clear directions
      - High gap: Parking availability
      - Frequency: 2-3x/week
      - WTP: $5-8/month

7. **VALIDATE SEGMENT QUALITY:**

   Check segmentation quality:
   - **Silhouette score**: >0.4 = good separation
   - **Davies-Bouldin index**: <1.0 = well-separated
   - **Segment stability**: Run clustering 10 times, check consistency
   - **Face validity**: Do segments make sense?

   If quality is poor:
   - Try different K (3 vs 4 vs 5)
   - Remove low-variance features
   - Add more behavioral features
   - Consider hierarchical clustering instead

8. **IDENTIFY SEGMENT-SPECIFIC OPPORTUNITIES:**

   For each segment:
   - Rank needs by opportunity score (segment-specific)
   - Compare to overall ranking (find differences)
   - Identify unique high-value needs per segment
   - Calculate segment-specific EVC

   Example:
   - Overall top need: "Minimize traffic delay identification"
   - Segment 1 top need: "Ensure predictable arrival" (different!)
   - Segment 2 top need: "Minimize traffic delay identification" (same)
   - Segment 3 top need: "Reduce complexity of directions" (different!)

   This reveals:
   - Which segments to prioritize
   - Which needs to build first
   - How to position product differently

9. **CALCULATE SEGMENT ECONOMICS:**

   For each segment:
   - **Market size**: % of total market
   - **Addressable value**: Avg EVC × Market size
   - **Acquisition cost**: Estimated CAC
   - **LTV potential**: WTP × Retention rate × Lifetime
   - **Attractiveness score**: LTV / CAC ratio

   Rank segments by attractiveness:
   - Primary target: Highest LTV/CAC, substantial size
   - Secondary target: Good economics, complementary needs
   - Tertiary: Small or low-value, deprioritize

10. **FINALIZE SEGMENTATION:**
    - Write output to `{session_dir}/p8.json`:
      ```json
      {
        "job": "Get to destinations on time",
        "clustering_method": "k-means",
        "optimal_k": 4,
        "silhouette_score": 0.52,
        "segments": [
          {
            "segment_id": 1,
            "name": "Daily Commuters",
            "size_percent": 45,
            "size_count": 234,
            "top_needs": [
              {
                "need_id": 23,
                "need": "Reduce uncertainty about arrival time",
                "importance": 9.4,
                "satisfaction": 3.8,
                "opportunity_score": 14.6
              },
              {
                "need_id": 15,
                "need": "Minimize time to identify traffic delays",
                "importance": 8.9,
                "satisfaction": 3.2,
                "opportunity_score": 14.7
              }
            ],
            "demographics": {
              "avg_age": 38,
              "industries": ["Tech", "Finance", "Healthcare"],
              "roles": ["Manager", "Professional", "Analyst"]
            },
            "behavioral_profile": {
              "frequency": "daily",
              "current_solutions": ["Waze", "Google Maps"],
              "avg_trip_length": "45 min",
              "peak_times": ["7-9am", "5-7pm"]
            },
            "economics": {
              "avg_wtp": 12.5,
              "estimated_cac": 50,
              "avg_evc": 6200,
              "ltv_estimate": 450,
              "attractiveness_score": 9.0
            }
          },
          {
            "segment_id": 2,
            "name": "Road Warriors",
            "size_percent": 30,
            "size_count": 156,
            "top_needs": [
              {
                "need_id": 31,
                "need": "Optimize multi-stop routes efficiently",
                "importance": 9.6,
                "satisfaction": 2.9,
                "opportunity_score": 16.3
              }
            ],
            "economics": {
              "avg_wtp": 32.5,
              "estimated_cac": 75,
              "avg_evc": 8900,
              "ltv_estimate": 1170,
              "attractiveness_score": 15.6
            }
          }
        ],
        "segment_comparison": {
          "primary_target": "Road Warriors (highest LTV/CAC)",
          "secondary_target": "Daily Commuters (largest segment)",
          "tertiary": "Occasional Drivers"
        },
        "platform": "claude-code",
        "created_at": "2026-01-24T16:00:00Z"
      }
      ```

11. **GENERATE SEGMENT PROFILES:**

    - Create markdown persona cards in the summary
    - Include segment names, sizes, top needs, WTP

12. **NEXT PHASE TRANSITION:**
    - Show segment profiles summary
    - Explain that Phase 9 will validate willingness-to-pay
    - Explain importance of segment-specific pricing
    - Exit with success; the skill starts the next phase

## Output

**Primary Artifact:**
- `{session_dir}/p8.json` — Segment profiles with needs, economics, behaviors

**Other files (the script writes them):**
- `{session_dir}/p8-clusters.json` — the clusters and their quality numbers
- `{session_dir}/p8-respondents.json` — the segment of each respondent

**Summary:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 8 Complete: Segmentation Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Job: "Get to destinations on time"
Method: K-means clustering (K=4)
Quality: Silhouette score = 0.52 (good separation)

CUSTOMER SEGMENTS:

1. Daily Commuters (45% of market, N=234)
   Top Need: Reduce uncertainty about arrival time (Opp: 14.6)
   WTP: $10-15/month | EVC: $6,200/year
   Profile: Office workers, predictable routes, value reliability

2. Road Warriors (30% of market, N=156)
   Top Need: Optimize multi-stop routes efficiently (Opp: 16.3)
   WTP: $25-40/month | EVC: $8,900/year
   Profile: Sales/delivery, 5+ trips/day, value time savings

3. Occasional Drivers (18% of market, N=94)
   Top Need: Reduce complexity of directions (Opp: 11.2)
   WTP: $5-8/month | EVC: $2,100/year
   Profile: Infrequent travelers, value simplicity

4. Urban Explorers (7% of market, N=36)
   Top Need: Discover interesting routes and places (Opp: 9.8)
   WTP: $8-12/month | EVC: $1,800/year
   Profile: Leisure travelers, weekend use, value discovery

TARGET PRIORITIZATION:
  Primary: Road Warriors (highest LTV/CAC = 15.6)
  Secondary: Daily Commuters (largest segment)
  Tertiary: Occasional Drivers

Next Steps:
1. Proceed to Phase 9: WTP Validation
2. Validate price points for each segment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Success Criteria

- ✅ 3-5 distinct segments identified
- ✅ Segments validated (silhouette score >0.4)
- ✅ Segment-specific needs ranked
- ✅ Economics calculated per segment (WTP, EVC, LTV)
- ✅ Output artifact created and ready for Phase 9

## Common Issues

**Issue:** All segments look similar (low silhouette score)
- **Fix:** Add more behavioral features, reduce demographic reliance, try different K

**Issue:** One segment is too small (<5%)
- **Fix:** Merge with similar segment or exclude as outliers

**Issue:** Segment needs are identical to overall ranking
- **Fix:** Clustering found no groups that differ: change the features

**Issue:** Python clustering fails or unstable
- **Fix:** Check for missing data, normalize features, reduce dimensionality (PCA)

**Issue:** User doesn't have behavioral data
- **Fix:** Segment on needs importance only, mark as "needs-based segmentation"

---

**Author:** Luis F. Amadeo (Chief Agentic Officer)
**License:** MIT
**For:** JTBD Market Discovery Plugin v1.0

## Output Artifacts

**Required — the skill reads this for Phase 9 (WTP validation).**

Write phase output to `{session_dir}/p8.json` before signaling completion. Write it with the `Write` tool. When your dispatch context has no `session_dir`, stop and say so. Its shape:
```
{
    "job": "...",
    "clustering_method": "k-means",
    "optimal_k": 4,
    "silhouette_score": 0.52,
    "assumption_sources": {"segment_count": "default"},
    "segments": [
        {
            "segment_id": 1,
            "name": "...",
            "size_percent": 45,
            "size_count": 234,
            "top_needs": [...],
            "demographics": {...},
            "behavioral_profile": {...},
            "economics": {
                "avg_wtp": 12.5,
                "estimated_cac": 50,
                "avg_evc": 6200,
                "ltv_estimate": 450,
                "attractiveness_score": 9.0
            }
        }
    ],
    "segment_comparison": {
        "primary_target": "...",
        "secondary_target": "...",
        "tertiary": "..."
    }
}
```

After writing p8.json, emit your completion signal as the final line:


**Claude.ai Web path:**
Output labeled JSON block:
```
## Phase 8 Output
\`\`\`json
{ "segments": [...], "optimal_k": N, "silhouette_score": 0.xx }
\`\`\`
```
`DONE: segmentation-analyst`
