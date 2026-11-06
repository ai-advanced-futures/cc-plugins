"""Cost-coverage-readout serializer for Charter §7.6 agentic-pricing handoff schema.

Produces a cost-coverage-readout.json handoff artifact (audience: internal) from
pricing's agentic-pricing-diagnosis.json + cost-amplifier-readout.json inputs plus
company financial parameters. No LLM in the path. Pure Python + jsonschema.

Charter citation (required by Charter §11):
  JustKeenAI Agentic Pricing Framework v2.1 — §6.3 re-implementation
  Reference: plugins/pricing/pricing/lib/{sensitivity_matrix,gm_trajectory,multiple_compression}.py
  NOTE: as of pricing v1.8.0 (ADR-009), pricing-core's gm_trajectory.py vertical
  path matches spec §5.3 (Y1=60, Y2=70, Y3=80, step +7); the reference file and
  §5.3 are now aligned.

CLI (repo checkout): uv run python -m scripts.cost_coverage_readout --diagnosis <path> ...
An installed plugin runs scripts/cost_coverage_core.py instead: standard library only.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from scripts.cost_coverage_core import (
    compression_signals,
    gm_trajectory,
    s1_to_s5,
    upstream_figures,
)
from scripts.utils.io import atomic_write_json

# ---------------------------------------------------------------------------
# Module-level constants. The `# noqa: E501  # bootstrap fills` suffix is
# LOAD-BEARING: bootstrap_cost_coverage_schema_hash.py's regex requires it
# as a capture group. Absent → bootstrap silently no-ops.
# ---------------------------------------------------------------------------

_SCHEMA_VERSION: str = "1.0.0"
_SCHEMA_SHA256_PINNED: str = "6e450b8d24446ba5939152190d789701088ef969452c6c8b72fb0fad93a5319e"  # noqa: E501  # bootstrap fills

# The handoff envelope's own version (HANDOFF_SCHEMA_VERSION) lives in cost_coverage_core.py,
# apart from the readout schema version, so the two evolve on independent contracts (T2-2).

_SCHEMA_PATH: Path = (
    Path(__file__).resolve().parents[1]
    / "schemas" / "agentic-pricing"
    / "cost-coverage-readout.schema.json"
)


# The math and its constants live in scripts/cost_coverage_core.py (standard library
# only), which an installed plugin runs; this module wraps them in pydantic models.


# ---------------------------------------------------------------------------
# Pydantic models — field order MUST mirror Charter schema properties order.
# ---------------------------------------------------------------------------

_STRICT_MODEL_CONFIG = ConfigDict(extra="forbid", frozen=True)


class ScenarioResult(BaseModel):
    """One scenario in the S1-S5 sensitivity matrix."""
    model_config = _STRICT_MODEL_CONFIG

    effective_margin_pct: float
    narrative_md: str = Field(min_length=1)


class S1S5Matrix(BaseModel):
    """5-scenario stress test result. Field order must match Charter schema."""
    model_config = _STRICT_MODEL_CONFIG

    s1: ScenarioResult
    s2: ScenarioResult
    s3: ScenarioResult
    s4: ScenarioResult
    s5: ScenarioResult


class GmTrajectory(BaseModel):
    """Y1/Y2/Y3 GM% projections under Predictability Architecture."""
    model_config = _STRICT_MODEL_CONFIG

    y1_pct: float
    y2_pct: float
    y3_pct: float
    requires_vertical_anchor_for_70plus: bool


class MultipleCompressionSignals(BaseModel):
    """PE diligence compression signals + estimated multiple pressure band."""
    model_config = _STRICT_MODEL_CONFIG

    forecast_variance_pct: float
    gm_pct: float
    nrr_delta_pct: float
    multiple_pressure_estimate: Literal["0", "0.5-1x", "1-2x", ">2x"]


class CostCoverageEnvelope(BaseModel):
    """Charter §7.6 envelope — audience pinned to 'internal'."""
    model_config = _STRICT_MODEL_CONFIG

    engagement_id: str = Field(
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    produced_at: str
    schema_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    archetype: str = Field(min_length=1)
    arr_band: str = Field(min_length=1)
    s1_to_s5_matrix: S1S5Matrix
    gm_trajectory: GmTrajectory
    multiple_compression_signals: MultipleCompressionSignals
    audience: Literal["internal"] = "internal"


# ---------------------------------------------------------------------------
# Math functions (Charter §6.3 re-implementation, no pricing.lib imports)
# ---------------------------------------------------------------------------


def compute_s1_to_s5(
    cost_baseline: float, composite_p75: float, headline_price: float
) -> S1S5Matrix:
    """Compute 5-scenario sensitivity matrix per spec §5.2."""
    return S1S5Matrix(**s1_to_s5(cost_baseline, composite_p75, headline_price))


def compute_gm_trajectory(archetype: str, starting_gm_pct: float) -> GmTrajectory:
    """Y1/Y2/Y3 GM% trajectory per spec §5.3 (vertical step +7, standard +5)."""
    return GmTrajectory(**gm_trajectory(archetype, starting_gm_pct))


def compute_compression_signals(
    forecast_variance_pct: float, gm_pct: float, nrr_delta_pct: float
) -> MultipleCompressionSignals:
    """PE compression signals + pressure band per spec §5.4."""
    return MultipleCompressionSignals(
        **compression_signals(forecast_variance_pct, gm_pct, nrr_delta_pct)
    )


# ---------------------------------------------------------------------------
# Serializer
# ---------------------------------------------------------------------------


def serialize_cost_coverage_readout(
    diagnosis_path: Path,
    amplifier_path: Path,
    gm_pct: float,
    nrr_delta_pct: float,
    forecast_variance_pct: float,
    cost_per_interaction_baseline: float,
    headline_price: float,
    engagement_id: str,
    produced_at: str,
    schema_version: str = _SCHEMA_VERSION,
) -> dict:
    """Build cost-coverage-readout package as a dict suitable for JSON emission."""
    try:
        datetime.fromisoformat(produced_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"produced_at is not valid ISO 8601: {produced_at!r}") from exc

    diagnosis = json.loads(diagnosis_path.read_text())
    amplifier = json.loads(amplifier_path.read_text())

    archetype, arr_band, composite_p75 = upstream_figures(
        diagnosis, amplifier, str(amplifier_path)
    )

    matrix = compute_s1_to_s5(
        cost_baseline=cost_per_interaction_baseline,
        composite_p75=composite_p75,
        headline_price=headline_price,
    )
    gm_traj = compute_gm_trajectory(archetype=archetype, starting_gm_pct=gm_pct)
    compression = compute_compression_signals(
        forecast_variance_pct=forecast_variance_pct,
        gm_pct=gm_pct,
        nrr_delta_pct=nrr_delta_pct,
    )

    envelope = CostCoverageEnvelope(
        engagement_id=engagement_id,
        produced_at=produced_at,
        schema_version=schema_version,
        archetype=archetype,
        arr_band=arr_band,
        s1_to_s5_matrix=matrix,
        gm_trajectory=gm_traj,
        multiple_compression_signals=compression,
    )
    return envelope.model_dump(mode="json")


def emit_to_json(package: dict, output_path: Path) -> None:
    """Validate against Charter schema (with format_checker) then write to disk."""
    import jsonschema

    schema = json.loads(_SCHEMA_PATH.read_text())
    jsonschema.validate(
        instance=package,
        schema=schema,
        cls=jsonschema.Draft7Validator,
        format_checker=jsonschema.FormatChecker(),
    )
    atomic_write_json(output_path, package)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serialize cost-coverage-readout Charter handoff artifact."
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
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    package = serialize_cost_coverage_readout(
        diagnosis_path=args.diagnosis,
        amplifier_path=args.amplifier,
        gm_pct=args.gm_pct,
        nrr_delta_pct=args.nrr_delta_pct,
        forecast_variance_pct=args.forecast_variance_pct,
        cost_per_interaction_baseline=args.cost_per_interaction_baseline,
        headline_price=args.headline_price,
        engagement_id=args.engagement_id,
        produced_at=args.produced_at,
    )
    emit_to_json(package, args.output)
    print(f"Written: {args.output}")


if __name__ == "__main__":
    main()
