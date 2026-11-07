---
name: phase-5-survey-deployment
description: Phase 5 of JTBD discovery — design and deploy a survey to collect importance and satisfaction ratings (1-10 scale) for all 80-100 customer needs from 50+ respondents
---

# Phase 5: Survey Deployment

**Goal:** Collect importance (1-10) and satisfaction (1-10) ratings for all needs from 50+ customers
**Duration:** Survey fielding: 1-2 weeks
**Output:** Survey data CSV → used by the discover skill to continue to Phase 6

## Survey Structure

**Rating Questions (per need):**
"How important is it to [NEED]?" (1-10)
"How satisfied are you with how well you can [NEED]?" (1-10)

## Survey CSV Format

```csv
respondent_id,need_id,need_description,importance,satisfaction
R001,N001,"Minimize time to identify traffic delays",9,3
```

## Sample Size Requirements

| Confidence Level | Min. Respondents |
|-----------------|------------------|
| Exploratory | 30+ |
| Reliable | 50+ |
| High confidence | 100+ |

## Data Quality Checks

Remove respondents who:
- Straight-line all ratings (all 7s across 80 needs)
- Complete in < 5 minutes
- Rate all needs 1 or 10

## Skill Behavior

Phase 5 is the only phase where the discover skill waits for user confirmation that survey data is collected. Phase 5 is not marked complete until user confirms data is ready.
