# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
ecosystem_health_scorer.py — Jansen's 5-dimension ecosystem health model.

Used in the discover phase to assess partner ecosystem viability.

Run: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/ecosystem_health_scorer.py <scores.json>
The file holds an object with the 5 dimensions. The script prints the result.

Formula: (sum of dimension scores / 5) × 4
Valid score range per dimension: 1–5 (integer)
Output total range: 4.0 (all 1s) to 20.0 (all 5s)

at_risk rules:
  - total < 12.0 (Priority C threshold), OR
  - productivity <= 2 AND diversity <= 2 (red-flag: declining productivity + low diversity)
"""

import argparse
import json
import sys
from pathlib import Path

HEALTH_DIMENSIONS = [
    "productivity",   # active partner output
    "robustness",     # survives disruption
    "niche_creation", # new partner types emerging
    "longevity",      # YoY growth
    "diversity",      # partner size/vertical mix
]


def score_ecosystem(scores: dict) -> dict:
    """Score the health of a partner ecosystem using Jansen's 5-dimension model.

    Args:
        scores: dict mapping each dimension name to an integer score 1–5.
                Must include all five dimensions in HEALTH_DIMENSIONS.

    Returns:
        dict with keys:
            "total"           — float in range [4.0, 20.0]
            "at_risk"         — bool; True if total < 12.0 OR (productivity <= 2 AND diversity <= 2)
            "dimension_scores" — copy of input scores dict

    Raises:
        ValueError: if any required dimension is missing from scores.
        ValueError: if any score is not an integer in range 1–5 (bools rejected).
    """
    for dimension in HEALTH_DIMENSIONS:
        if dimension not in scores:
            raise ValueError(f"Missing required dimension: '{dimension}'")
        value = scores[dimension]
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(
                f"Score for '{dimension}' must be an integer, got {value!r}"
            )
        if not (1 <= value <= 5):
            raise ValueError(
                f"Score for '{dimension}' must be in range 1–5, got {value!r}"
            )

    total = (sum(scores[d] for d in HEALTH_DIMENSIONS) / 5) * 4

    red_flag = scores["productivity"] <= 2 and scores["diversity"] <= 2
    at_risk = total < 12.0 or red_flag

    return {
        "total": total,
        "at_risk": at_risk,
        "dimension_scores": dict(scores),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("input", help="path of the JSON file")
    args = parser.parse_args(argv)
    try:
        data = json.loads(Path(args.input).read_text())
        if not isinstance(data, dict):
            raise ValueError("the file must hold an object with the 5 dimensions")
        result = score_ecosystem(data)
    except (OSError, ValueError, TypeError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
