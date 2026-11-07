---
name: ux-evaluate
description: Use in the test phase of Design Thinking, when wireframes exist. Holds the method for an evaluation with the Nielsen heuristics, WCAG compliance and the AI-HCI guidelines. The agent ux-evaluator reads it.
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/check_output.py *)
---

# TEST Phase Skill (Evaluate)

## Purpose

Evaluate design artifacts against multiple established frameworks. The skill `ux-design` starts the domain reviewers (accessibility, AI-HCI, usability) in the main conversation. The agent `ux-evaluator` then merges their findings into one UX health score with prioritized recommendations.

## Theoretical Foundation

This skill coordinates evaluation against foundational UX frameworks:

- **Jakob Nielsen**: 10 Usability Heuristics for Interface Design (1994)
- **Don Norman**: Design of Everyday Things, Emotional Design principles
- **Dieter Rams**: 10 Principles of Good Design
- **Ben Shneiderman**: 8 Golden Rules of Interface Design
- **WCAG 2.2**: Web Content Accessibility Guidelines (W3C)
- **Microsoft Research**: 18 Guidelines for Human-AI Interaction (Amershi et al., CHI 2019)

## Evaluation Framework Coverage

### Nielsen's 10 Usability Heuristics

| # | Heuristic | Focus Area |
|---|-----------|------------|
| H1 | Visibility of system status | Feedback, loading states |
| H2 | Match between system and real world | Language, metaphors |
| H3 | User control and freedom | Undo, cancel, escape |
| H4 | Consistency and standards | Conventions, patterns |
| H5 | Error prevention | Constraints, confirmation |
| H6 | Recognition rather than recall | Visibility, context |
| H7 | Flexibility and efficiency of use | Shortcuts, customization |
| H8 | Aesthetic and minimalist design | Focus, clarity |
| H9 | Help users recover from errors | Error messages, recovery |
| H10 | Help and documentation | Contextual help, guides |

### WCAG 2.2 Level AA (POUR Principles)

| Principle | Criteria Count | Focus |
|-----------|----------------|-------|
| Perceivable | 17 | Content presentation |
| Operable | 20 | Navigation, interaction |
| Understandable | 8 | Readability, predictability |
| Robust | 5 | Compatibility, parsing |

### Microsoft 18 Human-AI Interaction Guidelines

| Category | Guidelines | Focus |
|----------|------------|-------|
| Initially | G1-G2 | Capabilities, expectations |
| During Interaction | G3-G6 | Context, social norms |
| When Wrong | G7-G11 | Control, correction, explanation |
| Over Time | G12-G18 | Learning, adaptation, feedback |

### Dieter Rams' 10 Principles

| # | Principle | Evaluation Criteria |
|---|-----------|---------------------|
| R1 | Innovative | Novel solutions |
| R2 | Useful | Functional value |
| R3 | Aesthetic | Visual harmony |
| R4 | Understandable | Self-explanatory |
| R5 | Unobtrusive | Focus support |
| R6 | Honest | Transparency |
| R7 | Long-lasting | Timelessness |
| R8 | Thorough | Detail attention |
| R9 | Environmentally friendly | Resource efficiency |
| R10 | Minimal | Essential only |

## Evaluation Process

### Step 1: Artifact Analysis

```markdown
## Pre-Evaluation Analysis

1. Identify artifact type (wireframe, prototype, design spec)
2. Extract component inventory
3. Identify AI-powered features
4. Determine applicable frameworks
5. Select weighting profile based on context
```

### Step 2: Reviewers

```markdown
## Parallel Evaluation

The skill `ux-design` starts these domain reviewers, based on artifact context:

- ux-hci-design:accessibility-reviewer: Always (WCAG 2.2)
- ux-hci-design:usability-reviewer: Always (Nielsen + Rams)
- ux-hci-design:ai-hci-reviewer: If AI features present (Microsoft 18)
```

### Step 3: Finding Collection

```markdown
## Finding Normalization

1. Read the findings file of each reviewer: `<output_dir>/reviews/<reviewer>/findings.json`, the list under the key `findings`
2. Normalize severity scales (0-4)
3. Deduplicate overlapping findings
4. Link findings to specific components
5. Calculate framework scores
```

### Step 4: Score Calculation

```markdown
## UX Health Score

UX Score = (Σ(framework_score × framework_weight) / Σ(framework_weights_present)) × 100

Where:
- framework_score = passed_criteria / total_criteria — range 0.0 to 1.0
- weight = profile-specific weighting (canonical: scripts/calculate_ux_score.py)
- Denominator normalizes by sum of weights of PRESENT frameworks only
- When all 5 frameworks evaluated and weights sum to 1.0: formula reduces to Σ(score × weight) × 100
- When frameworks are missing (e.g. no AI features → ai_hci absent): score is re-normalized
  so the result represents "how well did the evaluated frameworks perform" not "weighted by absent ones"
```

## Contextual Weighting Profiles

```python
# Key naming: use ai_hci (underscore) to match Python WEIGHTING_PROFILES dict
WEIGHTING_PROFILES = {
    "balanced": {
        "nielsen": 0.25,
        "wcag": 0.25,
        "ai_hci": 0.20,
        "rams": 0.15,
        "norman": 0.15
    },
    "ai-heavy": {
        "nielsen": 0.20,
        "wcag": 0.20,
        "ai_hci": 0.35,
        "rams": 0.10,
        "norman": 0.15
    },
    "accessibility-first": {
        "nielsen": 0.20,
        "wcag": 0.45,
        "ai_hci": 0.15,
        "rams": 0.10,
        "norman": 0.10
    },
    "mobile-first": {
        "nielsen": 0.30,
        "wcag": 0.20,
        "ai_hci": 0.10,
        "rams": 0.20,
        "norman": 0.20
    },
    "enterprise": {
        "nielsen": 0.30,
        "wcag": 0.30,
        "ai_hci": 0.10,
        "rams": 0.10,
        "norman": 0.20
    }
}
```

## Severity Classification

### Nielsen Severity Scale

| Severity | Rating | Description | Action |
|----------|--------|-------------|--------|
| 0 | Not a problem | Disagree this is an issue | None |
| 1 | Cosmetic | Fix if time permits | Low priority |
| 2 | Minor | Low priority fix | Schedule |
| 3 | Major | High priority fix | Address soon |
| 4 | Catastrophe | Must fix before release | Block release |

### Normalized Severity (All Frameworks)

| Level | Impact | Nielsen | WCAG | AI-HCI |
|-------|--------|---------|------|--------|
| Critical | Prevents use | 4 | Level A fail | Trust-breaking |
| High | Significant barrier | 3 | Level AA fail | Control loss |
| Medium | Usability issue | 2 | Best practice | Confusion |
| Low | Enhancement | 1 | Nice-to-have | Optimization |

## Critical Finding Detection

### Workflow Pause Triggers

```markdown
## Critical Criteria (Must Fix)

### WCAG Critical
- Any Level A violation
- Keyboard trap
- Missing text alternatives for essential content
- Color-only information

### AI-HCI Critical
- No AI transparency indicators
- Irreversible AI actions without confirmation
- No override mechanism for AI decisions
- No explanation available for AI outputs

### Nielsen Critical
- System status never shown (H1 catastrophe)
- No error recovery path (H9 catastrophe)
- Inconsistent core navigation (H4 catastrophe)

### Score Threshold
- UX health score < 50 blocks release
```

## Output Format

### Report Schema

Only the evaluator writes this report (the agent `ux-evaluator`, or this skill when it runs alone). A reviewer keeps the shape of its own findings file.

Write the report in the shape of the schema `${CLAUDE_PLUGIN_ROOT}/schemas/outputs/evaluation-report-schema.json`. Read the schema before you write the report. After the normalization above, write the level as `priority`, and write `severity` from this table:

| Normalized level | `priority` | `severity` |
|---|---|---|
| Critical | `critical` | `critical` |
| High | `high` | `major` |
| Medium | `medium` | `moderate` |
| Low | `low` | `minor` |

Write 1 value of the table in `severity`, and no other text, because the schema takes only `critical`, `major`, `moderate`, `minor` and `cosmetic`. This plugin does not use `cosmetic`, because the normalized scale puts the Nielsen value 1 at Low. Tag a finding that rests on an open question or an assumption with `provisional` in `tags`, and name the assumption in its `description`. A `finding_id` is letters, a hyphen and digits, such as `WCAG-1`, `NIELSEN-1` or `AIHCI-1`. Give each finding a new `finding_id` in this form. Do not copy the ID of a reviewer, because `A11Y-001` does not agree with the schema. The `title` of a finding has 10 characters or more, and its `description` 20 or more.

### Evaluation Report Structure

```json
{
  "schema_version": "1.0",
  "evaluation": {
    "title": "UX evaluation of the checkout prototype",
    "evaluation_type": "multi_framework",
    "frameworks_used": [
      "nielsen-usability-10",
      "wcag-2.2"
    ],
    "target": {
      "name": "Checkout flow",
      "type": "prototype"
    },
    "context": {
      "platform": "web_responsive",
      "has_ai_features": false,
      "weighting_profile": "mobile-first"
    },
    "ux_health_score": {
      "overall": 76,
      "breakdown": {
        "nielsen": {
          "score": 82,
          "weight": 0.3
        },
        "wcag": {
          "score": 68,
          "weight": 0.35
        }
      }
    },
    "findings": [
      {
        "finding_id": "WCAG-1",
        "title": "Focus not visible",
        "severity": "critical",
        "priority": "critical",
        "description": "WCAG 2.4.7: the pay button shows no focus indicator.",
        "tags": [
          "wcag",
          "2.4.7"
        ]
      },
      {
        "finding_id": "NIELSEN-1",
        "title": "No loading indicator after submit",
        "severity": "major",
        "priority": "high",
        "description": "H1: the person does not know if the order was sent. Assumption: the payment call takes more than 1 second.",
        "tags": [
          "nielsen",
          "H1",
          "provisional"
        ]
      }
    ],
    "summary": {
      "total_findings": 2,
      "findings_by_severity": {
        "critical": 1,
        "major": 1,
        "moderate": 0,
        "minor": 0,
        "cosmetic": 0
      }
    },
    "recommendations": [
      {
        "recommendation": "Add a visible focus indicator to each control",
        "priority": "critical"
      }
    ]
  },
  "metadata": {
    "evaluation_date": "2026-11-06"
  }
}
```

### Check the report

After you write the report in the main conversation (a run of `/ux-hci-design:ux-evaluate` alone), run this command on its own, with no other command and no echo. The Bash tool reports the exit code. Write each `'` in the path as `'\''`, because inside single quotes the shell runs nothing.

```
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/check_output.py '<output_dir>/evaluation_report.json' --schema evaluation-report-schema.json
```

The evaluator agent does not run it, because it has no `Bash`. The skill `ux-design` runs it after the evaluator returns.

- Exit 0: show the path of the report and the UX health score.
- Exit 1, and the last line of the output is `<n> schema errors in <file>`: fix each field that a line names, write the report again, and run the check 1 more time. When it gives exit 1 again with that last line, show each error line, say "The evaluation report does not agree with its schema", and do not say that the evaluation is complete, because the person would act on a report that fails its schema.
- Each other result (exit 2, another exit code, or an exit 1 with another last line, for example when `uv` cannot get `jsonschema`): show the output, say "The evaluation report was not checked", and do not say that the evaluation is complete, because the report has no proof that it agrees with its schema.

### Grade Scale

| Score Range | Grade | Status |
|-------------|-------|--------|
| 90-100 | A | Excellent |
| 80-89 | B | Good |
| 70-79 | C | Acceptable |
| 60-69 | D | Needs Work |
| 50-59 | F | Poor |
| <50 | Block | Cannot Release |

## Cognitive Walkthrough Protocol

### Task-Based Evaluation

```markdown
## Walkthrough Steps

For each key user task:

1. **Will the user try to achieve the right effect?**
   - Is the action visible?
   - Is it obvious what to do?

2. **Will the user notice that the correct action is available?**
   - Is the control visible?
   - Is it labeled clearly?

3. **Will the user associate the correct action with the effect?**
   - Does the label match the goal?
   - Is the mapping natural?

4. **If the correct action is performed, will the user see progress?**
   - Is feedback provided?
   - Is success clear?
```

## Heuristic Evaluation Protocol

### Evaluator Guidelines

```markdown
## Evaluation Process

1. Independent Review
   - Each evaluator assesses independently
   - No discussion during initial review
   - Document all findings

2. Finding Documentation
   - Screenshot or component reference
   - Heuristic violated
   - Severity rating
   - Recommendation

3. Consolidation
   - Merge findings
   - Resolve severity disagreements
   - Prioritize by impact and effort

4. Report Generation
   - Executive summary
   - Detailed findings
   - Prioritized recommendations
```

## Integration with Design Thinking

### TEST Phase Workflow

```
1. Receive artifacts from PROTOTYPE phase
2. Configure evaluation context
3. Read the findings of the domain reviewers
4. Collect and normalize findings
5. Calculate UX health score
6. Generate evaluation report
7. Identify critical blockers
8. Provide remediation guidance
```

### Iteration Loop

```
If critical findings exist:
  → Return to PROTOTYPE for fixes
  → Re-evaluate affected components
  → Update scores

If score acceptable:
  → Proceed to implementation
  → Document design decisions
  → Archive evaluation artifacts
```

## Quality Criteria

Evaluation is complete when:

1. **Comprehensive**: All applicable frameworks evaluated
2. **Consistent**: Severity normalized across frameworks
3. **Actionable**: Each finding has clear recommendation
4. **Prioritized**: Findings ranked by impact × effort
5. **Critical-aware**: Blockers clearly identified
6. **Documented**: Full report in JSON format

---

**Previous Phase**: PROTOTYPE (wireframes, interaction patterns)
**Agent**: ux-evaluator (merges the reviewer findings)
**Reviewers (started by the skill ux-design)**: accessibility-reviewer, ai-hci-reviewer, usability-reviewer
**Output**: evaluation_report.json
**Next Step**: Remediation of critical findings or implementation

