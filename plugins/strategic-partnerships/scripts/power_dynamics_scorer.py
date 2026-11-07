# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
power_dynamics_scorer.py — Jansen's power dynamics model for the discover phase of strategic-partnerships.

Run: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/power_dynamics_scorer.py <scores.json> [--out FILE]
The file holds an object with the 4 power factors. The script prints the result.

Scores your relative power position across 4 structural factors and maps the
net balance to a negotiation stance.

Net balance formula: simple average of all 4 factor scores.
Stance thresholds:
    assertive      — net_balance >= 3.5  (power in your favor)
    collaborative  — 2.5 <= net_balance < 3.5  (balanced)
    value_led      — net_balance < 2.5  (power against you — lead with exceptional value)

With `--out`, the script writes the result to the file and prints 1 line.
"""

import argparse
import json
import sys
from pathlib import Path

POWER_FACTORS = [
    "dependency",        # who needs whom more? (your score = how much THEY need YOU)
    "substitutability",  # can either be replaced? (your score = how hard YOU are to replace)
    "centrality",        # who is more central to the ecosystem? (your score)
    "alternatives",      # how many comparable options? (your score = fewer options for them = higher)
]


def score_power_balance(your_scores: dict) -> dict:
    """Score your power position relative to a potential partner.

    Args:
        your_scores: dict mapping each factor in POWER_FACTORS to an integer 1–5
                     representing your position on that dimension.

    Returns:
        dict with keys:
            "net_balance"   — float, simple average of all 4 factors (range 1.0–5.0)
            "stance"        — str, one of "assertive" | "collaborative" | "value_led"
            "factor_scores" — dict, copy of input your_scores

    Raises:
        ValueError: if any required factor is missing.
        ValueError: if any score is not an integer in range 1–5 (bools rejected).
    """
    for factor in POWER_FACTORS:
        if factor not in your_scores:
            raise ValueError(f"Missing required factor: '{factor}'")
        value = your_scores[factor]
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(
                f"Score for '{factor}' must be an integer, got {value!r}"
            )
        if not (1 <= value <= 5):
            raise ValueError(
                f"Score for '{factor}' must be in range 1–5, got {value!r}"
            )

    net_balance = sum(your_scores[f] for f in POWER_FACTORS) / 4

    if net_balance >= 3.5:
        stance = "assertive"
    elif net_balance >= 2.5:
        stance = "collaborative"
    else:
        stance = "value_led"

    return {
        "net_balance": net_balance,
        "stance": stance,
        "factor_scores": dict(your_scores),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("input", help="path of the JSON file")
    parser.add_argument("--out", help="write the result to this file and print one line")
    args = parser.parse_args(argv)
    try:
        data = json.loads(Path(args.input).read_text())
        if not isinstance(data, dict):
            raise ValueError("the file must hold an object with the 4 power factors")
        result = score_power_balance(data)
        text = json.dumps(result, indent=2)
        if args.out:
            Path(args.out).write_text(text + "\n")
    except (OSError, ValueError, TypeError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(f"stance={result['stance']}" if args.out else text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
