# Agentic Pricing — Canonical Schemas

This directory ships the schema-coupled federation contracts from the JustKeenAI Agentic Pricing Charter v1.0.0.

> Based on JustKeenAI Agentic Pricing Framework v2.1 (2026-05-13).
> See `ATTRIBUTION.md` in the plugin folder for license and version-tracking.

## Contents

| File | Purpose |
|---|---|
| `vocabulary.yaml` | Internal-only / customer-facing / bidirectional term dictionaries + allowlist contexts (Charter §5.1.1) |
| `vocabulary.schema.json` | JSON Schema (Draft-07) for vocabulary.yaml |
| `pattern_catalogue.yaml` | P1–P19 + P12-Light reference data (Charter §7.9) |
| `pattern_catalogue.schema.json` | JSON Schema for pattern_catalogue.yaml |
| `agentic-pricing-diagnosis.schema.json` | Producer: pricing. Consumers: contract tools and finance tools. Audience: mixed (Charter §7.2) |
| `cost-amplifier-readout.schema.json` | Producer: pricing (RoT) / aiml (telemetry). Consumers: architecture tools and finance tools. Audience: internal (Charter §7.3) |
| `pattern-selection.schema.json` | Producer: pricing. Consumers: contract tools and workflow tools. Audience: mixed (Charter §7.4) |
| `clause-package.schema.json` | Producer: contract tools. Consumers: pricing and workflow tools. Audience: mixed (jurisdiction_notes fenced internal) (Charter §7.5) |
| `cost-coverage-readout.schema.json` | Producer: finance tools. Consumers: workflow tools. Audience: internal (Charter §7.6) |
| `sales-comp-precondition-gate.schema.json` | Producer: go-to-market tools. Consumers: workflow tools. Audience: internal (Charter §7.7) |
| `agentic-pricing-transition-phase-status.schema.json` | Producer: workflow tools. Consumers: all. Audience: internal (Charter §7.8) |

## Versioning

All schemas ship at `schema_version: "1.0.0"` per Charter §15.2.0. SemVer 1.x stability rules apply from day one. Schema version bumps follow Charter §15.2.

## Linter

The vocabulary linter that enforces the vocabulary.yaml dictionaries against agent files and handoff artifacts is the package `vocabulary_linter/` of this plugin. See Charter §5.3 / §5.3.1 / §5.3.2.

## Pattern definitions

See `pattern_catalogue.yaml` for the canonical P1–P19 + P12-Light definitions. Pricing-core sub-spec (pricing v1.4.0) will promote this YAML into `plugins/pricing/lib/pattern_catalogue.py` and expose the stable `PATTERN_IDS` symbol via `plugins/pricing/lib/charter_exports.py`.
