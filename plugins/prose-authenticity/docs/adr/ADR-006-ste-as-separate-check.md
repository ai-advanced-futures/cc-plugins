# ADR-006: STE conformance is a separate check, not a fourth detector tier

**Status:** Accepted
**Date:** 2026-07-29

## Context

The plugin has three detector tiers: `heuristics`, `hf`, and `api`. All of the tiers ask one question: did a machine write this text? They report on the same composite scale of 0 to 100. The scale is in `lib/verdicts.py`.

ASD-STE100 conformance asks a different question. Does the text follow a rule set?

A measured run showed that the two questions differ. One proposal had none of the 13 AI tells and yet broke two of the STE rules. The tell-check did not find the breaks.

## Decision

The STE checker is its own module. It has its own verdict and its own config file. It never writes into the detector composite.

## Consequences

To get both answers, you must run both checks. This is the intended cost. It is not possible to hold two measurements in one number.

The checker uses `config/ste.yaml`. It does not extend `config/detectors.yaml`. A change to a threshold on one side then never moves the threshold on the other side.

Both `lib/ste_checker.py` and `lib/run_detectors.py` emit a top-level `verdict` key. Both use the same `{PASS, WARN, FAIL}` enum. The scales differ. One scale measures how well the text follows the rules. The other measures the chance that a machine wrote the text.

A combined report must not merge the two outputs with a plain `dict.update()`. That call is unsafe. One verdict would silently replace the other.

A future combined report must rename the keys first: `ste_verdict` for the STE output and `detector_verdict` for the detector output.

This ADR records the naming convention. The `verdict` key in both modules stays as it is until a combined report exists.
