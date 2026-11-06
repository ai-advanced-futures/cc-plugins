# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
partner_scorer.py — Weighted scoring model for the discover phase of strategic-partnerships.

Run: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/partner_scorer.py <candidates.json>
The file holds a list of candidates (or an object with a `candidates` list). The script
prints the list with `score` and `priority`, sorted by score.

Formula: [(A×0.30) + (S×0.25) + (R×0.25) + (F×0.20)] × 4
Valid score range per dimension: 1–5 (integer)
Output score range: 4.0 (all 1s) to 20.0 (all 5s)
"""

import argparse
import json
import sys
from pathlib import Path

WEIGHTS = {
    "audience_overlap": 0.30,
    "strategic_fit": 0.25,
    "revenue_potential": 0.25,
    "execution_feasibility": 0.20,
}

_REQUIRED_KEYS = list(WEIGHTS.keys())


def score_candidate(candidate: dict) -> float:
    """Score a single partner candidate.

    Args:
        candidate: dict with keys audience_overlap, strategic_fit,
                   revenue_potential, execution_feasibility — each int 1–5.

    Returns:
        float in range [4.0, 20.0].

    Raises:
        ValueError: if any required key is missing or any score is outside 1–5.
    """
    for key in _REQUIRED_KEYS:
        if key not in candidate:
            raise ValueError(f"Missing required key: '{key}'")
        value = candidate[key]
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"Score for '{key}' must be an integer, got {value!r}")
        if not (1 <= value <= 5):
            raise ValueError(
                f"Score for '{key}' must be in range 1–5, got {value!r}"
            )

    weighted_sum = sum(candidate[k] * w for k, w in WEIGHTS.items())
    return weighted_sum * 4


def assign_priority(score: float) -> str:
    """Map a numeric score to a priority tier.

    Args:
        score: float output from score_candidate, range [4.0, 20.0].

    Returns:
        'A' if score >= 16
        'B' if 12 <= score < 16
        'C' if score < 12
    """
    if not (4.0 <= score <= 20.0):
        raise ValueError(f"score must be in [4.0, 20.0], got {score!r}")
    if score >= 16:
        return "A"
    if score >= 12:
        return "B"
    return "C"


def score_candidates(candidates: list[dict]) -> list[dict]:
    """Score and rank a list of partner candidates.

    Each input dict is copied before enrichment — originals are NOT mutated.

    Args:
        candidates: list of candidate dicts (same schema as score_candidate).

    Returns:
        New list of dicts, each with 'score' and 'priority' fields added,
        sorted by score descending (highest priority first).
    """
    enriched = []
    for candidate in candidates:
        copy = dict(candidate)
        copy["score"] = score_candidate(copy)
        copy["priority"] = assign_priority(copy["score"])
        enriched.append(copy)

    enriched.sort(key=lambda c: c["score"], reverse=True)
    return enriched


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("input", help="path of the JSON file")
    args = parser.parse_args(argv)
    try:
        data = json.loads(Path(args.input).read_text())
        if isinstance(data, dict) and "candidates" in data:
            data = data["candidates"]
        if not isinstance(data, list):
            raise ValueError("the file must hold a list of candidates")
        result = score_candidates(data)
    except (OSError, ValueError, TypeError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
