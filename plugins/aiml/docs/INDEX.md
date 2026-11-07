# AIML Plugin — Documentation Index

## Architecture

- [ADR-001: Plugin Architecture](adr/ADR-001-plugin-architecture.md) — the pipeline, the model tiers, the artifact paths
- [ADR-002: Agent Patterns](adr/ADR-002-agent-patterns.md) — skills only, parallel small agents, who asks the person, model tiers
- [ADR-003: Telemetry-Enriched Cost-Amplifier Readout](adr/ADR-003-charter-readout-producer.md) — both readout modes together, the three modules, the golden values
- [ADR-004: P15 Trigger Detector](adr/ADR-004-p15-trigger-detector.md) — 14 decisions for the `p15-trigger-event.json` producer (cost rate and quality floor)
- [ADR-005: Archetype Baseline Telemetry](adr/ADR-005-archetype-baseline-telemetry.md) — the producer of measured archetype baselines, with median aggregation
- [C4 Context Diagram](c4/context.md) — who uses aiml and how
- [C4 Container Diagram](c4/container.md) — skills, agents, scripts and `.aiml/handoff.json`

## Knowledge Sources

The agents use ideas from these works:

| Source | Used by |
|---|---|
| Géron — Hands-on ML Ch.1 (ML landscape) | decision-agent |
| Géron — Ch.2 (end-to-end ML project) | design-agent, plan-agent |
| Géron — Ch.3 (classification metrics) | evaluate-agent |
| Géron — Ch.11 (training deep nets, hyperparams) | tune-agent, simulator-agent |
| Iusztin & Labonne — LLM Engineer's Handbook | design-agent, scaffold-agent, tune-agent, ops-agent |
| "Attention Is All You Need" (Vaswani et al. 2017) | design-agent |
| Karpathy — Software 2.0, LLM OS | decision-agent, ops-agent |
| Chip Huyen — ML Engineering Lifecycle | decision-agent, design-agent |
| Andrew Ng — Data-Centric AI | design-agent, evaluate-agent, simulator-agent |
| Lilian Weng — agent taxonomy | design-agent |
