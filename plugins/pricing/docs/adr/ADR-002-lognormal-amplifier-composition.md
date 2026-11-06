# ADR-002 — LogNormal Amplifier Composition (Charter §14.1 resolution)

| | |
|---|---|
| Status | Accepted |
| Date | 2026-05-19 |
| Deciders | pricing-core sub-spec 1 |
| Context source | Charter §14.1 deferred-decision (the framework's 5-8x P75 rule-of-thumb has no closed-form composition) |
| Supersedes | The naive multiplicative composite (∏ multiplier_p75; ∏ multiplier_p95) used in PR #98's example fixtures |

## Context

The JustKeenAI Agentic Pricing Framework v2.1 enumerates 8 cost amplifiers (planner loop, tool fan-out, multi-model, evaluator, reasoning explosion, observability, RAG depth, cache miss). Each amplifier carries a rule-of-thumb (multiplier_p75, multiplier_p95) per Table §3.2. The framework asserts a composite "5-8x P75" rule-of-thumb but provides no closed form.

The naive multiplicative composite (∏ multiplier_p75; ∏ multiplier_p95) systematically over-estimates tail risk. Example: 3 amplifiers each at (P75=2.5x, P95=6.0x) under multiplicative composition give composite_p95 = 6³ = 216x — far above any observed in-the-wild signal.

Charter §14.1 punted the choice to pricing-core: closed-form vs Monte Carlo vs neural meta-model.

## Decision

**Closed-form LogNormal composition under independence assumption.**

For each amplifier i, fit a LogNormal distribution `LN(μᵢ, σᵢ)` from the quantile pair (multiplier_p75, multiplier_p95) using `statistics.NormalDist().inv_cdf()` (Python 3.11 stdlib). Under the independence assumption, the product of LogNormals is itself LogNormal with `μ_total = Σμᵢ`, `σ²_total = Σσᵢ²`. The composite's P50/P75/P95 are then `exp(μ_total + σ_total * Φ⁻¹(q))`.

This is implemented in `pricing.lib.amplifier_composer.compose_amplifiers()`.

## Worked example

Three amplifiers each at (P75=2.5x, P95=6.0x) — the spec §3.1 example:

| Statistic | Naive multiplicative | Closed-form LogNormal |
|---|---|---|
| composite P75 | 15.625x | 14.66x |
| composite P95 | 216x | 48.67x |

LogNormal is sub-multiplicative at P95 (tail), as expected. P75 is close to naive because the median-mass region dominates the product.

## Edge cases

1. **σ = 0 (degenerate Dirac)** — when all amplifiers have P75 = P95, σ_total = 0; all 4 composite outputs collapse to `exp(μ_total)`. Implemented and tested.

2. **No present amplifiers** — returns `AmplifierCompositeResult(mean=1.0, p50=1.0, p75=1.0, p95=1.0, present_amplifiers=[])`.

3. **multiplier_p75 < 1.0 or multiplier_p95 < multiplier_p75** — raises ValueError. The framework's amplifiers are always cost-increasing.

## Consequences

- The fixture `cost-amplifier-readout.example.json` was migrated from naive (4.875/45.0) to LogNormal (2.5567/9.3255) in T17.
- The independence assumption is the primary limitation. Real-world amplifiers correlate (e.g., RAG depth correlates with planner re-runs). A v1.4.1 extension may swap independence for a copula-based composer that accepts a correlation matrix.
- No scipy dependency required — `statistics.NormalDist` is stdlib-only.
- Sensitivity matrix (T9) and cost taxonomy (T6) read from the composite's P50/P75/P95 percentiles; their tail-risk magnitudes are accurate (vs the naive composite's inflated P95).

## Cross-references

- Implementation: `plugins/pricing/pricing/lib/amplifier_composer.py`
- Tests: `plugins/pricing/tests/unit/test_amplifier_composer.py` (13 tests including the spec §3.1 worked example)
- Charter §14.1 deferred decision (now resolved)
- Spec: `docs/superpowers/specs/2026-05-19-pricing-core-v1.4.0-design.md` §3
