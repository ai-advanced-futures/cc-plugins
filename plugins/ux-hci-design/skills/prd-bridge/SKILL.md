---
name: prd-bridge
description: Use when the person has a product requirements document (a PRD Markdown file) and wants design specifications from it. The skill maps it to its JSON structure. Holds the rules that map requirements to UX artifacts, with accessibility and AI-HCI checks.
---

# PRD Bridge Skill

## Purpose

Transform Product Requirements Documents (PRDs) into UX design specifications. Bridge the gap between product management and UX design by mapping requirements to design artifacts while ensuring accessibility and AI-HCI considerations are integrated.

## Transformation Overview

| PRD Input | UX Output |
|-----------|-----------|
| Requirements | Feature specifications |
| Success Metrics | UX metrics targets |
| User Stories | Interaction scenarios |
| Constraints | Design constraints |
| Scope | Feature prioritization |
| Acceptance Criteria | Validation checklist |

## PRD Input Schema

The person gives a PRD Markdown file. Map it to this structure before you apply the rules.

### Expected PRD Structure

```json
{
  "prd_metadata": {
    "title": "Product title",
    "version": "1.0",
    "status": "draft|review|approved"
  },
  "problem_statement": {
    "problem": "What problem we're solving",
    "impact": "Why it matters",
    "target_users": ["User segments"]
  },
  "requirements": [
    {
      "requirement_id": "REQ-001",
      "title": "Requirement title",
      "description": "Detailed description",
      "priority": "P0|P1|P2|P3",
      "type": "functional|non-functional|technical",
      "acceptance_criteria": ["List of criteria"],
      "success_metrics": [
        {"metric": "Metric name", "target": "Target value"}
      ]
    }
  ],
  "user_stories": [
    {
      "story_id": "US-001",
      "as_a": "User type",
      "i_want": "Capability",
      "so_that": "Benefit",
      "acceptance_criteria": ["Criteria"]
    }
  ],
  "constraints": {
    "technical": ["Technical constraints"],
    "business": ["Business constraints"],
    "timeline": "Delivery timeline",
    "budget": "Budget constraints"
  },
  "out_of_scope": ["Items explicitly excluded"]
}
```

## Transformation Rules

### 1. Requirements → Feature Specifications

```markdown
## Transformation Process

### Input (PRD Requirement)
{
  "requirement_id": "REQ-001",
  "title": "AI-powered code review summary",
  "description": "System shall generate summaries of code changes",
  "priority": "P0",
  "acceptance_criteria": [
    "Summary appears within 5 seconds",
    "Accuracy rate > 90%"
  ]
}

### Output (Design Feature)
{
  "feature_id": "F-001",
  "name": "AI Code Summary",
  "description": "AI-generated summary of code changes",
  "priority": "must_have",
  "source_requirement": "REQ-001",
  "user_story": "As a reviewer, I want an AI summary so I understand changes quickly",
  "acceptance_criteria": [
    "Summary appears within 5 seconds",
    "Accuracy rate > 90%",
    "Keyboard accessible",
    "Screen reader announces summary"
  ],
  "accessibility_requirements": [
    "4.5:1 contrast ratio",
    "aria-live for dynamic content",
    "Keyboard dismissible"
  ],
  "ai_requirements": {
    "transparency": "AI badge visible",
    "confidence_display": true,
    "user_control": "Edit and dismiss available"
  }
}
```

### 2. Success Metrics → UX Metrics

```markdown
## Metric Mapping

### PRD Metric Types
- Business metrics (revenue, conversion)
- Product metrics (adoption, retention)
- Quality metrics (error rates, performance)

### UX Metric Translation

| PRD Metric | UX Metric | Measurement |
|------------|-----------|-------------|
| Task completion rate | Usability score | Task success % |
| Time to complete | Efficiency score | Time on task |
| Error rate | Error frequency | Errors per task |
| User satisfaction | CSAT/SUS score | Survey rating |
| Adoption rate | Learnability | Time to first success |
```

### 3. User Stories → Interaction Scenarios

```markdown
## Story to Scenario Transformation

### Input (User Story)
As a senior engineer
I want to see a summary of code changes
So that I can review PRs faster

### Output (Interaction Scenario)
{
  "scenario_id": "SC-001",
  "persona_reference": "Efficiency-Focused Reviewer",
  "goal": "Review PR faster",
  "context": "Received PR notification, limited time",
  "steps": [
    {"step": 1, "action": "Open PR from notification", "touchpoint": "notification"},
    {"step": 2, "action": "View AI summary", "touchpoint": "summary_panel"},
    {"step": 3, "action": "Scan highlighted changes", "touchpoint": "diff_view"},
    {"step": 4, "action": "Add comments", "touchpoint": "comment_panel"},
    {"step": 5, "action": "Submit review", "touchpoint": "submit_button"}
  ],
  "success_criteria": [
    "Review completed in < 5 minutes",
    "All critical issues identified"
  ],
  "accessibility_scenarios": [
    "Same flow with keyboard only",
    "Same flow with screen reader"
  ]
}
```

### 4. Constraints → Design Constraints

```markdown
## Constraint Mapping

### Technical Constraints
PRD: "Must work on slow connections"
Design: "Loading states, skeleton screens, progressive loading"

### Business Constraints
PRD: "Must launch in 6 weeks"
Design: "Focus on MVP features, defer polish"

### Regulatory Constraints
PRD: "Must meet GDPR requirements"
Design: "Privacy controls, data visibility, consent flows"

### Accessibility Constraints
(Always added if not in PRD)
Design: "WCAG 2.2 Level AA compliance"
```

## Accessibility Integration

### Adding Accessibility Requirements

```markdown
## For Every PRD Requirement

### Check and Add
1. Keyboard operability requirement
2. Screen reader compatibility requirement
3. Contrast and visibility requirements
4. Touch target size requirements
5. Motion sensitivity considerations
6. Cognitive load considerations

### Example Enhancement
PRD: "User can submit feedback"
Enhanced: "User can submit feedback using mouse, keyboard (Enter), or voice command.
         Form validation errors are announced to screen readers.
         Submit button has 44x44px touch target."
```

## AI-HCI Integration

### Adding AI Requirements

```markdown
## For Every AI-Powered Feature

### Per Microsoft 18 Guidelines

1. **Transparency**: How is AI involvement indicated?
2. **Confidence**: How is certainty communicated?
3. **Explanation**: Can users understand why?
4. **Control**: Can users override or dismiss?
5. **Feedback**: Can users correct the AI?
6. **Degradation**: What if AI fails?

### Example Enhancement
PRD: "AI generates code summary"
Enhanced:
  - "AI" badge indicates generated content
  - Confidence score shown (low/medium/high)
  - "Show reasoning" link available
  - Edit and dismiss buttons accessible
  - Thumbs up/down for feedback
  - Manual summary option if AI unavailable
```

## Priority Mapping

### PRD Priority to MoSCoW

| PRD | MoSCoW | Description |
|-----|--------|-------------|
| P0 | Must Have | Critical for launch |
| P1 | Should Have | Important for value |
| P2 | Could Have | Nice to have |
| P3 | Won't Have (this release) | Future consideration |

### Design Priority Adjustment

```markdown
## Factors That Can Elevate Priority

1. **Accessibility requirement** - May elevate priority
   - If feature is inaccessible, it may become P0 to fix

2. **AI failure path** - May need elevation
   - Manual fallback for AI features

3. **Error handling** - Often under-prioritized
   - Error states need same priority as happy path
```

## Output Generation

### Design Requirements Document

```json
{
  "schema_version": "1.0",
  "design_requirements": {
    "source_prd": {
      "title": "PRD title",
      "version": "1.0"
    },
    "features": [
      {
        "feature_id": "F-001",
        "source_requirement": "REQ-001",
        "name": "Feature name",
        "priority": "must_have",
        "acceptance_criteria": [],
        "accessibility_requirements": [],
        "ai_requirements": {}
      }
    ],
    "interaction_scenarios": [],
    "design_constraints": {
      "technical": [],
      "business": [],
      "accessibility": ["WCAG 2.2 Level AA"],
      "ai_hci": ["Microsoft 18 Guidelines alignment"]
    },
    "ux_metrics": [],
    "out_of_scope": []
  },
  "metadata": {
    "transformed_date": "2025-01-20T10:00:00Z",
    "transformed_by": "PRD Bridge Skill"
  }
}
```

## Validation Checklist

### Before Transformation Complete

```markdown
## PRD Bridge Validation

### Completeness
- [ ] All PRD requirements mapped to features
- [ ] All user stories mapped to scenarios
- [ ] All constraints captured

### Accessibility
- [ ] Every feature has accessibility requirements
- [ ] Keyboard operability specified
- [ ] Screen reader compatibility specified
- [ ] WCAG level target set

### AI-HCI
- [ ] AI features have transparency requirements
- [ ] User control mechanisms specified
- [ ] Failure/degradation paths defined
- [ ] Feedback mechanisms included

### Traceability
- [ ] Each feature linked to source requirement
- [ ] Priority mapping documented
- [ ] Out of scope items noted
```

## Handoff Checklist

Before transitioning to IDEATE phase:

- [ ] PRD fully parsed
- [ ] All requirements transformed
- [ ] Accessibility requirements added
- [ ] AI-HCI requirements added
- [ ] Constraints documented
- [ ] Priorities mapped
- [ ] design_requirements.json generated
- [ ] Validation checklist complete

## Quality Criteria

Transformation is complete when:

1. **Complete**: All PRD elements mapped
2. **Accessible**: WCAG requirements added
3. **AI-Aware**: AI features have HCI requirements
4. **Traceable**: Clear links to source requirements
5. **Prioritized**: MoSCoW mapping applied
6. **Validated**: Output passes schema validation

---

**Input**: PRD document
**Output**: design_requirements.json
**Used By**: IDEATE phase, the helper skill ux-concept-designer
**Integrates With**: jtbd-bridge (if JTBD data available)
