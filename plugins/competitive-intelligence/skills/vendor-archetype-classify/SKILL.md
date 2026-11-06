---
name: vendor-archetype-classify
description: Classifies the current pricing of a vendor into one of the 5 canonical agentic-pricing archetypes. Use when the person wants to know which archetype the pricing page of a vendor maps to, or wants to refresh the Wave 1 vendor registry.
---

# Vendor Archetype Classification

This skill classifies the current pricing model of a vendor into one of the five canonical vendor archetypes (JustKeenAI v2.1 Chapter 1). You run in the main conversation, so you ask the person. The agent `competitive-intelligence:vendor-archetype-classifier-agent` cannot ask.

## When to use

- Classify a single vendor's pricing page → archetype.
- Audit / refresh the 22-vendor Wave 1 seed registry (`definitions/wave1-vendors.json`).

## How it works

1. Ask the person for the vendor name and its pricing page with `AskUserQuestion`, unless the person already gave them. The page is a URL or a pasted text. For a registry refresh, read `${CLAUDE_PLUGIN_ROOT}/definitions/wave1-vendors.json`, ask which vendors to refresh, and use the `vendor_name` and `pricing_page_url` of each.
2. Dispatch `competitive-intelligence:vendor-archetype-classifier-agent` with the `Agent` tool. Give it `vendor_name`, and `pricing_page_url` or `pricing_page_text`. Wait for it to finish.
3. The agent extracts seven boolean pricing signals from the vendor's pricing page.
4. The deterministic Python classifier (`scripts/vendor_archetype_classifier.py`) maps the signals to one of: `pure_outcome_absorbed`, `hybrid_platform_outcome`, `pure_per_seat` (+ `seat_anchor`), `hybrid_seat_meter`, `pure_passthrough`.
5. The emitter writes `.competitive-intelligence/vendor-archetype-classification.json` (the federation artifact, `audience: mixed`) and a handoff file.
6. Read `.competitive-intelligence/vendor-archetype-handoff.json`. Show the person the `state`. For `success`, show the archetype and the `best_in_class_pattern`. For `blocked` or `error`, show the `reason`.

If the agent returns `QUESTIONS: <path>`, read the file and ask each question. Then dispatch the agent again with the answers added as dispatch fields.

Take the archetype from the classifier output, because the classifier is a deterministic script.

See `reference/archetype-reference-card.md` for the signal rubric and the 5-archetype definitions with framework citations.
