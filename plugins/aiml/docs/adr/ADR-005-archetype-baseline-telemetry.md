# ADR-005 — Archetype Baseline Telemetry

| | |
|---|---|
| Status | Accepted |
| Date | 2026-05-31 (rewritten for the port, 2026-11-05) |
| Source of the context | JustKeenAI Agentic Pricing Framework v2.1 |

## Context

The pricing plugin has 3 archetype baselines that it infers. It needs measured baselines in their place. This ADR adds the producer of the measured baselines.

## Decisions

1. **Two schemas.** The input is `schemas/archetype-cost-samples.schema.json`: raw `cost_samples[]` from a collector. The output is `schemas/archetype-baseline-telemetry.schema.json`: the reduced `baseline_cost_per_interaction`. Raw telemetry is a first-class input, as in ADR-003.
2. **Median.** The script uses `statistics.median` for each archetype, as ADR-004 (D14) does. The median resists outliers in the cost of one interaction. The output records `aggregation: "median"`, so a reader can audit it.
3. **Three modules.** A loader, a pure aggregator, and a command-line emitter, as in ADR-003 and ADR-004. The aggregator does no input or output. The loader keeps the envelope fields in `ArchetypeCostSamples`.
4. **The plugin does not know which archetypes matter.** The aggregator writes all archetypes that are present. The schema accepts 6. The pricing plugin picks the 3 that it can override. The producer does not hold the rule of the pricing plugin.
5. **`exclusiveMinimum: 0` on a cost sample and on a baseline.** The input rejects a sample of 0. So a median of 0 cannot occur, and it cannot set a downstream cost to 0.
6. **Two exit codes in the emitter.** Exit 1 is an input problem. Exit 2 is a fault in the output logic, as in ADR-003.
7. **`produced_at` is the time of the write.** It is not copied from the input.
8. **`measurement_window` and `telemetry_source` pass through.** The output of the P15 trigger detector has no `measurement_window`. This output has it, so that the pricing plugin can audit the window.
9. **The shared `_jsonschema_formats` module is reused.** There is no new format module.

## Consequences

- The pricing plugin can use the measured baselines in place of its inferred baselines when the file `.aiml/archetype-baseline-telemetry.json` exists.
- The plugin has 11 agents, 12 skills and 14 scripts.

## Cross-references

- Schemas: `schemas/archetype-cost-samples.schema.json`, `schemas/archetype-baseline-telemetry.schema.json`
- Producer: `scripts/archetype_baseline_*.py`
- Skill and agent: `skills/archetype-baseline-telemetry/SKILL.md`, `agents/archetype-baseline-telemetry-agent.md`
