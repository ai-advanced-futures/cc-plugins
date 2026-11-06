# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Composite Opportunity Scorer — Phase 10

Computes weighted composite scores for JTBD opportunities by combining:
  - ODI Score       (40%) — from p6.json opportunity_score (0-20 scale)
  - Financial Score (35%) — from p7.json total_annual_evc (relative to max)
  - Segment Score   (25%) — from p8.json size_percent × p9.json confidence weight

Reads phase output files from a session directory and writes composite scores
to stdout as JSON.  The output-assembler agent calls this script, then
incorporates the result into final-output.json.

Usage:
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/composite_scorer.py --session-dir .jtbd-market-discovery/TIMESTAMP/

Author: Luis F. Amadeo (Chief Agentic Officer)
License: MIT
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Confidence label → numeric weight
CONFIDENCE_WEIGHTS: dict[str, float] = {
    "high": 1.0,
    "medium": 0.5,
    "low": 0.25,
}

# Composite score dimension weights (must sum to 1.0)
WEIGHT_ODI: float = 0.40
WEIGHT_FINANCIAL: float = 0.35
WEIGHT_SEGMENT: float = 0.25


def _load(session_dir: Path, filename: str) -> dict[str, Any]:
    path = session_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"{filename} not found in {session_dir}")
    return json.loads(path.read_text())


def compute_composite_scores(session_dir: Path) -> list[dict[str, Any]]:
    """
    Compute composite scores for all top opportunities.

    Args:
        session_dir: Absolute path to .jtbd-market-discovery/SESSION/ directory.

    Returns:
        List of opportunity dicts with composite_score added, sorted descending.
    """
    p6 = _load(session_dir, "p6.json")
    p7 = _load(session_dir, "p7.json")
    p8 = _load(session_dir, "p8.json")
    p9 = _load(session_dir, "p9.json")

    # Build EVC lookup: need_id → total_annual_evc
    evc_by_need: dict[str, float] = {}
    for entry in p7.get("top_evc_opportunities", []):
        need_id = str(entry.get("need_id", ""))
        evc_by_need[need_id] = float(entry.get("total_annual_evc", 0))

    max_evc = max(evc_by_need.values(), default=1.0) or 1.0

    # Segment confidence weight from p9 overall confidence
    overall_confidence = p9.get("confidence", "medium")
    if isinstance(overall_confidence, dict):
        # Some schemas nest it under a key
        overall_confidence = overall_confidence.get("level", "medium")
    confidence_weight = CONFIDENCE_WEIGHTS.get(str(overall_confidence).lower(), 0.5)

    # Best segment size_percent from p8
    segments = p8.get("segments", [])
    best_size_pct: float = max(
        (float(s.get("size_percent", 0)) for s in segments), default=50.0
    )

    # Score each opportunity from p6
    opportunities = p6.get("top_opportunities", p6.get("opportunities", []))
    scored: list[dict[str, Any]] = []

    for opp in opportunities:
        need_id = str(opp.get("need_id", ""))
        opportunity_score = float(opp.get("opportunity_score", 0))

        # ODI Score: normalize 0-20 scale to 0-100
        odi_score = (opportunity_score / 20.0) * 100.0

        # Financial Score: relative to highest EVC need
        this_evc = evc_by_need.get(need_id, 0.0)
        financial_score = (this_evc / max_evc) * 100.0

        # Segment Score: best segment size × confidence weight
        segment_score = (best_size_pct / 100.0) * confidence_weight * 100.0

        composite = (
            odi_score * WEIGHT_ODI
            + financial_score * WEIGHT_FINANCIAL
            + segment_score * WEIGHT_SEGMENT
        )

        scored.append({
            **opp,
            "odi_score_normalized": round(odi_score, 1),
            "financial_score": round(financial_score, 1),
            "segment_score": round(segment_score, 1),
            "composite_score": round(composite, 1),
        })

    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    for rank, opp in enumerate(scored, start=1):
        opp["rank"] = rank

    return scored


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Compute composite opportunity scores")
    parser.add_argument(
        "--session-dir",
        required=True,
        help="Absolute path to .jtbd-market-discovery/SESSION/ directory",
    )
    args = parser.parse_args()

    session_dir = Path(args.session_dir)
    if not session_dir.is_dir():
        print(f"Error: {session_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    try:
        results = compute_composite_scores(session_dir)
        print(json.dumps(results, indent=2))
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
