# ADR-002: Vendor Archetype Classifier

**Status:** Accepted
**Date:** 2026-06-01
**Plugin:** competitive-intelligence 1.2.0 (amended 1.7.0)

---

## Context

The plugin classifies the pricing of a vendor into one of five archetypes. It uses a
deterministic classifier. The classifier maps the pricing signals of a vendor onto the
JustKeenAI v2.1 Chapter-1 "Five vendor archetypes in market today" taxonomy.

The implementation is three Python modules in `scripts/`:

- `vendor_archetype_classifier.py` - pure classification (`classify`,
  `classify_registry`, `_signals_from_dict`; dataclasses `VendorPricingSignals`,
  `ClassificationResult`; constant `BEST_IN_CLASS_PATTERN`)
- `vendor_archetype_input_loader.py` - input load and validation (`load_and_validate`,
  `_signals`; dataclass `VendorArchetypeInput`)
- `vendor_archetype_emitter.py` - command line tool that writes the artifact and the
  handoff file (`build_output`, `main`, `_now_iso`)
- shared `_jsonschema_formats.py` (`FORMAT_CHECKER`, `SCHEMAS_DIR`) for Draft-07
  validation against `schemas/vendor-archetype-classification.schema.json`

The plugin also has the agent `vendor-archetype-classifier-agent`, the skill
`vendor-archetype-classify`, and a static seed registry of 22 vendors at
`definitions/wave1-vendors.json`.

This ADR records the decisions that the code does not make clear. Without it, a future
maintainer could "fix" something that is on purpose.

---

## Decision

### 1. 5-vs-6 collapse + `seat_anchor` discriminator -> exactly 5 canonical archetypes

The framework table "Five vendor archetypes" shows **six** rows. The two pure per-seat
variants (labor-anchored vertical and bounded-surface) are separate rows, but the
chapter calls the taxonomy "five". We join the two per-seat rows into one
`pure_per_seat` archetype with a `seat_anchor` discriminator. The value of
`seat_anchor` is `vertical_anchor` or `bounded_surface`. The five canonical archetypes
are: `pure_outcome_absorbed`, `hybrid_platform_outcome`, `pure_per_seat`,
`hybrid_seat_meter`, `pure_passthrough`. The per-seat split stays as structured
metadata. It is not a sixth top-level class.

### 2. Deterministic classifier, and an agent that extracts the signals

`classify()` (in `vendor_archetype_classifier.py`) is a **pure, first-match-wins**
function over a vector of 7 boolean values (`VendorPricingSignals`). It does no I/O
and it never raises an error. The archetype decision is deterministic and testable.
The **agent** (`vendor-archetype-classifier-agent`) only *extracts* the seven boolean
signals from the pricing page of a vendor. It never decides the archetype. The model
does the work that needs judgment (signal extraction). Python does the deterministic
work (taxonomy mapping). This follows the Python and LLM split of ADR-001 Decision 7.

### 3. Static registry and a drift check with no network

The seed registry `wave1-vendors.json` records 22 vendors with their extracted
signals and the recorded `(archetype, seat_anchor)`. `classify_registry()` runs
`classify()` again over each entry (with `_signals_from_dict`). It returns a drift
record for each vendor whose new classification differs from the recorded label.
There is **no live scraping and no network access**. The registry is a committed seed
that a person can review. The drift check compares the recorded labels with the
current classifier rules.

### 4. Handoff file

The emitter writes its result to `.competitive-intelligence/vendor-archetype-handoff.json`
(the `_OUT_SUBDIR` and `_HANDOFF` constants in `vendor_archetype_emitter.py`). The path
is fixed, so the skill `vendor-archetype-classify` always knows where to read the
`state`. The skill runs the emitter with
`uv run ${CLAUDE_PLUGIN_ROOT}/scripts/vendor_archetype_emitter.py`. The script lists its
package in a PEP 723 block, so `uv` installs the package when the script starts.

### 5. `audience: mixed` = routing metadata + field-level filtering (no stored customer summary)

`vendor-archetype-classification` is the first schema with `audience: mixed`. The
emitted artifact (`build_output`) is **operator-shaped**. It holds the full signal
vector, the rationale, and `best_in_class_pattern`. The `mixed` audience is a routing
directive. It is **not** a second stored payload. A customer-safe summary is made when
a person sends it, by field-level filtering of the operator artifact. The schema has
**no** stored `customer_summary` field, because a second copy of the view would drift
from the first. `mixed` means "route to both audiences, filter for each audience". It
does not mean "store both".

### 6. A.3 is the best-in-class UPGRADE TARGET for `pure_outcome_absorbed`, not a description

`BEST_IN_CLASS_PATTERN["pure_outcome_absorbed"]` names the A.3 pattern ("add a
platform floor") as the **upgrade target** for a pure-outcome-absorbed vendor. A.3 does
*not* describe what such a vendor does now. The archetype is defined by the *absence*
of a platform-fee floor, so a description would contradict itself. The mismatch is on
purpose. It is recorded here so that a future maintainer of the drift test does not
"correct" the entry to match the signals of the archetype. The `best_in_class_pattern`
column says where to move. It does not say where the vendor is.

### 7. Outcome-metric precedence: Rules 2 and 3 come before Rules 4 and 5

`classify()` checks passthrough first (Rule 1). Then it checks the two outcome-metric
rules (Rule 2 `hybrid_platform_outcome`, Rule 3 `pure_outcome_absorbed`). Then it checks
the seat and meter rules (Rule 4 `hybrid_seat_meter`, Rule 5 `pure_per_seat`). A vendor
with `has_outcome_metric=True` gets an outcome archetype **even if** it also has seat
and meter signals. In the framework, outcome metrics dominate. The order is on purpose.
No wave-1 vendor has the outcome, seat, and meter overlap today. If one appears, the
order is the defined rule.

### `unclassified` is not in the schema -> blocked handoff and exit code 1

`classify()` returns an `unclassified` sentinel `ClassificationResult`
(`is_classified=False`) when no rule matches (for example a per-seat vendor with no
anchor signal). The schema limits `archetype` to the five canonical values.
`unclassified` is not one of them, so the emitter never writes a classification
artifact for it. Instead `vendor_archetype_emitter.main` writes a **blocked** handoff
that names the reason, and it returns exit code **1**. The three handoff states are
`success`, `blocked` (unclassified), and `error` (input check failure or write
failure). A write failure also returns exit code 2.

---

## Consequences

**Positive:**
- The taxonomy mapping is deterministic, pure, and easy to test in full. Only the
  signal extraction, which needs judgment, is in the LLM agent.
- `classify_registry()` is a regression gate with no network. If an edit to the
  classifier rules changes the label of a wave-1 vendor, the drift check finds it.

**Negative and risks:**
- The meaning of `BEST_IN_CLASS_PATTERN["pure_outcome_absorbed"]` (Decision 6) is not
  obvious. This ADR and the module docstring record it.
- `audience: mixed` (Decision 5) gives each consumer a duty: make the customer-safe
  view by filtering, and do not read a stored summary.
- The 22-vendor registry is a seed that a person curates by hand. A person must keep it
  current. The drift check tests that the registry agrees with itself. It does not test
  that the registry is current with the live market.

## References

- Schema: `schemas/vendor-archetype-classification.schema.json` (Draft-07, `schema_version` const `1.0.0`, `audience: mixed`)
- Classifier: `scripts/vendor_archetype_classifier.py`
- Input loader: `scripts/vendor_archetype_input_loader.py`
- Emitter: `scripts/vendor_archetype_emitter.py`
- Registry: `definitions/wave1-vendors.json` (22 vendors)
- Agent: `vendor-archetype-classifier-agent`; skill: `vendor-archetype-classify`
