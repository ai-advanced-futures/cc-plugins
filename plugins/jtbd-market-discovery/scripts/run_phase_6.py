# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas==3.1.1"]
# ///
"""Phase 6: score the needs of an ODI-mapped survey file.

usage: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_phase_6.py --input '<session_dir>/survey-odi.csv' --out '<session_dir>/p6-scores.json'

The input is the file that `survey_adapter.py apply` wrote: a CSV with the columns `importance` and
`satisfaction`. The script calls `score_needs_dataframe`, `categorize_opportunities` and
`get_top_opportunities(n=20)` of `scripts/opportunity_scorer.py` and writes
`{"scored": [...], "top_opportunities": [...]}` to --out. Exit 0: the file is written, and one line
`rows=<n> top=<n>` is on stdout. Exit 1: an input error (1 line on stderr, no file). Exit 2: usage.
"""
import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

import pandas as pd  # noqa: E402

from scripts.opportunity_scorer import (  # noqa: E402
    categorize_opportunities,
    get_top_opportunities,
    score_needs_dataframe,
)

TOP_N = 20


def _records(frame):
    """The rows of a frame as plain JSON values (NaN becomes null)."""
    return json.loads(frame.to_json(orient="records"))


def run(input_path, out_path):
    """Score the file and write the result. Returns (rows, top)."""
    df = pd.read_csv(input_path)
    scored = categorize_opportunities(score_needs_dataframe(df))
    top = get_top_opportunities(scored, n=TOP_N)
    payload = {"scored": _records(scored), "top_opportunities": _records(top)}
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return len(scored), len(top)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="run_phase_6.py", description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="the ODI-mapped survey CSV")
    parser.add_argument("--out", required=True, help="the result file")
    args = parser.parse_args(argv)  # exits 2 on a usage error
    try:
        rows, top = run(args.input, args.out)
    except (OSError, ValueError, KeyError, pd.errors.ParserError) as err:
        print("run_phase_6.py: %s" % err, file=sys.stderr)
        return 1
    print("rows=%d top=%d" % (rows, top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
