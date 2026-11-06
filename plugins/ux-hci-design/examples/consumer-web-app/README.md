# Consumer Web App Example: E-commerce Checkout Flow

This example shows the complete UX/HCI Design workflow for the redesign of an e-commerce checkout flow.

## Project Context

- **Product**: ShopEasy, an online retail platform
- **Target Users**: General consumers, ages 25 to 65
- **Platform**: Web (responsive)
- **Weighting Profile**: `mobile-first` (30% Nielsen, 20% WCAG, 10% AI-HCI, 20% Rams, 20% Norman)

## Workflow Summary

### Phase 1: EMPATHIZE

User interviews found these pain points in the current checkout:
- 47% of carts are abandoned at the payment step.
- Users are confused about the shipping options.
- The guest checkout is hard to find.

### Phase 2: DEFINE

The workflow made these personas and this journey map from the research:
- Primary persona: "Busy Parent Sarah"
- Secondary persona: "Tech-Savvy Student Marcus"
- Journey map: a checkout flow with 7 stages

### Phase 3: IDEATE + PROTOTYPE

The team explored three design concepts:
1. Single-page express checkout (Rams-aligned)
2. Step-by-step wizard with progress
3. AI-assisted smart checkout

The team chose Concept 1 with progressive disclosure.

### Phase 4: TEST

Evaluation results:
- **UX Health Score**: 82/100 (Grade B)
- **Nielsen**: 85% (no catastrophes)
- **WCAG**: 88% (Level AA compliant)
- **Rams**: 80% (strong on "Useful" and "Minimal")

## Artifacts

```
consumer-web-app/
├── .ux-config.json          # Project configuration
├── personas/
│   └── persona-sarah.json   # Primary persona
├── journey-maps/
│   └── checkout-journey.json
├── prototypes/
│   └── wireframe-checkout.json
└── evaluation/
    └── evaluation-report.json
```

The file `.ux-config.json` holds the project context. The skill `ux-design` reads this file. When the file exists, the skill asks no context question.

## Running the Workflow

Start Claude Code in the folder `plugins/ux-hci-design/examples`. Then run these commands.

```bash
/ux-hci-design:ux-design empathize consumer-web-app/
/ux-hci-design:ux-design define consumer-web-app/
/ux-hci-design:ux-design ideate consumer-web-app/
/ux-hci-design:ux-design prototype consumer-web-app/
/ux-hci-design:ux-design test consumer-web-app/
```

## Key Learnings

1. **Mobile-first matters**: 68% of users shop on a mobile device.
2. **Trust signals are critical**: Security badges reduced cart abandonment.
3. **Progressive disclosure works**: Users preferred a simple first view.
4. **Accessibility gives better UX**: The WCAG improvements helped all users.
