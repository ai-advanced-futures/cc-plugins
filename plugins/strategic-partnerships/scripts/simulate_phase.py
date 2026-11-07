# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
simulate_phase.py — Pre-flight simulator for strategic-partnerships phase dispatch.

Run: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/simulate_phase.py --phase P --session-id ID [--out FILE]
The script reads `.sp-tmp/<session_id>/` in the current folder. Each `<x>.md` file counts as
the available input `<x>_output`. It prints the JSON result.

Checks whether required inputs are available before dispatching a phase agent.
Returns a confidence rating (HIGH / MEDIUM / LOW) and a list of missing inputs.

With `--out`, the script writes the result to the file and prints 1 line.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Same value as SP_TMP_DIR in session_manager.py; each script is a single file.
SP_TMP_DIR = ".sp-tmp"

PHASE_REQUIRED_INPUTS: dict[str, list[str]] = {
    "assess": [],
    "discover": ["assess_output"],
    "structure": ["assess_output", "discover_output"],
    "architect": ["assess_output", "discover_output"],
    "monetize": ["assess_output", "structure_output"],
    "synthesize": [
        "assess_output",
        "discover_output",
        "structure_output",
        "architect_output",
        "monetize_output",
    ],
}


def simulate_phase(phase: str, available_inputs: list[str]) -> dict:
    """Check whether required inputs are available before dispatching a phase agent.

    Args:
        phase: One of the 6 phases defined in PHASE_REQUIRED_INPUTS.
        available_inputs: List of input keys that are currently available.

    Returns:
        dict with keys:
            "phase"      — the phase name
            "confidence" — "HIGH" | "MEDIUM" | "LOW"
            "missing"    — list of required inputs not present in available_inputs

    Raises:
        ValueError: If `phase` is not a recognised phase name.
    """
    if phase not in PHASE_REQUIRED_INPUTS:
        raise ValueError(
            f"Unknown phase: '{phase}'. Valid phases: {sorted(PHASE_REQUIRED_INPUTS)}"
        )

    required = PHASE_REQUIRED_INPUTS[phase]
    available_set = set(available_inputs)
    missing = [inp for inp in required if inp not in available_set]

    # Confidence logic
    if len(required) == 0:
        confidence = "HIGH"
    elif len(missing) == 0:
        confidence = "HIGH"
    elif len(missing) == len(required):
        confidence = "LOW"
    else:
        confidence = "MEDIUM"

    return {"phase": phase, "confidence": confidence, "missing": missing}


def available_inputs(session_dir: Path) -> list[str]:
    """The inputs of a session folder: `<x>_output` for each `<x>.md` file."""
    if not session_dir.is_dir():
        raise ValueError(f"Session not found: {session_dir.name}")
    return sorted(f"{path.stem}_output" for path in session_dir.glob("*.md"))


def session_id_arg(value: str) -> str:
    """Accept a plain name only, so the path stays inside `.sp-tmp/`. Same check as session_manager.py."""
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", value) or value in (".", ".."):
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a plain name (1 to 64 characters of A-Z, a-z, 0-9, '.', '_' and '-')"
        )
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--phase", required=True, choices=sorted(PHASE_REQUIRED_INPUTS))
    parser.add_argument("--session-id", required=True, type=session_id_arg)
    parser.add_argument("--out", help="write the result to this file and print one line")
    args = parser.parse_args(argv)
    try:
        result = simulate_phase(args.phase, available_inputs(Path(SP_TMP_DIR) / args.session_id))
        text = json.dumps(result, indent=2)
        if args.out:
            Path(args.out).write_text(text + "\n")
    except (OSError, ValueError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(f"confidence={result['confidence']}" if args.out else text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
