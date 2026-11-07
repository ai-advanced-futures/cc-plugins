# Schema Reference

This document describes each schema in the UX/HCI Design Plugin.

## Overview

The plugin uses JSON schemas for three tasks. The schemas hold design knowledge, check outputs, and set the project context. The schemas are in these folders:

```
schemas/
├── heuristics/           # Usability evaluation frameworks
├── design-principles/    # Core design philosophy
├── accessibility/        # WCAG and accessibility standards
├── ai-hci/              # Human-AI interaction guidelines (Microsoft 18)
├── ai-paradigm/         # 2025-2026 AI UX thought leader frameworks (NEW)
├── outputs/             # Output artifact schemas (JSON Schema draft-07)
└── project-context-schema.json  # Project configuration
```

---

## Knowledge Schemas

Knowledge schemas hold the design frameworks and guidelines of expert designers.

### Nielsen's 10 Usability Heuristics

**File:** `schemas/heuristics/nielsen-usability-10.json`

**Purpose:** Holds Jakob Nielsen's 10 Usability Heuristics. Use them to evaluate an interface.

**Structure:**
```json
{
  "title": "Nielsen's 10 Usability Heuristics",
  "version": "1.0",
  "heuristics": [
    {
      "number": 1,
      "name": "Visibility of System Status",
      "short_description": "...",
      "detailed_description": "...",
      "key_principles": ["..."],
      "evaluation_criteria": {
        "questions": ["..."],
        "what_to_look_for": ["..."]
      },
      "common_violations": [
        {
          "issue": "...",
          "example": "...",
          "severity": 3
        }
      ],
      "best_practices": ["..."],
      "remediation_guidance": {
        "quick_fixes": ["..."],
        "comprehensive_solutions": ["..."],
        "testing_approach": ["..."]
      }
    }
  ],
  "severity_scale": {
    "levels": [
      {"level": 0, "label": "No Problem"},
      {"level": 1, "label": "Cosmetic"},
      {"level": 2, "label": "Minor"},
      {"level": 3, "label": "Major"},
      {"level": 4, "label": "Catastrophic"}
    ]
  }
}
```

**Usage:**
```python
import json

with open('schemas/heuristics/nielsen-usability-10.json') as f:
    nielsen = json.load(f)

# Iterate through heuristics for evaluation
for h in nielsen['heuristics']:
    print(f"{h['number']}. {h['name']}")
    for q in h['evaluation_criteria']['questions']:
        print(f"  - {q}")
```

---

### Rams' 10 Principles of Good Design

**File:** `schemas/design-principles/rams-good-design-10.json`

**Purpose:** Holds Dieter Rams' 10 Principles of Good Design.

**Structure:**
```json
{
  "title": "Rams' 10 Principles of Good Design",
  "version": "1.0",
  "principles": [
    {
      "number": 1,
      "name": "Good design is innovative",
      "original_german": "Gutes Design ist innovativ",
      "short_description": "...",
      "detailed_description": "...",
      "key_principles": ["..."],
      "evaluation_criteria": {
        "questions": ["..."]
      },
      "common_violations": [
        {
          "issue": "...",
          "example": "...",
          "impact": "..."
        }
      ],
      "best_practices": ["..."]
    }
  ]
}
```

---

### Norman's Interaction Design Principles

**File:** `schemas/design-principles/norman-interaction-principles.json`

**Purpose:** Holds the interaction design principles of Don Norman. These include affordances, mental models, and the seven stages of action.

**Structure:**
```json
{
  "title": "Norman's Interaction Design Principles",
  "version": "1.0",
  "principles": [
    {
      "number": 1,
      "name": "Visibility",
      "short_description": "...",
      "detailed_description": "...",
      "key_principles": ["..."],
      "evaluation_criteria": {...},
      "common_violations": [...],
      "best_practices": [...]
    }
  ],
  "interaction_framework": {
    "seven_stages_of_action": [
      {
        "stage": "Goal",
        "description": "...",
        "design_implication": "..."
      }
    ],
    "gulfs": {
      "gulf_of_execution": "...",
      "gulf_of_evaluation": "..."
    }
  }
}
```

---

### WCAG 2.2 Accessibility Guidelines

**File:** `schemas/accessibility/wcag-2.2-criteria.json`

**Purpose:** Holds the WCAG 2.2 guidelines with the Level A and Level AA success criteria.

**Structure:**
```json
{
  "title": "WCAG 2.2 Success Criteria",
  "version": "2.2",
  "conformance_levels": {
    "A": "Minimum level",
    "AA": "Target level for most sites"
  },
  "principles": [
    {
      "code": "1",
      "name": "Perceivable",
      "description": "...",
      "guidelines": [
        {
          "code": "1.1",
          "name": "Text Alternatives",
          "success_criteria": [
            {
              "number": "1.1.1",
              "name": "Non-text Content",
              "level": "A",
              "description": "...",
              "techniques": {
                "sufficient": ["..."],
                "advisory": ["..."]
              },
              "test_procedures": ["..."],
              "common_failures": ["..."]
            }
          ]
        }
      ]
    }
  ]
}
```

**Conformance Levels:**
- **Level A:** 31 criteria. This is the minimum level of accessibility.
- **Level AA:** 24 more criteria. This is the recommended target.
- **Level AAA:** The schema does not include this level. Do not use it as a target for all criteria.

---

### Microsoft's 18 Guidelines for Human-AI Interaction

**File:** `schemas/ai-hci/microsoft-guidelines-18.json`

**Purpose:** Holds the 18 Guidelines for Human-AI Interaction from Microsoft Research.

**Structure:**
```json
{
  "title": "Microsoft's 18 Guidelines for Human-AI Interaction",
  "version": "1.0",
  "organization": "Microsoft Research",
  "guidelines": [
    {
      "guideline_number": 1,
      "guideline_name": "Make clear what the system can do",
      "category": "Initially",
      "interaction_phase": "before_interaction",
      "description": "...",
      "evaluation_criteria": {
        "questions": ["..."],
        "indicators": ["..."]
      },
      "common_issues": [
        {
          "issue": "...",
          "example": "...",
          "severity": 2
        }
      ],
      "best_practices": ["..."],
      "related_guidelines": [2, 11]
    }
  ],
  "categories": {
    "Initially": [1, 2],
    "During interaction": [3, 4, 5, 6, 7, 8, 9, 10],
    "When wrong": [11, 12, 13],
    "Over time": [14, 15, 16, 17, 18]
  }
}
```

**Categories:**
1. **Initially** (G1-G2): Set the expectations of the user.
2. **During interaction** (G3-G10): Define how the system behaves while the user works.
3. **When wrong** (G11-G13): Handle errors.
4. **Over time** (G14-G18): Learn from the user and adapt.

---

## AI Paradigm Schemas (2025-2026 Thought Leader Frameworks)

These schemas hold new AI UX patterns from thought leaders. The thought leaders change how people interact with AI systems. The schemas go beyond the heuristics for graphical interfaces. They cover three types of interaction design: design based on intent, design based on outcome, and design for agents that act alone.

### Outcome-Value Framework (Phil Gilbert)

**File:** `schemas/ai-paradigm/outcome-value-framework.json`

**Purpose:** Evaluates an AI system on the value it delivers. It does not evaluate the quality of the interface.

**Key Insight:** "AI output is cheap, so designers must focus on the value and trust of AI actions, not interface polish."

**Key Principles:**
- Value Clarity - Is the value of the outcome clear?
- Value Velocity - How fast does the system deliver value?
- Trust Calibration - Does the trust of the user match the reliability of the system?
- Value Compounding - Does value grow over time?
- Value Transparency - Can users see how the system created the value?

---

### AI-Native Metrics (PSR and Beyond)

**File:** `schemas/ai-paradigm/ai-native-metrics.json`

**Purpose:** A set of new metrics. They replace the metrics for graphical interfaces.

**Key Metrics:**
| Old Metric | New Metric | Why |
|------------|------------|-----|
| Click-through Rate | **Prompt Success Rate (PSR)** | Measures intent capture |
| Page Views | Value per Interaction | Measures outcome value |
| Time on Task | Time to Value | Efficiency of value delivery |
| Error Rate | Recovery Velocity | Speed of error recovery |

**PSR Formula:** `successful_outcomes / total_user_expressions`

**Benchmark Ranges:**
- Excellent: >90%
- Good: 75-90%
- Acceptable: 60-75%
- Poor: <60%

---

### Intent-Based Interaction (Jakob Nielsen 2025)

**File:** `schemas/ai-paradigm/intent-based-interaction.json`

**Purpose:** A framework to evaluate systems that generate the interface from the intent of the user.

**Key Insight:** "Traditional GUI will be replaced by AI agents that generate interfaces on the fly based on user intent."

**Evaluation Dimensions:**
1. Intent Capture Fidelity
2. Interface Generation Appropriateness
3. Intent-Outcome Continuity
4. Zero-Interface Opportunities
5. Intent Evolution Support

---

### AI Integration Maturity (Luke Wroblewski)

**File:** `schemas/ai-paradigm/ai-integration-maturity.json`

**Purpose:** Evaluates an AI feature by its maturity stage.

**5 Maturity Stages:**
| Stage | Name | Human Role | AI Role |
|-------|------|------------|---------|
| 1 | Invisible Enhancement | Unaware user | Hidden optimizer |
| 2 | AI-Assisted | Decision maker | Suggester |
| 3 | AI-Augmented | Exception handler | Routine processor |
| 4 | AI-First | Supervisor | Primary actor |
| 5 | Autonomous Partnership | Partner | Partner |

**Usage:** Use the evaluation criteria that fit the stage. Do not use one set of criteria for all stages.

---

### AI Orchestration Patterns (Phil Schroeder)

**File:** `schemas/ai-paradigm/ai-orchestration-patterns.json`

**Purpose:** A framework to evaluate how humans and AI share the work of a task.

**Paradigm Shift:** The model changes from "user flows" (humans do tasks) to "orchestration flows" (humans direct AI).

**Orchestration Dimensions:**
1. Delegation Clarity - Can humans delegate with clear instructions?
2. Progress Visibility - Can humans see the progress?
3. Intervention Points - Can humans step in at the right time?
4. Outcome Verification - Can humans check the results?
5. Learning Loop - Do the patterns get better over time?

---

### Background Agent Patterns (Birdzhan Hassan)

**File:** `schemas/ai-paradigm/background-agent-patterns.json`

**Purpose:** A framework for AI that works alone while a human supervises it.

**Paradigm Shift:** The model changes from "chat-alike" interaction to "background agent" interaction.

**Evaluation Dimensions:**
1. Autonomous Action Boundaries
2. Proactive Notification
3. Ambient Awareness
4. Recovery and Rollback
5. Trust Evolution

**Autonomy Levels:**
- Tight: The agent does no action without approval.
- Moderate: The agent does routine actions alone. It sends exceptions to a human.
- Loose: The agent does most actions alone. It reports the results.
- Full: A human does only a periodic review.

---

### Hybrid AI-GUI Patterns

**File:** `schemas/ai-paradigm/hybrid-ai-gui-patterns.json`

**Purpose:** A framework for interfaces that combine natural language (conversation) and graphical elements.

**Pattern Categories:**
1. **Modal Switching** - The user moves between natural language and the graphical interface.
2. **Parallel Modalities** - Natural language and the graphical interface work at the same time.
3. **Adaptive Modality Selection** - The system chooses the best modality.

**Hybrid Heuristics:**
1. Modality Coherence - The modalities are consistent.
2. Transition Fluidity - The switch between modalities is smooth.
3. Modality Parity - The user can do the core tasks in all modalities.
4. Selection Appropriateness - The system picks the right modality for the task.
5. User Control of Modality - The user can change the selection.

---

## Output Schemas (JSON Schema draft-07)

Output schemas define the structure of the artifacts that the plugin creates.

### Persona Schema

**File:** `schemas/outputs/persona-schema.json`

**Purpose:** Checks the persona artifacts that the plugin creates.

**Key Fields:**
- `persona.name` - Persona identifier
- `persona.demographics` - Age, occupation, etc.
- `persona.goals` - User goals with priority and frequency
- `persona.pain_points` - Frustrations with severity
- `persona.accessibility_needs` - Vision, hearing, motor, cognitive
- `persona.ai_interaction_preferences` - Transparency, control levels

**Example:**
```json
{
  "schema_version": "1.0",
  "persona": {
    "id": "persona-001",
    "name": "Alex Chen",
    "subtitle": "The Efficient Professional",
    "demographics": {
      "age_range": "28-42",
      "occupation": "Product Manager"
    },
    "goals": [
      {
        "goal": "Complete tasks quickly",
        "priority": "high",
        "frequency": "daily"
      }
    ],
    "accessibility_needs": {
      "vision": "Prefers high contrast",
      "hearing": "None",
      "motor": "RSI concerns",
      "cognitive": "Clear layouts"
    },
    "ai_interaction_preferences": {
      "transparency": "high",
      "control": "high"
    }
  }
}
```

---

### Journey Map Schema

**File:** `schemas/outputs/journey-map-schema.json`

**Purpose:** Checks the customer journey map artifacts.

**Key Fields:**
- `journey.phases` - Journey stages
- `journey.touchpoints` - Interaction points
- `journey.emotions` - Emotional curve data
- `journey.pain_points` - Friction moments
- `journey.opportunities` - Design opportunities

---

### Evaluation Report Schema

**File:** `schemas/outputs/evaluation-report-schema.json`

**Purpose:** Checks the heuristic evaluation reports.

**Key Fields:**
- `evaluation.frameworks_applied` - Nielsen, WCAG, AI-HCI, etc.
- `findings` - Individual issues found
- `framework_scores` - Scores per framework
- `recommendations_summary` - Prioritized actions

**Example Finding:**
```json
{
  "finding_id": "finding-001",
  "framework": "nielsen",
  "principle_id": "nielsen-01",
  "principle_name": "Visibility of System Status",
  "severity": 3,
  "issue": "No loading indicator when fetching data",
  "location": "Dashboard main view",
  "recommendation": "Add skeleton loading states"
}
```

---

### Mental Model Schema

**File:** `schemas/outputs/mental-model-schema.json`

**Purpose:** Checks the mental model diagram artifacts.

**Key Fields:**
- `concepts` - Mental model concepts
- `relationships` - How concepts relate
- `misconceptions` - Common user misunderstandings

---

## Project Context Schema

**File:** `schemas/project-context-schema.json`

**Purpose:** Sets the weights of the evaluation for one project.

**Structure:**
```json
{
  "schema_version": "1.0",
  "project_context": {
    "type": "web-app",
    "domain": "b2b",
    "ai_intensity": "moderate",
    "accessibility_requirements": "required",
    "target_platforms": ["desktop", "mobile"],
    "tech_stack": ["react", "typescript"]
  },
  "weighting_profile": "balanced",
  "priority_frameworks": ["nielsen", "wcag", "ai-hci", "rams", "norman"],
  "custom_weights": {
    "nielsen": 0.25,
    "wcag": 0.25,
    "ai-hci": 0.25,
    "rams": 0.15,
    "norman": 0.10
  }
}
```

**Weighting Profiles:**
- `balanced` - All frameworks have the same weight.
- `accessibility-heavy` - WCAG compliance has the highest priority.
- `ai-heavy` - The AI-HCI guidelines have the highest priority.
- `mobile-focused` - Mobile UX patterns have the highest priority.
- `enterprise` - Efficiency and learnability have the highest priority.

---

## Validation

### Using the Validator

```bash
# Validate all schemas
python3 scripts/validate_schemas.py

# Validate specific schema
python3 scripts/validate_schemas.py --schema schemas/heuristics/nielsen-usability-10.json

# Verbose output
python3 scripts/validate_schemas.py --verbose
```

### Validation Rules

Each schema type has its own validation rules:

| Schema Type | Required Elements | Validation |
|------------|------------------|------------|
| Nielsen | 10 heuristics, severity 0-4 | Unique numbers, complete structure |
| Rams | 10 principles | Unique numbers, German originals |
| Norman | 7+ principles | Framework structure |
| WCAG | 4 POUR principles | Level A/AA criteria |
| AI-HCI | 18 guidelines | Category validation |
| Output | JSON Schema draft-07 | Standard JSON Schema validation |

---

## Extending Schemas

### Adding New Knowledge Schema

1. Create a JSON file in the correct folder.
2. Use the structure of the existing schemas.
3. Add the validation in `scripts/validate_schemas.py`.
4. Add tests in `tests/unit/`.
5. Describe the schema in this file.

### Adding New Output Schema

1. Create a JSON Schema draft-07 file in `schemas/outputs/`. The validator finds output schemas by itself.
2. Add a sample fixture in `tests/fixtures/`.
3. Add integration tests.

---

## References

- [JSON Schema draft-07](https://json-schema.org/draft-07/json-schema-release-notes.html)
- [Nielsen Norman Group](https://www.nngroup.com/)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [Microsoft AI-HCI Guidelines](https://www.microsoft.com/en-us/research/project/guidelines-for-human-ai-interaction/)

---

**Last Updated:** 2026-01-23
