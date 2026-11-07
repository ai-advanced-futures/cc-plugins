# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Roadmap builder — effort/impact matrix to prioritized roadmap.

Uses the classic 2x2 effort × impact matrix:
  - Quick wins:     low effort + high impact   (do first)
  - Strategic bets: high effort + high impact  (plan and invest)
  - Fill-ins:       low effort + low impact    (do if capacity)
  - Thankless:      high effort + low impact   (avoid or defer)

Command line: roadmap_builder.py <input.json> [--out <output.json>]
The input file holds the list of gap and opportunity items. Without --out, the script prints one JSON object.
With --out, the script writes the JSON object to the output file and prints one line.
After an error, the script writes no output file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CATEGORIES = [
    {"name": "quick_win",      "effort": "low",  "impact": "high"},
    {"name": "strategic_bet",  "effort": "high", "impact": "high"},
    {"name": "fill_in",        "effort": "low",  "impact": "low"},
    {"name": "thankless",      "effort": "high", "impact": "low"},
]

_VALID_EFFORTS = {"low", "high"}
_VALID_IMPACTS = {"low", "high"}


def categorize_item(item: dict) -> str:
    effort = item.get("effort", "").lower()
    impact = item.get("impact", "").lower()

    if effort not in _VALID_EFFORTS:
        raise ValueError(f"effort must be 'low' or 'high', got '{effort}'")
    if impact not in _VALID_IMPACTS:
        raise ValueError(f"impact must be 'low' or 'high', got '{impact}'")

    for cat in CATEGORIES:
        if cat["effort"] == effort and cat["impact"] == impact:
            return cat["name"]
    return "fill_in"


def build_roadmap(items: list[dict]) -> dict:
    """Build prioritised roadmap from a list of gap/opportunity items."""
    result: dict[str, list] = {
        "quick_wins": [], "strategic_bets": [], "fill_ins": [], "thankless": []
    }

    category_map = {
        "quick_win": "quick_wins",
        "strategic_bet": "strategic_bets",
        "fill_in": "fill_ins",
        "thankless": "thankless",
    }

    for item in items:
        cat = categorize_item(item)
        result[category_map[cat]].append({**item, "category": cat})

    return result


def main(argv: list[str]) -> int:
    if len(argv) == 2:
        out = None
    elif len(argv) == 4 and argv[2] == "--out":
        out = Path(argv[3])
    else:
        print("Usage: roadmap_builder.py <input.json> [--out <output.json>]", file=sys.stderr)
        return 1
    try:
        result = build_roadmap(json.loads(Path(argv[1]).read_text()))
        if out is not None:
            out.write_text(json.dumps(result))
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f"roadmap_builder.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result) if out is None else f"items={sum(len(v) for v in result.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
