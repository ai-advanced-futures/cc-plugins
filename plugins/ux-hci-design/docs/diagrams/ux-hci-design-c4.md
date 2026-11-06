# ux-hci-design C4 Architecture Diagram

## Context Level

This level shows how the person and the plugin `ux-hci-design` work with the other plugins.

```
[Designer / Product Team] --> [ux-hci-design Plugin] : starts /ux-hci-design:ux-design
[ux-hci-design Plugin] --> [developer agent] : implementation-ready handoff
[ux-hci-design Plugin] --> [prd plugin] : receives PRD-to-design bridge inputs
[ux-hci-design Plugin] --> [jtbd-market-discovery plugin] : receives JTBD opportunity data
```

## Container Level

This level shows the agents, skills, and schemas inside the plugin.

### Agents (execution layer)

A skill starts an agent with the name `ux-hci-design:<agent>`. An agent cannot ask the person a question.

| Agent | Model | Role |
|-------|-------|------|
| `ux-researcher` | sonnet | EMPATHIZE: user research, Track 3 handoff decisions |
| `ux-concept-designer` | sonnet | IDEATE: concept generation, Handoff-Complete criterion |
| `ux-prototype-builder` | sonnet | PROTOTYPE: wireframes, specifications with accessibility notes |
| `ux-evaluator` | sonnet | TEST: merges the findings of the 3 reviewers and writes the evaluation report |
| `ux-artifact-generator` | sonnet | DEFINE: personas, journey maps, mental models |
| `accessibility-reviewer` | haiku | WCAG 2.2 Level AA audit |
| `ai-hci-reviewer` | haiku | Microsoft 18 Guidelines audit |
| `usability-reviewer` | haiku | Nielsen 10 Heuristics evaluation |

### Skills (entry points)

| Skill | Command | Purpose |
|-------|---------|---------|
| `ux-design` | `/ux-hci-design:ux-design` | Main orchestrator: the full Design Thinking workflow |
| `empathize` | `/ux-hci-design:empathize` | Method of the EMPATHIZE phase |
| `define` | `/ux-hci-design:define` | Method of the DEFINE phase: persona and journey synthesis |
| `ideate` | `/ux-hci-design:ideate` | Method of the IDEATE phase: concept generation |
| `prototype` | `/ux-hci-design:prototype` | Method of the PROTOTYPE phase: wireframes |
| `ux-evaluate` | `/ux-hci-design:ux-evaluate` | Method of the TEST phase: heuristic evaluation |
| `accessibility-audit` | `/ux-hci-design:accessibility-audit` | WCAG audit |
| `ai-hci-audit` | `/ux-hci-design:ai-hci-audit` | AI-HCI audit |
| `jtbd-bridge` | `/ux-hci-design:jtbd-bridge` | JTBD to UX artifact bridge |
| `prd-bridge` | `/ux-hci-design:prd-bridge` | PRD to design specification bridge |

### Schemas (validation layer)

- `schemas/outputs/`: JSON schemas for all UX deliverables (design-concept, evaluation-report, persona, journey-map, wireframe, and others)
- `schemas/heuristics/`: Nielsen 10, Dieter Rams 10, Norman interaction principles
- `schemas/accessibility/`: WCAG 2.2 criteria
- `schemas/ai-hci/`: Microsoft 18 Guidelines
- `schemas/ai-paradigm/`: AI-native UX patterns
