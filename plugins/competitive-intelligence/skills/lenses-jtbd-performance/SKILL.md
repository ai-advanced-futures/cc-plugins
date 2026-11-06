---
name: lenses-jtbd-performance
description: Runs when the lens executor or the skill analyze needs the JTBD performance lens. It compares the speed and the accuracy of each job step across competitors.
user-invocable: false
---

# JTBD Performance Analysis Lens

## Purpose

Compare how well solutions help customers accomplish their jobs because performance gaps on specific job steps reveal actionable competitive advantages and vulnerabilities.

## Input Required

- `intelligence-data.json` - Competitive data gathered in Phase 3
- `competitive-ecosystem.json` - Competitor list and classifications
- `context-config.json` - Analysis scope and depth

## Process

### 1. Job Decomposition

Break down the customer job into 8-15 sequential steps using the 6 universal phases:

| Phase | Description | Example Steps |
|-------|-------------|---------------|
| Understand | Define what needs to happen | Define requirements, Identify constraints |
| Plan | Determine approach | Select approach, Allocate resources |
| Execute | Do the core work | Perform tasks, Monitor progress |
| Assess | Evaluate results | Verify quality, Measure outcomes |
| Revise | Make corrections | Fix issues, Adjust approach |
| Conclude | Finalize and communicate | Document results, Share findings |

### 2. Performance Scoring

For each job step, score each competitor (including your product) on two dimensions:

**Speed (1-5 scale):**
- 1: Very slow, multiple days/weeks
- 2: Slow, hours to complete
- 3: Moderate, reasonable time
- 4: Fast, minutes to complete
- 5: Instant/automated

**Accuracy (1-5 scale):**
- 1: Many errors, unreliable
- 2: Frequent errors, needs checking
- 3: Occasional errors, acceptable
- 4: Rare errors, reliable
- 5: Perfect, no errors

### 3. Gap Calculation

Calculate performance gaps:
- **Significant gap:** 2+ point difference
- **Moderate gap:** 1 point difference
- **Parity:** Same score

Identify:
- Where you lead (your score > competitor)
- Where they lead (competitor score > yours)
- Parity points (equal scores)

### 4. Feature Mapping

Map job steps to specific features/capabilities:
- Which features enable performance on each step?
- What's missing that causes gaps?
- What could close gaps?

## Output Format

Generate `jtbd-analysis.json`:

```json
{
  "job_statement": "Help [customer] accomplish [outcome] when [situation]",
  "job_steps": [
    {
      "id": "step-1",
      "phase": "understand",
      "description": "Define reporting requirements",
      "scores": {
        "your_product": {"speed": 4, "accuracy": 4},
        "competitor_a": {"speed": 5, "accuracy": 4},
        "competitor_b": {"speed": 3, "accuracy": 3}
      },
      "gaps": {
        "competitor_a": {"speed": -1, "accuracy": 0, "significance": "moderate"},
        "competitor_b": {"speed": 1, "accuracy": 1, "significance": "significant"}
      },
      "feature_mapping": {
        "your_product": ["Template library", "Requirements wizard"],
        "competitor_a": ["AI auto-detection"],
        "competitor_b": ["Manual forms"]
      },
      "confidence": "high"
    }
  ],
  "summary": {
    "you_lead": ["step-2", "step-4", "step-6"],
    "they_lead": {
      "competitor_a": ["step-1", "step-3"],
      "competitor_b": []
    },
    "parity": ["step-5"],
    "biggest_gap": {
      "step": "step-3",
      "competitor": "competitor_a",
      "gap": 2,
      "dimension": "speed"
    }
  }
}
```

## Confidence Factors

Apply the standard confidence scale (HIGH/MEDIUM/LOW/SPECULATIVE, defined in confidence_scoring.py). Assign based on:

**High confidence when:**
- Direct product access and testing
- Multiple customer testimonials
- Win/loss data supports findings

**Medium confidence when:**
- Product demos or documentation
- Review site mentions
- Limited testing

**Low confidence when:**
- Marketing claims only
- No direct verification
- Outdated information

## Philosophy

<job_centric>
Job performance matters more than features.
Customers hire products to get jobs done.
Score the job outcome, not the feature list.
</job_centric>

<gap_significance>
Not all gaps matter equally.
2+ point gaps are actionable.
1 point gaps are noise without volume.
</gap_significance>

## Cascading Outputs

This lens informs:
- **Forces Analysis:** Performance gaps → Push/Pull forces
- **Economic Value:** Job step improvements → Value quantification
- **Technology Disruption:** Job step complexity → AI replaceability

## Completion Protocol

After writing all output files:

**Write jtbd-summary.json** to `data_dir` (from dispatch context):
{
  "lens": "jtbd-performance",
  "completed_at": "{ISO 8601 timestamp}",
  "competitors_analyzed": N,
  "headline": "{your_best_steps} lead — {top_competitor} leads step {worst_gap_step} (+{gap_points}pts)",
  "key_findings": [
    "Biggest gap: Step {N}, {competitor} (score {their} vs your {yours})",
    "Your strongest step: Step {N} (score {S}, leads all competitors)",
    "Steps you lead overall: {N} of {total} job steps ({percentage}%)",
    "AI disruption risk: Steps {list} ({high|medium|low} exposure)"
  ],
  "confidence": "{HIGH|MEDIUM|LOW|SPECULATIVE}",
  "warnings": ["{any sparse data warnings}"],
  "data_file": "jtbd-analysis.json"
}

**Return to caller:** DONE: lens-jtbd
