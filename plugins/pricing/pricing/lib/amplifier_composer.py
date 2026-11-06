"""Closed-form LogNormal composition of 8 cost amplifiers.

Per spec §3 + ADR-002 (to be added in Phase 6). Implements LogNormal
closure-under-product for the framework's 8 amplifiers under independence
assumption.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

# Module-level Φ⁻¹ constants computed once at import via Python 3.11 stdlib.
# No scipy / no Acklam approximation needed (see spec §3.2).
_PHI_INV_P75: float = statistics.NormalDist().inv_cdf(0.75)
_PHI_INV_P95: float = statistics.NormalDist().inv_cdf(0.95)
_PHI_INV_P50: float = 0.0  # NormalDist median
_DENOM_75_95: float = _PHI_INV_P95 - _PHI_INV_P75


@dataclass
class AmplifierReading:
    amp_id: int  # 1-8 per framework Table §3.2
    multiplier_p75: float
    multiplier_p95: float
    present: bool


@dataclass
class AmplifierCompositeResult:
    mean: float
    p50: float
    p75: float
    p95: float
    present_amplifiers: list[int]


def fit_lognormal_from_quantiles(p75: float, p95: float) -> tuple[float, float]:
    """Fit LogNormal distribution from P75 and P95 quantiles.

    Returns (μ, σ). When p75 == p95, returns σ = 0 (degenerate Dirac).
    """
    if p75 <= 0 or p95 <= 0:
        raise ValueError(f"quantiles must be positive: p75={p75}, p95={p95}")
    log_p75 = math.log(p75)
    log_p95 = math.log(p95)
    sigma = (log_p95 - log_p75) / _DENOM_75_95
    mu = log_p75 - sigma * _PHI_INV_P75
    return mu, sigma


def compose_amplifiers(readings: list[AmplifierReading]) -> AmplifierCompositeResult:
    """Compose present amplifiers into single LogNormal distribution.

    Returns AmplifierCompositeResult with mean (for pricing), P50 (median),
    P75 (typical-case GM stress), P95 (underwriting reserve).

    Assumes independence between amplifiers (per spec §3.3 / ADR-002).
    """
    present = [r for r in readings if r.present]
    present_ids = [r.amp_id for r in present]

    if not present:
        return AmplifierCompositeResult(mean=1.0, p50=1.0, p75=1.0, p95=1.0, present_amplifiers=[])

    # Validate
    for r in present:
        if r.multiplier_p75 < 1.0:
            raise ValueError(f"amp_id={r.amp_id}: multiplier_p75 must be ≥ 1.0, got {r.multiplier_p75}")
        if r.multiplier_p95 < r.multiplier_p75:
            raise ValueError(
                f"amp_id={r.amp_id}: multiplier_p95 ({r.multiplier_p95}) must be ≥ multiplier_p75 "
                f"({r.multiplier_p75})"
            )

    # Fit each, sum log-space
    mu_total = 0.0
    sigma_sq_total = 0.0
    for r in present:
        mu_i, sigma_i = fit_lognormal_from_quantiles(r.multiplier_p75, r.multiplier_p95)
        mu_total += mu_i
        sigma_sq_total += sigma_i * sigma_i

    sigma_total = math.sqrt(sigma_sq_total)

    if sigma_total == 0:
        # Degenerate Dirac — all 4 outputs collapse to exp(μ_total)
        point = math.exp(mu_total)
        return AmplifierCompositeResult(
            mean=point, p50=point, p75=point, p95=point, present_amplifiers=present_ids
        )

    mean = math.exp(mu_total + sigma_sq_total / 2.0)
    p50 = math.exp(mu_total)
    p75 = math.exp(mu_total + sigma_total * _PHI_INV_P75)
    p95 = math.exp(mu_total + sigma_total * _PHI_INV_P95)

    return AmplifierCompositeResult(
        mean=mean, p50=p50, p75=p75, p95=p95, present_amplifiers=present_ids
    )
