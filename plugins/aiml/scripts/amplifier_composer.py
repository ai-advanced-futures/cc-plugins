"""LogNormal closed-form composition of 8 cost amplifiers (reimplemented for aiml).

Per Charter §6.3 reimplementation mandate — same numerical behavior as pricing's
amplifier_composer.py but written from scratch from JustKeenAI framework v2.1 §3.
NO pricing.lib imports (enforced by test_no_pricing_lib_imports.py).

Input type: amplifier_telemetry_loader.AmplifierReading (canonical 6-field struct).
Result type: AmplifierCompositeResult (composer-local).
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

from amplifier_telemetry_loader import AmplifierReading  # canonical 6-field input struct

# Φ⁻¹ constants — Python 3.11 stdlib (no scipy).
_PHI_INV_P75: float = statistics.NormalDist().inv_cdf(0.75)
_PHI_INV_P95: float = statistics.NormalDist().inv_cdf(0.95)
_PHI_INV_P50: float = 0.0
_DENOM_75_95: float = _PHI_INV_P95 - _PHI_INV_P75


@dataclass(frozen=True)
class AmplifierCompositeResult:
    mean: float
    p50: float
    p75: float
    p95: float
    # Insertion order of present amp IDs (NOT sorted). Mirrors pricing's
    # reference composer (`return [r.amp_id for r in present]`) to honor the
    # spec §7.1.1 (5) all-5-fields numerical-parity contract. See ADR-001
    # decision #16. Test fixtures construct inputs in sorted order so the
    # observable values are identical to a sorted list in practice — but the
    # binding is structural, not value-based.
    present_amplifiers: list[int]


def _fit_lognormal(p75: float, p95: float) -> tuple[float, float]:
    if p75 <= 0 or p95 <= 0:
        raise ValueError(f"quantiles must be positive: p75={p75}, p95={p95}")
    if p95 < p75:
        raise ValueError(f"p95 must be >= p75: p75={p75}, p95={p95}")
    log_p75 = math.log(p75)
    log_p95 = math.log(p95)
    sigma = (log_p95 - log_p75) / _DENOM_75_95
    mu = log_p75 - sigma * _PHI_INV_P75
    return mu, sigma


def compose(readings: dict[int, AmplifierReading]) -> AmplifierCompositeResult:
    """Compose present amplifiers into a single LogNormal under independence.

    Closed-form: sum of LogNormals (under independence) is LogNormal with
    mu_total = sum(mu_i), sigma_total = sqrt(sum(sigma_i**2)).
    """
    present = [r for r in readings.values() if r.present]

    if not present:
        return AmplifierCompositeResult(mean=1.0, p50=1.0, p75=1.0, p95=1.0, present_amplifiers=[])

    # Validate ALL present readings (including p75 < 1.0 — input schema requires ≥1.0,
    # but composer enforces internally too).
    mu_total = 0.0
    sigma_sq_total = 0.0
    for r in present:
        if r.multiplier_p75 < 1.0:
            raise ValueError(f"multiplier_p75 must be ≥1.0 for amp {r.amp_id}: got {r.multiplier_p75}")
        mu, sigma = _fit_lognormal(r.multiplier_p75, r.multiplier_p95)
        mu_total += mu
        sigma_sq_total += sigma * sigma

    sigma_total = math.sqrt(sigma_sq_total)

    # Degenerate Dirac case: sigma_total == 0 (all amps have p75 == p95).
    # All 4 outputs collapse to exp(mu_total). Mirrors pricing's reference behavior.
    if sigma_total == 0:
        point = math.exp(mu_total)
        return AmplifierCompositeResult(
            mean=point, p50=point, p75=point, p95=point,
            present_amplifiers=[r.amp_id for r in present],
        )

    p50 = math.exp(mu_total + sigma_total * _PHI_INV_P50)
    p75 = math.exp(mu_total + sigma_total * _PHI_INV_P75)
    p95 = math.exp(mu_total + sigma_total * _PHI_INV_P95)
    mean = math.exp(mu_total + 0.5 * sigma_total * sigma_total)

    return AmplifierCompositeResult(
        mean=mean, p50=p50, p75=p75, p95=p95,
        # INSERTION ORDER, NOT sorted — mirrors pricing's reference composer
        # `return [r.amp_id for r in present]` per ADR-003 decision #16. The
        # spec §7.1.1 (5) parity contract is "all 5 result fields match
        # pricing's output exactly" — structural equality, not just numerical.
        present_amplifiers=[r.amp_id for r in present],
    )


if __name__ == "__main__":
    # Smoke test: print pricing-fixture-3-amps composite.
    # Uses the canonical 6-field AmplifierReading from amplifier_telemetry_loader.
    r = compose({
        1: AmplifierReading(amp_id=1, multiplier_p75=2.5, multiplier_p95=6.0, sample_size_n=1, detection_signal="(smoke)", present=True),
        3: AmplifierReading(amp_id=3, multiplier_p75=1.5, multiplier_p95=3.0, sample_size_n=1, detection_signal="(smoke)", present=True),
        5: AmplifierReading(amp_id=5, multiplier_p75=1.3, multiplier_p95=2.5, sample_size_n=1, detection_signal="(smoke)", present=True),
    })
    print(f"p75={r.p75:.4f} p95={r.p95:.4f} present={r.present_amplifiers}")
