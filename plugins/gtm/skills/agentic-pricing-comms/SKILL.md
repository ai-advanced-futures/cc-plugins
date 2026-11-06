---
name: agentic-pricing-comms
description: Six stakeholder communication templates for an agentic-pricing transition (Board, CFO, CS, Sales, Customer announcement, Internal FAQ) with the operator-grade-vs-Predictability-Architecture vocabulary rule. Auto-selects templates from a p15-trigger-event artifact.
audience: mixed
---

# Agentic-Pricing Stakeholder Comms

Generate stakeholder communications for an agentic-pricing rollout (JustKeenAI
framework v2.1 Chapter 5). Six templates live in `templates/`, one per audience.

## Vocabulary rule (load-bearing)

Operator-grade terms (`shared risk`, `transition`, `cost-coverage`, `vendor margin`,
`margin compression`, `amplifier`) are for internal use only. The customer hears `predictable cost`, `hard ceilings`,
`value floors`, `quality assurance`. Mixing the two vocabularies destroys the framing (the Cursor failure).
Template #5 (Customer announcement) uses Predictability-Architecture vocabulary
only. `${CLAUDE_PLUGIN_ROOT}/scripts/comms_vocabulary.py::check_customer_vocabulary` checks its source files at
test time. It does not check copy that a model writes.

## Auto-comms from a P15 trigger

Given a `p15-trigger-event.json` artifact (produced by the plugin `aiml`), validate it
against `${CLAUDE_PLUGIN_ROOT}/schemas/p15-trigger-event.schema.json`, then map each event's `trigger_kind` to a
template set via `${CLAUDE_PLUGIN_ROOT}/scripts/comms_router.py::select_templates`:
- `quality_floor_breach` → #5 Customer-announcement + #6 Internal-FAQ
- `cost_rate_breach` → #2 CFO + #1 Board

Show `severity` inside the draft. It has no effect on which templates the router selects.
Empty `events` → no comms. The optional envelope `detection_notes` is ignored.
