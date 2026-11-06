# Healthcare Portal Example: Patient Appointment System

This example shows the complete UX/HCI Design workflow for a healthcare patient portal with strict accessibility requirements.

## Project Context

- **Product**: MedConnect, a patient healthcare portal
- **Target Users**: Patients of all ages and abilities
- **Platform**: Web (responsive), accessible
- **Weighting Profile**: `accessibility-first` (20% Nielsen, 45% WCAG, 15% AI-HCI, 10% Rams, 10% Norman)

## Compliance Requirements

- WCAG 2.2 Level AA (mandatory)
- Section 508 compliance
- HIPAA rules for patient health data
- Support for several languages

## Workflow Summary

### Phase 1: EMPATHIZE

The research found these needs:
- Elderly patients with vision or motor difficulties
- Caregivers who manage several family members
- Users who rely on assistive technology
- Users who are not native English speakers

### Phase 2: DEFINE

The workflow made these personas and this journey map:
- Primary persona: "Grandmother Eleanor" (accessibility focus)
- Secondary persona: "Caregiver Maria"
- Journey map: the appointment scheduling flow

### Phase 3: IDEATE + PROTOTYPE

The team explored three design concepts:
1. High-contrast design with large text by default
2. Adaptive interface with personalization
3. Voice-enabled appointment booking

The team chose Concept 1 with some elements of Concept 2.

### Phase 4: TEST

Evaluation results:
- **UX Health Score**: 88/100 (Grade B)
- **Nielsen**: 85%
- **WCAG**: 94% (strong Level AA compliance)
- **AI-HCI**: 80% (few AI features)
- **Rams**: 82%

## Artifacts

```
healthcare-portal/
├── .ux-config.json
├── personas/
│   └── persona-eleanor.json
├── journey-maps/
│   └── appointment-journey.json
├── prototypes/
│   └── wireframe-appointment.json
└── evaluation/
    └── evaluation-report.json
```

The file `.ux-config.json` holds the project context. The skill `ux-design` reads this file. When the file exists, the skill asks no context question.

## Accessibility Focus

This example stresses WCAG 2.2 Level AA compliance.

### Key Design Decisions

1. **1.4.3 (Contrast)**: Body text has a contrast ratio of 7:1 or more.
2. **2.1.1 (Keyboard)**: The team tested that the keyboard operates all functions.
3. **2.4.7 (Focus Visible)**: Focus indicators have high contrast.
4. **2.5.8 (Target Size)**: Touch targets are at least 44x44 px.
5. **3.3.7 (Redundant Entry)**: Forms fill in known data by themselves.
6. **3.3.8 (Accessible Authentication)**: Log-in needs no cognitive test.

## Running the Workflow

Start Claude Code in the folder `plugins/ux-hci-design/examples`. Then run these commands.

```bash
/ux-hci-design:ux-design empathize healthcare-portal/
/ux-hci-design:ux-design define healthcare-portal/
/ux-hci-design:ux-design ideate healthcare-portal/
/ux-hci-design:ux-design prototype healthcare-portal/
/ux-hci-design:ux-design test healthcare-portal/
```

## Key Learnings

1. **Accessibility helps everyone**: Large text and clear contrast help all users.
2. **Error prevention is critical**: A confused patient can miss an appointment.
3. **Progressive disclosure reduces mental load**: Show only the essential options first.
4. **Tests with real users are essential**: Automated tests find only 30% of the issues.
