# Competitive Intelligence Documentation

This page lists the documents of the competitive-intelligence plugin.

## Architecture Decision Records (ADRs)

An ADR is the record of one design decision.

| ADR | Title | Version |
|-----|-------|---------|
| [ADR-001](adr/ADR-001-competitive-intelligence-plugin-architecture.md) | Plugin architecture: agent pipeline, six lenses, file-based protocol, session scoping, summary pattern, questions in skills, Python and LLM split | 1.0.0 to 1.1.0 (amended 1.3.0 to 1.7.0) |
| [ADR-002](adr/ADR-002-vendor-archetype-classifier.md) | Vendor archetype classifier | 1.2.0 |
| [ADR-003](adr/ADR-003-trigger-mode-taxonomy.md) | Trigger and mode taxonomy: four triggers, two analysis modes | 1.5.0 |
| [ADR-004](adr/ADR-004-plugin-result-file.md) | Plugin result file: two thin runners, one writer, a session for each run | 1.6.0 |

## Design

- [DESIGN.md](DESIGN.md) - the design of the plugin

## C4 Diagrams

- [C4 Context](diagrams/competitive-intelligence-c4-context.md) - the people and the plugins around this plugin
- [C4 Container](diagrams/competitive-intelligence-c4-container.md) - the skills, the agents, the scripts, and the session folder
