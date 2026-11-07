# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""DAMA-DMBOK Knowledge Area scorer.

Scores intake answers against the 11 DAMA Knowledge Areas (DMBOK2).
All scoring is deterministic — no LLM calls.

Command line: dama_scorer.py <input.json> [--out <output.json>]
The input file holds the dama_answers object. Without --out, the script prints one JSON object.
With --out, the script writes the JSON object to the output file and prints one line.
After an error, the script writes no output file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

KNOWLEDGE_AREAS = [
    {"id": "data_governance",    "name": "Data Governance"},
    {"id": "data_architecture",  "name": "Data Architecture"},
    {"id": "data_modeling",      "name": "Data Modeling & Design"},
    {"id": "data_storage",       "name": "Data Storage & Operations"},
    {"id": "data_security",      "name": "Data Security"},
    {"id": "data_integration",   "name": "Data Integration & Interoperability"},
    {"id": "document_content",   "name": "Document & Content Management"},
    {"id": "reference_master",   "name": "Reference & Master Data"},
    {"id": "data_warehousing",   "name": "Data Warehousing & Business Intelligence"},
    {"id": "metadata_management", "name": "Metadata Management"},
    {"id": "data_quality",       "name": "Data Quality"},
]

_KA_IDS = {ka["id"] for ka in KNOWLEDGE_AREAS}


def classify_gap(score: float) -> str:
    """Classify a score as none / minor / major gap."""
    if score >= 3.0:
        return "none"
    if score >= 2.0:
        return "minor"
    return "major"


def score_knowledge_area(ka_id: str, raw_score: int | float) -> float:
    """Validate and return score for a single KA."""
    if ka_id not in _KA_IDS:
        raise ValueError(f"Unknown knowledge area: '{ka_id}'. Valid IDs: {sorted(_KA_IDS)}")
    if not (0 <= raw_score <= 4):
        raise ValueError(f"Score must be between 0 and 4, got {raw_score}")
    return float(raw_score)


def score_all_kas(answers: dict[str, int | float]) -> dict:
    """Score all 11 DAMA knowledge areas."""
    missing = _KA_IDS - set(answers.keys())
    if missing:
        raise ValueError(f"Missing knowledge area(s): {sorted(missing)}")

    scores = {ka_id: score_knowledge_area(ka_id, val) for ka_id, val in answers.items()}
    overall = sum(scores.values()) / len(scores)
    return {
        "scores": scores,
        "overall_score": round(overall, 2),
        "gap_flag": classify_gap(overall),
    }


def main(argv: list[str]) -> int:
    if len(argv) == 2:
        out = None
    elif len(argv) == 4 and argv[2] == "--out":
        out = Path(argv[3])
    else:
        print("Usage: dama_scorer.py <input.json> [--out <output.json>]", file=sys.stderr)
        return 1
    try:
        result = score_all_kas(json.loads(Path(argv[1]).read_text()))
        if out is not None:
            out.write_text(json.dumps(result))
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f"dama_scorer.py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result) if out is None else f"overall_score={result['overall_score']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
