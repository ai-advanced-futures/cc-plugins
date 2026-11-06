# ADR-003: Tiered Detectors

**Status:** Accepted

## Context

No one signal finds AI text reliably. The plugin can use three kinds of detector:

- **Free stdlib heuristics** (burstiness, type-token ratio, phrase tells). They are always available. Alone, they are weak.
- **Local HuggingFace models.** They are stronger. They need optional heavy dependencies (`torch`, `transformers`) and local compute.
- **Commercial APIs** (GPTZero, Originality.ai, Sapling). They are the strongest. They cost money, need API keys, and send text to a third party. This action needs consent.

The plugin needs one design that joins these tiers to give one verdict. The design must not hide the large differences in reliability and availability between the tiers.

## Decision

There are three fixed tiers:

- `heuristics` is always on.
- `hf` is opt-in and local.
- `api` is opt-in and needs consent.

Each tier reports scores on the same canonical scale of composite points, from 0 to 100. The scale is in `lib/verdicts.py`, for example `pass_max_composite = 50.0`. The thresholds are comparable across tiers, although the detectors differ.

- **UNAVAILABLE is a first-class tier status.** It is not the same as a low or PASS score.
  - A tier is unavailable when no detector in it ran successfully. The cause can be a missing dependency, an absent API key, or no consent.
  - An unavailable tier reports `UNAVAILABLE`. The verdict computation drops it.
  - It does not score as 0, because 0 would read as "confidently human".
- **The precedence does not change. The run evaluates it at the start.** The order is `api > hf > heuristics`.
  - The final verdict is the verdict of the strictest *available* tier.
  - It is never a "worst across all tiers" aggregate or a count of detectors that spans many tiers. The tier boundaries never blur.
  - `run_detectors.py` finds which tiers are available once, at the start of a run. It does not do this in each iteration.
- **The consent pre-flight is deterministic. It is not agent judgment.**
  - The script `run_detectors.py` decides if the `api` tier can run. It checks the recorded consent and the environment keys.
  - It does this before any text leaves the process.
  - An agent never decides on the fly if it is acceptable to send text to a commercial API.

## Consequences

- `config/detectors.yaml` is the single source of truth for the detector list and the thresholds. It mirrors `DEFAULT_THRESHOLDS` in `lib/verdicts.py`. The doc-contract test `test_detectors_yaml_thresholds_match_verdicts_defaults` checks that the two match. This is a contract between prose and Python constants.
- To add, retire, or reclassify a detector is an edit of `config/detectors.yaml`. It is not a code change. An example is the `desklib` model. It has `status: excluded`, because it has a 0.655 false-positive rate on known-human PE writing.
- A run can degrade to `heuristics` only, because `hf` and `api` are unavailable. It still produces a verdict and never fails hard. The verdict output always reports the degradation. It is never silent.
- `single_fail_above` (70.0) applies only to tiers with a single detector (`heuristics`). `multi_fail_count` (2) applies to tiers with 2 or more detectors (`hf`, `api`). The two FAIL rules are structurally different. Do not mix them when you add a detector to a tier.
