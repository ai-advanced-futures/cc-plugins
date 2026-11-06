---
name: lenses-forces-analysis
description: Runs when the lens executor or the skill analyze needs the forces lens. It finds the switching dynamics (push, pull, anxiety, habit) between a competitor and the offering.
user-invocable: false
---

# Forces Analysis Lens

## Purpose

Understand what creates momentum for customers to switch solutions because switching dynamics determine competitive wins more than feature comparisons.

## Input Required

- `intelligence-data.json` - Competitive data
- `jtbd-analysis.json` - Performance gaps (cascading input)
- `competitive-ecosystem.json` - Competitor context

## The Four Forces Framework

Based on Bob Moesta's Forces of Progress:

```
                    SWITCHING
                        ↓
    ┌───────────────────────────────────────┐
    │                                       │
    │  PUSH ──────────→  ←─────── PULL     │
    │  (Pain with       (Attraction to     │
    │   current)         new solution)     │
    │                                       │
    │  HABIT ─────────→  ←─────── ANXIETY  │
    │  (Inertia with    (Fear of           │
    │   current)         change)           │
    │                                       │
    └───────────────────────────────────────┘
```

**Forces pushing toward switch:**
- Push: Pain with current solution
- Pull: Attraction to new solution

**Forces resisting switch:**
- Anxiety: Fear of change
- Habit: Comfort with current

## Process

### 1. Map Push Forces

Identify pain points with current solutions:
- What frustrates customers about incumbents?
- What job steps are underserved?
- What triggers active searching?

Link to JTBD gaps:
- Performance gap → Push force strength

### 2. Map Pull Forces

Identify attractions to competitors:
- What do they promise?
- What capabilities attract attention?
- What outcomes do they enable?

Link to JTBD strengths:
- Performance advantage → Pull force strength

### 3. Map Anxiety Forces

Identify switching concerns:
- Implementation complexity
- Learning curve
- Integration risks
- Cost of migration
- Vendor stability

### 4. Map Habit Forces

Identify inertia factors:
- Existing workflows depend on current tool
- Team familiarity
- Sunk cost in customization
- Organizational resistance to change

### 5. Calculate Force Balance

For each competitor relationship:
- Net switching pressure = (Push + Pull) - (Anxiety + Habit)
- Positive = likely to switch
- Negative = likely to stay

## Output Format

Generate `forces-analysis.json`:

```json
{
  "analysis_perspective": "customers_switching_to_competitor_a",
  "forces": {
    "push": {
      "strength": "high",
      "factors": [
        {
          "factor": "Slow report generation",
          "strength": "high",
          "linked_job_step": "step-3",
          "evidence": "Cited in 60% of churn interviews",
          "confidence": "high"
        }
      ],
      "total_score": 8
    },
    "pull": {
      "strength": "high",
      "factors": [
        {
          "factor": "AI-powered automation",
          "strength": "high",
          "linked_job_step": "step-3",
          "evidence": "Key differentiator in their messaging",
          "confidence": "medium"
        }
      ],
      "total_score": 7
    },
    "anxiety": {
      "strength": "medium",
      "factors": [
        {
          "factor": "Data migration complexity",
          "strength": "high",
          "mitigation": "They offer free migration service",
          "confidence": "high"
        },
        {
          "factor": "Learning curve",
          "strength": "low",
          "mitigation": "Similar UX patterns",
          "confidence": "medium"
        }
      ],
      "total_score": 4
    },
    "habit": {
      "strength": "medium",
      "factors": [
        {
          "factor": "Existing workflow integration",
          "strength": "medium",
          "evidence": "Customers have built processes around current tool",
          "confidence": "high"
        }
      ],
      "total_score": 4
    }
  },
  "net_switching_pressure": {
    "score": 7,
    "interpretation": "Strong pressure to switch",
    "formula": "(8 + 7) - (4 + 4) = 7"
  },
  "key_battlegrounds": [
    {
      "force": "push",
      "factor": "Report generation speed",
      "your_action": "Close performance gap",
      "their_action": "Amplify in messaging"
    }
  ]
}
```

## Force Strength Scoring

| Score | Strength | Description |
|-------|----------|-------------|
| 1-2 | Low | Minor factor, easily overcome |
| 3-4 | Medium | Notable factor, influences some |
| 5-6 | High | Strong factor, influences many |
| 7-8 | Very High | Dominant factor, hard to overcome |

## Total Score Calculation

**total_score** for each force = SUM of individual factor strength scores

Strength to numeric value mapping:
- Low strength: 1
- Medium strength: 2
- High strength: 3
- Very High strength: 4

**net_switching_pressure** = (push.total_score + pull.total_score) - (anxiety.total_score + habit.total_score)

Positive net_switching_pressure (>2) = strong switch trigger
Negative net_switching_pressure (<-2) = strong retention
Near zero (-2 to +2) = balanced forces

## Philosophy

<switching_is_complex>
A switch needs a feature and an emotional force together.
Emotional forces matter as much as rational.
Habit and anxiety often win.
</switching_is_complex>

<link_to_jobs>
Push forces trace to job performance pain.
Pull forces trace to job performance promise.
Abstract forces without job context are weak.
</link_to_jobs>

## Cascading Outputs

This lens informs:
- **Synthesis:** Forces balance → Strategic implications
- **Recommendations:** Force manipulation opportunities

## Completion Protocol

After writing all output files:

**Write forces-summary.json** to `data_dir` (from dispatch context):
{
  "lens": "forces-analysis",
  "completed_at": "{ISO 8601 timestamp}",
  "competitors_analyzed": N,
  "headline": "Strongest pull: {top_pull_force}; highest anxiety: {top_anxiety_force}",
  "key_findings": [
    "Primary push force: {force} (intensity: {High|Medium|Low})",
    "Primary pull force: {force} (competitor: {name})",
    "Strongest habit barrier: {habit}",
    "Net switching pressure: {positive=toward switching|negative=against}"
  ],
  "confidence": "{HIGH|MEDIUM|LOW|SPECULATIVE}",
  "warnings": [],
  "data_file": "forces-analysis.json"
}

**Return to caller:** DONE: lens-forces
