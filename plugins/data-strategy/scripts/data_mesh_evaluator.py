# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Data Mesh principle evaluator (Dehghani 4 Principles).

Scores each of the four Data Mesh principles on a 0.0–1.0 scale.

Command line: data_mesh_evaluator.py <input.json>
The input file holds the mesh_answers object. The script prints one JSON object.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PRINCIPLES = [
    {"id": "domain_ownership",     "name": "Domain Ownership"},
    {"id": "data_as_product",      "name": "Data as a Product"},
    {"id": "self_serve",           "name": "Self-Serve Infrastructure"},
    {"id": "federated_governance", "name": "Federated Computational Governance"},
]

_PRINCIPLE_IDS = {p["id"] for p in PRINCIPLES}


def classify_mesh_compliance(score: float) -> str:
    if score >= 0.7:
        return "high"
    if score >= 0.3:
        return "partial"
    return "low"


def score_principle(principle_id: str, raw_score: float) -> float:
    if principle_id not in _PRINCIPLE_IDS:
        raise ValueError(f"Unknown principle: '{principle_id}'. Valid: {sorted(_PRINCIPLE_IDS)}")
    if not (0.0 <= raw_score <= 1.0):
        raise ValueError(f"Score must be between 0.0 and 1.0, got {raw_score}")
    return float(raw_score)


def score_all_principles(answers: dict[str, float]) -> dict:
    missing = _PRINCIPLE_IDS - set(answers.keys())
    if missing:
        raise ValueError(f"Missing principle(s): {sorted(missing)}")

    scores = {pid: score_principle(pid, val) for pid, val in answers.items()}
    overall = sum(scores.values()) / len(scores)
    return {
        "scores": scores,
        "overall_score": round(overall, 3),
        "compliance": classify_mesh_compliance(overall),
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: data_mesh_evaluator.py <input.json>", file=sys.stderr)
        return 1
    try:
        result = score_all_principles(json.loads(Path(argv[1]).read_text()))
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f"data_mesh_evaluator.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
