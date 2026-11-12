# UX/HCI Design Plugin - Agent Reference

This document describes the 8 helper skills of the UX/HCI Design plugin. Each one is a forked skill in `skills/<name>/SKILL.md` (`context: fork`), and only the skill `ux-design` starts it.

## Agent Architecture

```
UX Design Orchestrator (/ux-hci-design:ux-design skill)
    │
    ├── EMPATHIZE Phase
    │   └── ux-researcher
    │
    ├── DEFINE Phase
    │   └── ux-artifact-generator
    │
    ├── IDEATE Phase
    │   └── ux-concept-designer
    │
    ├── PROTOTYPE Phase
    │   └── ux-prototype-builder
    │
    └── TEST Phase
        ├── accessibility-reviewer   (the skill starts the reviewers one after the other)
        ├── ai-hci-reviewer          (only when the product has AI features)
        ├── usability-reviewer
        └── ux-evaluator             (starts after them, and merges their findings)
```

---

## Rules for All Agents

- An agent cannot ask the person a question. The skill `ux-design` asks the person with AskUserQuestion.
- When an agent needs an answer, it writes its open questions to `<output_dir>/open-questions.md` and returns. The skill asks these questions and calls the agent again.
- No helper may use the `Agent` tool: its `disallowed-tools` names it, and an `Agent` call of a helper runs in the background in an interactive session. The skill `ux-design` starts all helpers with the `Skill` tool, in the main conversation.
- Only `ux-prototype-builder` has the `Skill` tool (`Skill(tailwind-plus:advise)`).
- Each helper has these `allowed-tools` (the builder has 1 more, the `Skill` grant above): `Edit(/.ux-artifacts/**)` (it approves `Write` and `Edit` in that folder) and `Read` of the skills and the schemas of the plugin. Its `disallowed-tools` names each other tool, among them `Bash`, `AskUserQuestion` and `mcp__*`, but not `Edit` (a reviewer called `Edit` on its own file in 2 of 6 live runs, and a denied name refuses that call). Measured in Claude Code 2.1.322 (8 live runs, 1 for each helper): a forked helper still lists `Agent`, `Bash` and `Skill`, in spite of this field. So the list records the intent, and the permission mode is the real limit: Claude Code refuses a call outside the grants in `-p`, and asks the person in an interactive session. A helper can still try a call of a tool that is not granted, for example `Bash`, and Claude Code refuses it.
- An agent writes its files to `<output_dir>` and nothing else. It does not write the brain `docs/ux-hci-design/`. After each phase, the skill `ux-design` saves the files as pages (`ux_graph.py ingest`) and removes the files that it read. Before it starts an agent, the skill puts a copy of each saved input file in `<output_dir>/inputs/` (`ux_graph.py view --out`), and gives the agent that path. The agents have no Bash, so they cannot run the save code.

---

## Phase Agents

### ux-researcher

**Purpose**: Do user research in the EMPATHIZE phase.

**Capabilities**:
- Interview protocol generation
- Mental model mapping
- Affinity diagramming
- Research synthesis

**Theoretical Foundation**:
- Don Norman: Emotional Design
- Alan Cooper: Goal-directed design
- Bill Moggridge: Design ethnography

**Output**: `research_findings.json`

---

### ux-artifact-generator

**Purpose**: Make UX artifacts in the DEFINE phase.

**Capabilities**:
- Persona creation
- Journey map generation
- Mental model documentation
- JTBD transformation

**Output**: `personas.json`, `journey_maps.json`, `mental_models.mmd`

---

### ux-concept-designer

**Purpose**: Make design concepts in the IDEATE phase.

**Capabilities**:
- Divergent concept generation
- HMW question formulation
- Rams principle alignment
- Concept evaluation

**Theoretical Foundation**:
- IDEO Design Thinking
- Dieter Rams: 10 Principles
- Stanford d.school methods

**Output**: `design_concepts.json`

---

### ux-prototype-builder

**Purpose**: Make wireframes and prototypes in the PROTOTYPE phase.

**Capabilities**:
- Wireframe specification
- Component definition
- Interaction pattern documentation
- Accessibility annotation

**Theoretical Foundation**:
- Bill Buxton: Sketching UX
- Brad Frost: Atomic Design
- Luke Wroblewski: Mobile First

**Output**: `wireframes.json`, `interaction_patterns.json`

---

### ux-evaluator

**Purpose**: Merge the findings of the reviewers in the TEST phase.

**Capabilities**:
- Read the findings files of the domain reviewers
- Combine their findings
- Calculate the UX health score
- Apply the weights of the project context

**Weighting Profiles**:
| Profile | Nielsen | WCAG | AI-HCI | Rams | Norman |
|---------|---------|------|--------|------|--------|
| balanced | 25% | 25% | 20% | 15% | 15% |
| ai-heavy | 20% | 20% | 35% | 10% | 15% |
| accessibility-first | 20% | 45% | 15% | 10% | 10% |
| mobile-first | 30% | 20% | 10% | 20% | 20% |
| enterprise | 30% | 30% | 10% | 10% | 20% |

**Output**: `evaluation_report.json`

---

## Domain Reviewers

### accessibility-reviewer

**Purpose**: Evaluate a design against WCAG 2.2 Level AA.

**Framework**: Web Content Accessibility Guidelines 2.2

**Evaluates**:
- The WCAG criteria of Level A and Level AA
- POUR principles (Perceivable, Operable, Understandable, Robust)
- ARIA implementation
- Keyboard accessibility

**Severity Classification**:
| Severity | WCAG Impact |
|----------|-------------|
| Critical | Level A failure |
| High | Level AA failure |
| Medium | Best practice |
| Low | Enhancement |

**Output**: `<output_dir>/findings.json` (key `findings`), for `ux-evaluator`

---

### ai-hci-reviewer

**Purpose**: Evaluate a design against the Microsoft 18 Guidelines for Human-AI Interaction.

**Framework**: Microsoft 18 Guidelines (Amershi et al., CHI 2019)

**Evaluates**:
- **Initially** (G1-G2): Capabilities, confidence
- **During Interaction** (G3-G6): Context, relevance, social norms
- **When Wrong** (G7-G11): Invocation, dismissal, correction, explanation
- **Over Time** (G12-G18): Learning, adaptation, feedback, controls

**Trust Indicators**:
- Transparency score
- Control score
- Reliability score
- Respect score

**Output**: `<output_dir>/findings.json` (key `findings`), for `ux-evaluator`

---

### usability-reviewer

**Purpose**: Evaluate a design against the Nielsen heuristics and the Rams principles.

**Frameworks**:
- Jakob Nielsen: 10 Usability Heuristics
- Dieter Rams: 10 Principles of Good Design

**Nielsen's 10 Heuristics**:
| # | Heuristic |
|---|-----------|
| H1 | Visibility of system status |
| H2 | Match between system and real world |
| H3 | User control and freedom |
| H4 | Consistency and standards |
| H5 | Error prevention |
| H6 | Recognition rather than recall |
| H7 | Flexibility and efficiency of use |
| H8 | Aesthetic and minimalist design |
| H9 | Help users recognize/recover from errors |
| H10 | Help and documentation |

**Nielsen Severity Scale**:
| Rating | Description |
|--------|-------------|
| 0 | Not a problem |
| 1 | Cosmetic |
| 2 | Minor |
| 3 | Major |
| 4 | Catastrophe |

**Output**: `<output_dir>/findings.json` (key `findings`), for `ux-evaluator`

---

## Agent Dispatch

The skill `ux-design` starts one helper for each phase with the `Skill` tool. The name is `ux-hci-design:<helper>`. A bare name finds no skill.

Each start gives the helper these fields in `args`:

| Field | Meaning |
|-------|---------|
| `project_context` | The values of `.ux-config.json` |
| `inputs` | The absolute paths of the phase inputs |
| `output_dir` | The absolute path where the agent writes its outputs |
| `method_file` | The absolute path of the skill that holds the method |

The agent reads `method_file` first.

```python
def dispatch_agent(phase, context):
    if phase == "empathize":
        return "ux-hci-design:ux-researcher"
    elif phase == "define":
        return "ux-hci-design:ux-artifact-generator"
    elif phase == "ideate":
        return "ux-hci-design:ux-concept-designer"
    elif phase == "prototype":
        return "ux-hci-design:ux-prototype-builder"
    elif phase == "test":
        # the skill starts the reviewers first, then ux-evaluator merges their findings
        return "ux-hci-design:ux-evaluator"
```

---

## Quality Criteria

All agents follow these quality criteria:

1. **Evidence-based**: Each finding links to specific components.
2. **Actionable**: Each finding has clear guidance for the fix.
3. **Prioritized**: Findings are ranked by severity.
4. **Traceable**: The audit trail is complete.
5. **Framework-aligned**: Each finding cites an established theory.

---

## Usage

A person starts the helpers through the skill `/ux-hci-design:ux-design`. The plugin has 13 skills for a person. Each one is `/ux-hci-design:<skill>`.

```bash
# Run full workflow
/ux-hci-design:ux-design

# Run specific phase
/ux-hci-design:ux-design empathize
/ux-hci-design:ux-design define
/ux-hci-design:ux-design ideate
/ux-hci-design:ux-design prototype
/ux-hci-design:ux-design test

# Quick evaluation
/ux-hci-design:ux-design evaluate-heuristics
```

The other arguments of the skill are `integrate`, `accessibility-audit`, `generate-persona`, and `journey-map`.
