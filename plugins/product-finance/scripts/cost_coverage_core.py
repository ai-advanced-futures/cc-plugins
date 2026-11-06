# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Cost-coverage-readout math and a command that needs only Python's standard library.

Charter citation (required by Charter §11):
  JustKeenAI Agentic Pricing Framework v2.1 — §6.3 re-implementation
  Reference: plugins/pricing/pricing/lib/{sensitivity_matrix,gm_trajectory,multiple_compression}.py
  pricing-core's gm_trajectory.py vertical path matches spec §5.3 (Y1=60, Y2=70, Y3=80,
  step +7) as of pricing v1.8.0 (ADR-009).

`cost_coverage_readout.py` wraps these functions in pydantic models and checks the
result against the Charter schema. This file is what an installed plugin runs, where
Python may have neither pydantic nor jsonschema (ADR-006):

  uv run "<plugin root>/scripts/cost_coverage_core.py" --diagnosis <path> --amplifier <path> ...

Its output is byte-identical to the pydantic path's (tests/unit/test_cost_coverage_core.py).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = "1.0.0"
ENGAGEMENT_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

# ---------------------------------------------------------------------------
# Charter §3.17 + §5.3 GM trajectory constants — see ADR-002 for vertical step provenance
# ---------------------------------------------------------------------------

# Vertical archetype (lifted caps for 70+ reachability per spec §5.3)
_VERTICAL_Y1_CAP: float = 60.0
_VERTICAL_Y2_CAP: float = 70.0
_VERTICAL_Y3_CAP: float = 80.0
_VERTICAL_STARTING_STEP: float = 10.0  # Y1 = min(cap, starting_gm + STARTING_STEP)
_VERTICAL_ANNUAL_STEP: float = 7.0  # +7 per year — matches pricing-core v1.8.0 (ADR-009)

# Standard archetypes (matches pricing-core +5 step exactly)
_STANDARD_Y1_FLOOR: float = 45.0
_STANDARD_Y1_CAP: float = 55.0
_STANDARD_Y2_CAP: float = 60.0
_STANDARD_Y3_CAP: float = 65.0
_STANDARD_STARTING_STEP: float = 7.0
_STANDARD_ANNUAL_STEP: float = 5.0

_VERTICAL_ANCHOR_THRESHOLD_PCT: float = 70.0

# ---------------------------------------------------------------------------
# Charter §3.6 PE compression signal thresholds — matches pricing-core
# ---------------------------------------------------------------------------

_FV_COMPRESSED_THRESHOLD_PCT: float = 15.0
_GM_COMPRESSED_THRESHOLD_PCT: float = 70.0
_GM_MONITORING_THRESHOLD_PCT: float = 75.0
_NRR_DRAG_THRESHOLD_PCT: float = -5.0

_FV_COMPRESSED_SCORE: float = 1.0
_GM_COMPRESSED_SCORE: float = 1.0
_GM_MONITORING_SCORE: float = 0.5
_NRR_DRAG_SCORE: float = 0.5

# Band boundaries (compared against cumulative pressure score)
_BAND_BOUNDARY_LOW: float = 0.5
_BAND_BOUNDARY_HIGH: float = 1.5


def s1_to_s5(cost_baseline: float, composite_p75: float, headline_price: float) -> dict:
    """5-scenario sensitivity matrix per spec §5.2, keys in Charter schema order."""
    if headline_price <= 0:
        raise ValueError(f"headline_price must be > 0; got {headline_price}")
    if cost_baseline <= 0:
        raise ValueError(f"cost_baseline must be > 0; got {cost_baseline}")

    def margin(cost_factor: float, amp_factor: float) -> float:
        effective_cost = cost_baseline * cost_factor * amp_factor
        return (headline_price - effective_cost) / headline_price * 100.0

    def scenario(margin_pct: float, narrative: str) -> dict:
        return {"effective_margin_pct": margin_pct, "narrative_md": narrative}

    return {
        "s1": scenario(
            margin(1.0, composite_p75),
            (
                f"S1 base scenario: no stress. Effective cost = "
                f"baseline ({cost_baseline}) x composite P75 ({composite_p75}). "
                f"Used as the reference floor for the other scenarios."
            ),
        ),
        "s2": scenario(
            margin(1.5, composite_p75),
            (
                "S2 inference +50% scenario: cost baseline rises 50%. "
                "Effective cost = baseline x 1.5 x composite P75. "
                "Reflects sustained foundation-model price hikes."
            ),
        ),
        "s3": scenario(
            margin(1.0, composite_p75 * 1.2),
            (
                "S3 volume +200% scenario: usage surge with modest amplifier uplift. "
                "Composite P75 x 1.2 captures the marginal-amplifier effect "
                "when load spikes."
            ),
        ),
        "s4": scenario(
            margin(1.0, composite_p75 * 3.0),
            (
                "S4 loop 3x scenario: agentic loop overhead amplifier #1 triples. "
                "Composite P75 x 3.0 reflects worst-case loop-overhead amplifier "
                "stress. Critical for autonomous workflow archetypes."
            ),
        ),
        "s5": scenario(
            margin(1.5, composite_p75 * 1.2 * 3.0),
            (
                "S5 combined worst case: inference +50% AND volume +200% AND "
                "loop 3x simultaneously. Tests resilience under cascading "
                "foundation-model + amplifier pressure."
            ),
        ),
    }


def gm_trajectory(archetype: str, starting_gm_pct: float) -> dict:
    """Y1/Y2/Y3 GM% trajectory per spec §5.3.

    Vertical archetype uses step +7 (matches pricing-core v1.8.0 per ADR-009) to make
    requires_vertical_anchor_for_70plus reachable. Standard archetypes use step +5
    matching pricing-core exactly.
    """
    if archetype == "vertical_pro_services_agent":
        y1 = min(_VERTICAL_Y1_CAP, starting_gm_pct + _VERTICAL_STARTING_STEP)
        y2 = min(_VERTICAL_Y2_CAP, y1 + _VERTICAL_ANNUAL_STEP)
        y3 = min(_VERTICAL_Y3_CAP, y2 + _VERTICAL_ANNUAL_STEP)
    else:
        y1 = max(
            _STANDARD_Y1_FLOOR,
            min(_STANDARD_Y1_CAP, starting_gm_pct + _STANDARD_STARTING_STEP),
        )
        y2 = min(_STANDARD_Y2_CAP, y1 + _STANDARD_ANNUAL_STEP)
        y3 = min(_STANDARD_Y3_CAP, y2 + _STANDARD_ANNUAL_STEP)
    return {
        "y1_pct": y1,
        "y2_pct": y2,
        "y3_pct": y3,
        "requires_vertical_anchor_for_70plus": y3 >= _VERTICAL_ANCHOR_THRESHOLD_PCT,
    }


def compression_signals(forecast_variance_pct: float, gm_pct: float, nrr_delta_pct: float) -> dict:
    """PE compression signals + pressure band per spec §5.4.

    Scoring matches pricing/lib/multiple_compression.py exactly (float additive, max 2.5).
    """
    fv_score = (
        _FV_COMPRESSED_SCORE if forecast_variance_pct >= _FV_COMPRESSED_THRESHOLD_PCT else 0.0
    )
    if gm_pct < _GM_COMPRESSED_THRESHOLD_PCT:
        gm_score = _GM_COMPRESSED_SCORE
    elif gm_pct < _GM_MONITORING_THRESHOLD_PCT:
        gm_score = _GM_MONITORING_SCORE
    else:
        gm_score = 0.0
    nrr_score = _NRR_DRAG_SCORE if nrr_delta_pct < _NRR_DRAG_THRESHOLD_PCT else 0.0

    score = fv_score + gm_score + nrr_score

    # All sub-scores are integer multiples of 0.5 → exact float comparison is safe.
    if score == 0:
        band = "0"
    elif score <= _BAND_BOUNDARY_LOW:
        band = "0.5-1x"
    elif score <= _BAND_BOUNDARY_HIGH:
        band = "1-2x"
    else:
        band = ">2x"
    return {
        "forecast_variance_pct": forecast_variance_pct,
        "gm_pct": gm_pct,
        "nrr_delta_pct": nrr_delta_pct,
        "multiple_pressure_estimate": band,
    }


def upstream_figures(diagnosis: dict, amplifier: dict, amplifier_name: str) -> tuple:
    """(archetype, arr_band, composite_p75) from pricing's two files, checked."""
    if amplifier.get("audience") != "internal":
        raise ValueError(
            f"amplifier file {amplifier_name} has audience="
            f"{amplifier.get('audience')!r}; required 'internal'"
        )
    composite_p75 = amplifier.get("composite_p75")
    if isinstance(composite_p75, bool) or not isinstance(composite_p75, (int, float)):
        raise ValueError(f"amplifier file {amplifier_name} composite_p75 missing or non-numeric")
    if composite_p75 <= 0:
        raise ValueError(
            f"amplifier file {amplifier_name} composite_p75 must be > 0; got {composite_p75}"
        )
    return diagnosis["archetype"], diagnosis["portco_arr_band"], float(composite_p75)


def check_produced_at(produced_at: str) -> None:
    try:
        datetime.fromisoformat(produced_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"produced_at is not valid ISO 8601: {produced_at!r}") from exc


def readout(
    diagnosis_path: Path,
    amplifier_path: Path,
    gm_pct: float,
    nrr_delta_pct: float,
    forecast_variance_pct: float,
    cost_per_interaction_baseline: float,
    headline_price: float,
    engagement_id: str,
    produced_at: str,
    schema_version: str = SCHEMA_VERSION,
) -> dict:
    """The Charter §7.6 envelope as a dict, keys in Charter schema order."""
    check_produced_at(produced_at)
    if not ENGAGEMENT_ID.fullmatch(engagement_id):
        raise ValueError(f"engagement_id is not a lowercase UUID: {engagement_id!r}")
    if not SEMVER.match(schema_version):
        raise ValueError(f"schema_version is not X.Y.Z: {schema_version!r}")
    archetype, arr_band, composite_p75 = upstream_figures(
        json.loads(Path(diagnosis_path).read_text()),
        json.loads(Path(amplifier_path).read_text()),
        str(amplifier_path),
    )
    if not archetype or not arr_band:
        raise ValueError("diagnosis archetype and portco_arr_band must be non-empty")
    return {
        "engagement_id": engagement_id,
        "produced_at": produced_at,
        "schema_version": schema_version,
        "archetype": archetype,
        "arr_band": arr_band,
        "s1_to_s5_matrix": s1_to_s5(cost_per_interaction_baseline, composite_p75, headline_price),
        "gm_trajectory": gm_trajectory(archetype, gm_pct),
        "multiple_compression_signals": compression_signals(
            forecast_variance_pct, gm_pct, nrr_delta_pct
        ),
        "audience": "internal",
    }


def coverage_ratio(
    cost_per_interaction_baseline: float, composite_p75: float, headline_price: float
) -> float:
    """How far the headline price covers the S1 effective cost per interaction."""
    return headline_price / (cost_per_interaction_baseline * composite_p75)


def write_json(target: Path, payload: dict) -> None:
    """Write `payload` as indented JSON to `target` atomically (temp file, then rename)."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps(payload, indent=2))
        os.replace(tmp_name, target)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def _parse_args(argv: list) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write the cost-coverage-readout Charter artifact."
    )
    parser.add_argument("--diagnosis", required=True, type=Path)
    parser.add_argument("--amplifier", required=True, type=Path)
    parser.add_argument("--gm-pct", required=True, type=float)
    parser.add_argument("--nrr-delta-pct", required=True, type=float)
    parser.add_argument("--forecast-variance-pct", required=True, type=float)
    parser.add_argument("--cost-per-interaction-baseline", required=True, type=float)
    parser.add_argument("--headline-price", required=True, type=float)
    parser.add_argument("--engagement-id", required=True, type=str)
    parser.add_argument("--produced-at", required=True, type=str)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list) -> int:
    """Write the readout; print one JSON line naming it and its coverage ratio."""
    args = _parse_args(argv)
    try:
        package = readout(
            args.diagnosis,
            args.amplifier,
            args.gm_pct,
            args.nrr_delta_pct,
            args.forecast_variance_pct,
            args.cost_per_interaction_baseline,
            args.headline_price,
            args.engagement_id,
            args.produced_at,
        )
        _, _, composite_p75 = upstream_figures(
            json.loads(args.diagnosis.read_text()),
            json.loads(args.amplifier.read_text()),
            str(args.amplifier),
        )
    except (OSError, ValueError, KeyError) as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 1
    write_json(args.output, package)
    summary = {
        "readout": str(args.output),
        "coverage_ratio": coverage_ratio(
            args.cost_per_interaction_baseline, composite_p75, args.headline_price
        ),
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
