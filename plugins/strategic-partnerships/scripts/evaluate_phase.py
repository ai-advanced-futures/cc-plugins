# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
evaluate_phase.py — Post-execution phase output evaluator.

Run: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/evaluate_phase.py --phase P --session-id ID
The script reads `<P>.md` in `.sp-tmp/<session_id>/` of the current folder and prints the
JSON result.

Checks whether a phase agent's output text contains the expected rubric
sections. Returns a structured result dict with pass/fail verdict and
a list of any missing rubric items.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Same value as SP_TMP_DIR in session_manager.py; each script is a single file.
SP_TMP_DIR = ".sp-tmp"

PHASE_RUBRICS = {
    "assess": [
        "partnership_archetype",
        "power_position",
        "readiness_gaps",
    ],
    "discover": [
        "priority_a_candidates",
        "ecosystem_health",
        "power_dynamics",
    ],
    "structure": [
        "model_type",
        "revenue_streams",
        "term_sheet_outline",
    ],
    "architect": [
        "integration_pattern",
        "api_boundary",
        "data_flows",
    ],
    "monetize": [
        "revenue_projections",
        "npv_estimate",
        "roi_verdict",
    ],
    "synthesize": [
        "go_no_go_recommendation",
        "risk_register",
        "next_steps",
    ],
}


def evaluate_phase(phase: str, output_text: str) -> dict:
    """Evaluate a phase agent's output against its rubric.

    Args:
        phase: One of the 6 phase names defined in PHASE_RUBRICS.
        output_text: The markdown text produced by the phase agent.

    Returns:
        {
            "phase": str,
            "result": "PASS" | "FAIL",
            "gaps": list[str],  # rubric items NOT found in output_text
        }

    Raises:
        ValueError: If phase is not in PHASE_RUBRICS.
    """
    if phase not in PHASE_RUBRICS:
        raise ValueError(
            f"unknown phase '{phase}'; valid phases: {sorted(PHASE_RUBRICS.keys())}"
        )

    rubric_items = PHASE_RUBRICS[phase]
    lowered = output_text.lower()

    gaps = [item for item in rubric_items if item.lower() not in lowered]

    return {
        "phase": phase,
        "result": "PASS" if not gaps else "FAIL",
        "gaps": gaps,
    }


def session_id_arg(value: str) -> str:
    """Accept a plain name only, so the path stays inside `.sp-tmp/`. Same check as session_manager.py."""
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", value) or value in (".", ".."):
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a plain name (1 to 64 characters of A-Z, a-z, 0-9, '.', '_' and '-')"
        )
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--phase", required=True, choices=sorted(PHASE_RUBRICS))
    parser.add_argument("--session-id", required=True, type=session_id_arg)
    args = parser.parse_args(argv)
    try:
        text = (Path(SP_TMP_DIR) / args.session_id / f"{args.phase}.md").read_text()
        result = evaluate_phase(args.phase, text)
    except (OSError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
