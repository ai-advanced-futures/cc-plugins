# ADR-005: Magic Number Canonicalization (single source of truth)

**Date:** 2026-06-03
**Status:** Accepted
**Plugin:** product-finance v0.6.0, amended in v0.14.0 and v0.16.0

## Context

Five separate Magic Number implementations existed across the plugin, with two
different formulas:

| # | Location | Formula | Banding | Return |
|---|----------|---------|---------|--------|
| 1 | `scripts/rule_of_40.py::calculate_magic_number_quarterly` | `(qNNA × 4) / prior_q_sm` (canonical) | `assess_ratio_health` | dict |
| 2 | `scripts/unit_economics.py::calculate_magic_number` | `net_new_arr / sm_spend` then `×(12/period)` | inline if/elif | `MagicNumberResult` |
| 3 | `scripts/unit_economics.py::calculate_magic_number_safe` | `net_new_arr / sm_spend` | none | `Optional[float]` |
| 4 | `scripts/utils/calculators.py::calculate_magic_number` | `net_new_arr / sm_spend` (raises on zero) | none | `float` |
| 5 | the Rule of 40 tool of the server that v0.11.0 removed | `qNNA / prior_q_sm` — **no ×4** | inline `_assess_magic_number_health` | dict `{value, health}` |

The formula divergence (×4 lag-adjusted quarterly vs. simple current-period vs. ×(12/period))
meant the "same" metric returned materially different values depending on the entrypoint. #5
(the tool of that server) silently omitted the ×4 annualization the canonical SaaS formula
requires.

## Decision

Lift the canonical lag-adjusted quarterly formula into a new shared module
`scripts/utils/magic_number.py` exposing:

- A frozen dataclass `MagicNumberOutcome(magic_number: Optional[float], health: MetricHealth, interpretation: str)`.
- `calculate_magic_number(quarterly_net_new_arr, prior_quarter_sm_spend) -> MagicNumberOutcome`,
  computing `(quarterly_net_new_arr × 4) / prior_quarter_sm_spend` via the shared `safe_divide`,
  banded via the shared `MAGIC_NUMBER_THRESHOLDS` + `assess_ratio_health`.

**In-scope sites delegate (this PR):**

- **#1 rule_of_40** — `calculate_magic_number_quarterly` is deleted; the call site delegates and
  adapts `MagicNumberOutcome` → its existing `{"magic_number", "health", "interpretation"}` dict
  (output shape preserved).
- **#2 unit_economics** — `calculate_magic_number(MagicNumberInput)` delegates and adapts →
  `MagicNumberResult` with `benchmark_notes = outcome.interpretation` and
  `efficiency_interpretation = f"Magic Number: {outcome.magic_number:.2f}"`. The internal
  `MagicNumberInput`/`MagicNumberResult` fields are renamed
  `net_new_arr → quarterly_net_new_arr`, `sales_marketing_spend → prior_quarter_sm_spend`, and
  `period_months` is dropped (the ×4 form needs no per-period annualization). The emitted
  `magic_number` JSON/markdown output keys are renamed in lockstep. `UnitEconomicsInput` (the
  stdin contract) is NOT renamed — it has no direct `MagicNumberInput` construction path.
- **#5 the server tool** — it delegated to the canonical module and gained the missing ×4, so
  `(1M, 500k)` shifted from `2.0` to `8.0`. Version 0.11.0 removed the server; the module stays.

**Deferred (logged as new FOLLOWUPS rows in the state-update PR):**

- **F55** — #3 `calculate_magic_number_safe` (test-only simple primitive): decide redirect vs delete.
- **F56** — #4 `utils/calculators.calculate_magic_number` (dead + untested): decide delete vs adopt.

Their simple non-quarterly semantics + different error contracts make "canonicalizing" them a
behavior change rather than a dedupe — out of F8's "formula divergence" scope.

### LOCK-POINT A — negative-ARR handling

`assess_ratio_health(negative, MAGIC_NUMBER_THRESHOLDS)` returns `UNKNOWN` (no lower-bound ≤ a
negative value), and the interpretation map has no `UNKNOWN` entry, so a naive lift would downgrade
the old `unit_economics` "negative → CRITICAL, ARR is declining" signal to `unknown` / `""`. The
canonical helper therefore intercepts `magic_number < 0` BEFORE banding and returns
`(magic_number, CRITICAL, "Negative Magic Number — ARR is declining; fix churn/retention.")`.
Since 0.14.0 the helper returns the exact value, unrounded; each output site rounds it half away from zero (ADR-009).
This is a strict improvement that now also flows to rule_of_40 (which previously had the same latent
gap). The interpretation string MUST contain "declining" (asserted by `test_unit_economics` and
`test_magic_number`).

### LOCK-POINT B — holistic mapping

`analyze_unit_economics` maps `quarterly_net_new_arr = data.net_new_arr`.

Amended in 0.14.0. Until then the holistic path took the whole period's S&M costs as
`prior_quarter_sm_spend`, so at the default 12-month period the Magic Number was a quarter of its true
value. `UnitEconomicsInput` now has an optional `prior_quarter_sm_spend`, and the script uses it when
given. When it is absent, the script estimates the quarter's spend as
(sales_costs + marketing_costs) × 3 / period_months. The figure carries `is_estimate` and an
`estimate_note`, prints as an estimate in the markdown, and is left out of `overall_health` and of the
recommendations, except one line that says to recalculate it with the quarter's spend. An estimate prints no
Notes sentence: `benchmark_notes` is null. The estimate is built outside the input limits, so it may exceed
the limit on a given spend.

### None-spend banding

The canonical `None`-spend branch returns `MetricHealth.UNKNOWN` ("unknown"). The old server tool made both `None` and an `UNKNOWN` band "critical". The canonical band "unknown" is the one kept.

## Consequences

- **Single source of truth.** A `test_magic_number.py` single-source guard asserts only
  `scripts/utils/magic_number.py` carries the quarterly ×4 composition; #3/#4 are allowlisted as
  deferred (F55/F56). The server tool was not on the list: it delegated.
- **Breaking, but isolated & pre-1.0.** Renamed internal model + emitted output keys + a materially
  different metric value (×4), all in one independently-revertable PR. No
  Python importers of the renamed models outside `unit_economics.py` + its tests. minor bump
  (v0.6.0) is acceptable pre-1.0.
- **No dispatch ABI.** No `schema_version` interaction — this is a normal ADR (no Phase-0 stub).

## Amendment (v0.7.0, 2026-06-04) — F55/F56 resolved + F51 enum consolidation

- **F55 ✅ RESOLVED:** `unit_economics.calculate_magic_number_safe` (test-only simple primitive) DELETED. The `DEFERRED_ALLOWLIST` in `test_magic_number.py` is now empty.
- **F56 ✅ RESOLVED:** `utils/calculators.calculate_magic_number` (dead simple primitive) + its `scripts/utils/__init__.py` export DELETED. The canonical `magic_number.calculate_magic_number` and the live `unit_economics.calculate_magic_number` wrapper are unaffected.
- **F51 (related):** the enum-consolidation pattern F6 established for health enums is extended to `GrowthStage` and `AIProvider`. Canonical `AIProvider` (`scripts/utils/enums.py`) is grown to a 10-member union (adds `AWS_BEDROCK`/`AZURE_OPENAI`/`HUGGINGFACE`/`CUSTOM`; existing `AWS`/`AZURE`/`OTHER` retained). `rule_of_40.py` and `ai_roi_calculator.py` now import the canonical enums; `test_enum_consolidation.py` bans all four enum names.

## Amendment in v0.16.0

The Rule of 40 report and JSON no longer print `interpretation`; the dict still carries it (#1 and LOCK-POINT A).
