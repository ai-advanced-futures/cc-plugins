# AI SaaS Product Example: Code Assistant Interface

This example shows the complete UX/HCI Design workflow for an AI code assistant interface, like Claude Code.

## Project Context

- **Product**: CodeMate AI, an AI coding assistant
- **Target Users**: Software developers of all experience levels
- **Platform**: Desktop application with a web interface
- **Weighting Profile**: `ai-heavy` (20% Nielsen, 20% WCAG, 35% AI-HCI, 10% Rams, 15% Norman)

## Workflow Summary

### Phase 1: EMPATHIZE

The research found these needs of developers:
- They need to see how sure the AI is.
- They want control over the AI suggestions.
- They dislike "magic" AI that cannot explain itself.
- They need an easy way to correct AI mistakes.

### Phase 2: DEFINE

The workflow made these personas and this journey map:
- Primary persona: "Senior Developer Alex"
- Secondary persona: "Junior Developer Jamie"
- Journey map: the AI-assisted code review flow

### Phase 3: IDEATE + PROTOTYPE

The team explored three design concepts:
1. Inline AI suggestions with confidence badges
2. Side-panel AI assistant with full control
3. Conversational AI with code context

The team chose Concept 2 with some elements of Concept 1.

### Phase 4: TEST

Evaluation results:
- **UX Health Score**: 78/100 (Grade C)
- **Nielsen**: 82%
- **WCAG**: 75%
- **AI-HCI**: 80% (17/18 guidelines addressed)
- **Rams**: 76%

## Artifacts

```
ai-saas-product/
├── .ux-config.json
├── personas/
│   └── persona-alex.json
├── journey-maps/
│   └── code-review-journey.json
├── prototypes/
│   └── wireframe-ai-assistant.json
└── evaluation/
    └── evaluation-report.json
```

The file `.ux-config.json` holds the project context. The skill `ux-design` reads this file. When the file exists, the skill asks no context question.

## AI-HCI Focus

This example stresses the Microsoft 18 Guidelines for Human-AI Interaction.

### Key Design Decisions

1. **G1 (Capabilities)**: The onboarding explains what the AI can and cannot do.
2. **G2 (Confidence)**: Each AI suggestion shows a confidence indicator.
3. **G8 (Dismissal)**: One click dismisses any AI output.
4. **G9 (Correction)**: The person edits an AI suggestion in place.
5. **G11 (Explanation)**: The "Why?" button shows the reasoning of the AI.
6. **G17 (Global Controls)**: The AI settings panel has fine controls.

## Running the Workflow

Start Claude Code in the folder `plugins/ux-hci-design/examples`. Then run these commands.

```bash
/ux-hci-design:ux-design empathize ai-saas-product/
/ux-hci-design:ux-design define ai-saas-product/
/ux-hci-design:ux-design ideate ai-saas-product/
/ux-hci-design:ux-design prototype ai-saas-product/
/ux-hci-design:ux-design test ai-saas-product/
```

## Key Learnings

1. **AI transparency is a must**: Developers want to understand the reasoning of the AI.
2. **Control builds trust**: Easy correction and dismissal increase use of the AI.
3. **Context matters**: An AI suggestion must relate to the current task.
4. **Progressive disclosure works**: Start with a simple view. Show more detail when the person asks.
