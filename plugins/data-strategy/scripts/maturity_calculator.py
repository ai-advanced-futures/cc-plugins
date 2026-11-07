# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Gartner D&A Maturity Level calculator.

Maps intake answers to one of 5 Gartner D&A Maturity levels:
  1 — Descriptive   (what happened)
  2 — Diagnostic    (why it happened)
  3 — Predictive    (what will happen)
  4 — Prescriptive  (what should we do)
  5 — Cognitive     (automated decision-making)

Command line: maturity_calculator.py <input.json> [--out <output.json>]
The input file holds the gartner_answers object. Without --out, the script prints one JSON object.
With --out, the script writes the JSON object to the output file and prints one line.
After an error, the script writes no output file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

MATURITY_LEVELS = [
    {"level": 1, "label": "Descriptive",  "description": "Reporting on what happened"},
    {"level": 2, "label": "Diagnostic",   "description": "Explaining why it happened"},
    {"level": 3, "label": "Predictive",   "description": "Forecasting what will happen"},
    {"level": 4, "label": "Prescriptive", "description": "Recommending what to do"},
    {"level": 5, "label": "Cognitive",    "description": "Automated decision-making"},
]

_DIMENSIONS = {"reporting", "analytics", "predictive", "prescriptive", "automation"}

_LEVEL_THRESHOLDS = [
    (3.2, 5),
    (2.4, 4),
    (1.6, 3),
    (0.8, 2),
    (0.0, 1),
]


def classify_maturity_level(answers: dict[str, int | float]) -> int:
    missing = _DIMENSIONS - set(answers.keys())
    if missing:
        raise ValueError(f"Missing dimension(s): {sorted(missing)}")

    avg = sum(float(v) for v in answers.values()) / len(answers)
    for threshold, level in _LEVEL_THRESHOLDS:
        if avg >= threshold:
            return level
    return 1


def get_maturity_label(level: int) -> str:
    if not (1 <= level <= 5):
        raise ValueError(f"Level must be between 1 and 5, got {level}")
    return next(m["label"] for m in MATURITY_LEVELS if m["level"] == level)


def calculate_overall_maturity(answers: dict[str, int | float]) -> dict:
    level = classify_maturity_level(answers)
    return {
        "level": level,
        "label": get_maturity_label(level),
        "dimension_scores": {k: float(v) for k, v in answers.items()},
    }


def main(argv: list[str]) -> int:
    if len(argv) == 2:
        out = None
    elif len(argv) == 4 and argv[2] == "--out":
        out = Path(argv[3])
    else:
        print("Usage: maturity_calculator.py <input.json> [--out <output.json>]", file=sys.stderr)
        return 1
    try:
        result = calculate_overall_maturity(json.loads(Path(argv[1]).read_text()))
        if out is not None:
            out.write_text(json.dumps(result))
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f"maturity_calculator.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result) if out is None else f"level={result['level']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
