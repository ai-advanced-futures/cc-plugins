# /// script
# requires-python = ">=3.11"
# dependencies = ["pydantic>=2.0.0", "pandas>=1.5.0"]
# ///
"""Entry point: run M&A pipeline (Phase 0–6) using PipelineOrchestrator.

Usage:
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_investigation.py <input_file.json>

Input: JSON file with all phase inputs.
Output: PipelineResult.to_summary() printed as JSON to stdout.

Phase 3 (Operational DD) and Phase 4 (Financial DD) run in parallel.
See run_pipeline.py for more usage examples.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corporate_development.main import run_pipeline  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_investigation.py <input_file.json>", file=sys.stderr)
        sys.exit(1)

    try:
        with open(sys.argv[1]) as f:
            user_input = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = run_pipeline(user_input)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Pipeline error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
