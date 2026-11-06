"""PE diligence threshold assessment per spec §9.

Framework §3.6 multiple-compression thresholds:
- Forecast variance >15% triggers 1-2x EV/Revenue compression.
- GM <70% triggers deeper diligence + multiple pressure.
- NRR delta drives lift/clear/drag classification.

Combined signals produce an estimated multiple-pressure band ("0",
"0.5-1x", "1-2x", ">2x"). Band-typed return is intentional per Charter
§11.3 honesty-over-precision: PE diligence is judgment, not a point
estimate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class CompressionRisk:
    forecast_variance_signal: Literal["clear", "monitoring", "compressed"]
    gm_signal: Literal["clear", "monitoring", "compressed"]
    nrr_signal: Literal["lift", "clear", "drag"]
    estimated_multiple_pressure: str  # "0", "0.5-1x", "1-2x", ">2x"
    rationale: str


def assess_compression(
    forecast_variance_pct: float,
    gm_pct: float,
    nrr_delta_pct: float,
) -> CompressionRisk:
    """Assess PE diligence compression risk per framework §3.6."""

    # Forecast variance: framework says >15% triggers 1-2x compression
    if forecast_variance_pct < 10:
        fv_signal: Literal["clear", "monitoring", "compressed"] = "clear"
    elif forecast_variance_pct < 15:
        fv_signal = "monitoring"
    else:
        fv_signal = "compressed"

    # Framework §3.6: GM <70% compressed (deeper diligence + multiple pressure),
    # 70-75% monitoring, ≥75% clear.
    if gm_pct < 70:
        gm_signal: Literal["clear", "monitoring", "compressed"] = "compressed"
    elif gm_pct < 75:
        gm_signal = "monitoring"
    else:
        gm_signal = "clear"

    # NRR delta: lift > 10%, clear -5 to 10%, drag < -5%
    if nrr_delta_pct > 10:
        nrr: Literal["lift", "clear", "drag"] = "lift"
    elif nrr_delta_pct >= -5:
        nrr = "clear"
    else:
        nrr = "drag"

    # Combined estimated multiple pressure (additive score → band).
    pressure_score = 0.0
    if fv_signal == "compressed":
        pressure_score += 1
    if gm_signal == "compressed":
        pressure_score += 1
    if gm_signal == "monitoring":
        pressure_score += 0.5
    if nrr == "drag":
        pressure_score += 0.5

    if pressure_score == 0:
        pressure = "0"
    elif pressure_score <= 0.5:
        pressure = "0.5-1x"
    elif pressure_score <= 1.5:
        pressure = "1-2x"
    else:
        pressure = ">2x"

    rationale = (
        f"Forecast variance {forecast_variance_pct:.1f}% ({fv_signal}). "
        f"GM {gm_pct:.1f}% ({gm_signal}). "
        f"NRR delta {nrr_delta_pct:+.1f}% ({nrr}). "
        f"Combined: {pressure} multiple compression risk."
    )

    return CompressionRisk(
        forecast_variance_signal=fv_signal,
        gm_signal=gm_signal,
        nrr_signal=nrr,
        estimated_multiple_pressure=pressure,
        rationale=rationale,
    )
