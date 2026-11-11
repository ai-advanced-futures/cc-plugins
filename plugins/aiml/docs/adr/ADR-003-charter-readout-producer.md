# ADR-003 — Telemetry-enriched cost-amplifier-readout producer

**Status:** Accepted (2026-05-22, rewritten for the port, 2026-11-05)

## Context

- The plugin is the producer of `cost-amplifier-readout` in `mode: telemetry_enriched`. Its schema is `schemas/cost-amplifier-readout.schema.json`. The input schema is `schemas/amplifier-telemetry-input.schema.json`.
- The plugin must not import code from another plugin. It writes its own LogNormal math.
- Before this decision, a readout built from framework defaults (`rule_of_thumb`) was the only readout. A measured readout was needed next to it.

## Decision

1. **Both modes exist together.** A telemetry-enriched readout and a rule-of-thumb readout stay side by side. Neither has precedence. A reader picks one, based on the data it has.
2. **A new skill and agent pair.** `/aiml:cost-amplifier-readout` starts `cost-amplifier-readout-agent`.
3. **Three Python modules.** `amplifier_telemetry_loader.py` → `amplifier_composer.py` → `cost_amplifier_readout_emitter.py`. The emitter is the one command-line entry point. The skill runs it, before it starts the agent, with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/cost_amplifier_readout_emitter.py`. The agent has no `Bash`: it reads the output file and writes the handoff (D-266).
4. **The input schema is in `schemas/`.** `amplifier-telemetry-input.schema.json` describes the raw telemetry. A file that a person writes by hand is valid input.
5. **One `AmplifierReading` dataclass.** It has 6 fields: `amp_id, multiplier_p75, multiplier_p95, sample_size_n, detection_signal, present`. It is in `amplifier_telemetry_loader.py`. The composer uses it as it is, and ignores `sample_size_n` and `detection_signal` in the math. The result type `AmplifierCompositeResult` stays in the composer. The test `test_no_pricing_lib_imports.py` walks `scripts/` and `tests/` and fails on any `import pricing*` or `from pricing*`.
6. **Conformance test first, sentinel second.** The test of the output schema lands in the same commit as, or before, the file `.charter-conforms` that names the schema.
7. **The agent uses haiku.** It runs scripts and fills a template for the notes. It needs no deep reasoning.
8. **`.charter-conforms` states a role for each schema.** `cost-amplifier-readout: produces` and `amplifier-telemetry-input: produces`. A producer is also the reader of its input, so a `consumes` line for the input is not needed.
9. **The framework name is in the `notes` field.** Both fixture schemas have `additionalProperties: false`, so a top-level `framework_citation` key would fail. The text `JustKeenAI v2.1` is in `notes`.
10. **A `notes` text of more than 2000 characters raises `ValueError`.** The script does not cut the text without a sign.
11. **The emitter writes `produced_at` itself.** The value is the UTC time of the write, not a value from the input. The time of the telemetry window stays in the input `measurement_window` and appears in `notes`.
12. **Tests cover `tests/unit/` and run in one CI job.** The job `aiml` of `.github/workflows/ci.yml` runs `pytest tests/` in `plugins/aiml`, with the packages of `requirements-dev.txt`. A skipped test for a missing package fails the job.
13. **A fixture holds the golden values.** `tests/fixtures/agentic-pricing/composer-golden-values.json` holds the expected result of the composer for 5 scenarios (1 amplifier, 3 amplifiers, all 8 present, all absent, P75 equal to P95). The composer test checks all five result fields. The test fails when the file or a scenario is missing.
14. **`present_amplifiers` keeps the order of the input.** The composer returns `[r.amp_id for r in present]`. A Python dict keeps the order of insertion, and the loader builds the dict in the order of the JSON object. The test checks the list against the scenario and against the golden file. The count of present amplifiers is in `notes`.

## Consequences

- **Positive:** the pattern of one loader, one composer and one emitter is set for the next producers. No other plugin is a dependency.
- **Negative:** about 80 lines of LogNormal math are the same in the pricing plugin and here. The plugin cannot share code with it, so a copy is the cost.
- **Risk control:** the golden-value tests check that the numbers equal the reference for 5 scenarios. The import test stops a later change from adding a dependency.
- **Later:** the P15 trigger detector (ADR-004) and the archetype baseline (ADR-005) use the same pattern.
