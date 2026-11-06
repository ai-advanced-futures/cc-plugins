# ADR-004: P15 Trigger Detector

**Status:** Accepted
**Date:** 2026-05-30 (rewritten for the port, 2026-11-05)
**Earlier ADR:** ADR-003 (the cost-amplifier-readout producer)

## Context

ADR-003 gave the plugin a way to compose cost amplifiers into a LogNormal. The plugin could not yet detect that a contracted threshold was crossed.

This ADR adds the detection. The result is the file `p15-trigger-event.json`. Its schema is `schemas/p15-trigger-event.schema.json`. A `trigger_kind` key sets the kind of each event: `cost_rate_breach` or `quality_floor_breach`. The gtm and pricing plugins read the file.

## Decisions

**D1.** One schema holds two trigger kinds. The key `trigger_kind` (`cost_rate_breach`, `quality_floor_breach`) tells them apart. Both kinds share the envelope fields. Each kind has its own `computed` and `contracted` blocks. The JSON Schema uses `oneOf` with a constant for `trigger_kind`.

**D2.** The quality fields go into the existing input schema, `amplifier-telemetry-input` 1.0.0 → 1.1.0. Two optional blocks are new: `quality_metrics[]` and `contractual_thresholds`. A file of version 1.0.0 stays valid for version 1.1.0.

**D3.** The threshold comes from the first of these sources that has a value. For quality: the command line, then the `contractual_thresholds` of the input, then the `contracted_floor` of the entry in `quality_metrics[]`. For cost: the first two. If detection needs a threshold and no source has one, the loader raises `NoThresholdsResolvedError`.

**D4.** The detector keeps no state. An optional history file holds the earlier inputs. It is a JSON array of `amplifier-telemetry-input` 1.1.0 objects, and it has no schema of its own. Without a history, the cost-rate detection is skipped, because one point gives no rate. The quality-floor detection still runs.

**D5.** The file has an array of events. The gtm plugin and the pricing plugin read it. The plugin also keeps it for its own audit.

**D6.** There is a new specialist: `p15-trigger-detector-agent` and the skill `/aiml:p15-trigger-detection`. The agent uses `haiku`, has the tools `[Bash, Read, Write]`, and ends with `DONE: aiml`. It has no `AskUserQuestion`.

**D7.** The schema is in `schemas/p15-trigger-event.schema.json`, with the other schemas of the plugin.

**D8.** The severity bands follow the miss band of the clause: minor [0, 15), major [15, 50), critical [50, ∞). The limit 50 is new in this ADR. A test pins the edges. The upper limit 100 is not enforced.

**D9.** The three new scripts (`p15_trigger_input_loader.py`, `p15_trigger_detector.py`, `p15_trigger_emitter.py`) do not import from the pricing plugin. `test_no_pricing_lib_imports.py` checks this for each file of `scripts/`.

**D10.** The detector is a pure function. It does no input or output. The loader reads. The emitter writes. The detector returns `(events, detection_notes)`.

**D11.** A missing threshold is an error, not a zero. The loader raises `NoThresholdsResolvedError` with a clear name.

**D12.** The history file uses the schema of ADR-003. There is no new history schema.

**D13.** `inputs_hash` is `sha256(_canonical_json_bytes(current) + _canonical_json_bytes(history))`. `_canonical_json_bytes(obj)` is `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`. A missing or empty history gives `b""`. The hash covers the full history that the person gave.

**D14.** The baseline of an amplifier is the median of its samples inside the window. The median resists outliers better than the mean.

## Consequences

**Possible now:**
- `/aiml:p15-trigger-detection` writes a trigger file that a program can read.
- The schema lets another plugin validate the file.
- One input shape serves both the cost-rate and the quality-floor detection.
- `inputs_hash` lets a person repeat a run and compare the result.

**Not yet done:**
- A plugin that reads the file and starts a remedy or a message to a customer.
- A collector that fills the input file from a monitoring system.

## Alternatives considered

**A schema inside the plugin that no other plugin can find.** Rejected: the plugins that read the file need a schema in a known place. The schema is in `schemas/` of the plugin.

**Ship the cost kind first.** Rejected: the quality-floor trigger is a main feature of the detector.
