# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas==3.1.1", "numpy==2.4.6"]
# ///
"""Phase 9: check the willingness to pay (WTP) of a survey file against the economic value.

usage: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_phase_9.py --input '<wtp survey>' --p7 '<session_dir>/p7.json' --out '<session_dir>/wtp-results.json'

The input is a CSV with the column `wtp_monthly`, one row for each respondent. The monthly EVC is
`total_annual_evc` of the opportunity with `rank` 1 in `top_evc_opportunities` of --p7, divided by 12.
The script calls `layer1_outlier_detection()` and `validate_all_layers()` of `scripts/wtp_validator.py`
with no benchmarks, and writes `{"monthly_evc", "layer1", "validation"}` to --out.
Exit 0: the file is written, and one line `passed=<true|false>` is on stdout. Exit 1: an input error,
for example no data (1 line on stderr, no file). Exit 2: usage.
"""
import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.wtp_validator import WTPValidator  # noqa: E402

WTP_COLUMN = "wtp_monthly"


def monthly_evc(p7):
    """The monthly EVC of the top opportunity of a p7 object."""
    top = p7.get("top_evc_opportunities") if isinstance(p7, dict) else None
    if not isinstance(top, list) or not top:
        raise ValueError("p7.json has no top_evc_opportunities")
    first = next((o for o in top if isinstance(o, dict) and o.get("rank") == 1), None)
    if first is None:
        raise ValueError("p7.json has no opportunity with rank 1")
    annual = first.get("total_annual_evc")
    if isinstance(annual, bool) or not isinstance(annual, (int, float)):
        raise ValueError("total_annual_evc of rank 1 must be a number")
    return float(annual) / 12


def _plain(value):
    """json.dumps hook: a numpy number or bool becomes a plain value."""
    if isinstance(value, (np.generic,)):
        return value.item()
    raise TypeError("cannot write %s" % type(value).__name__)


def run(input_path, p7_path, out_path):
    """Validate the file and write the result. Returns the overall result (bool)."""
    evc = monthly_evc(json.loads(Path(p7_path).read_text(encoding="utf-8")))
    df = pd.read_csv(input_path)
    if WTP_COLUMN not in df.columns:
        raise ValueError("the input has no column %s" % WTP_COLUMN)
    validator = WTPValidator(df[WTP_COLUMN], evc=evc)  # raises ValueError on empty data
    layer1 = validator.layer1_outlier_detection()
    validation = validator.validate_all_layers()
    payload = {"monthly_evc": evc, "layer1": layer1, "validation": validation}
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=_plain), encoding="utf-8")
    return bool(validation["overall_passed"])


def main(argv=None):
    parser = argparse.ArgumentParser(prog="run_phase_9.py", description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="the WTP survey CSV")
    parser.add_argument("--p7", required=True, help="the file p7.json")
    parser.add_argument("--out", required=True, help="the result file")
    args = parser.parse_args(argv)  # exits 2 on a usage error
    try:
        passed = run(args.input, args.p7, args.out)
    except (OSError, ValueError, KeyError, pd.errors.ParserError) as err:
        print("run_phase_9.py: %s" % err, file=sys.stderr)
        return 1
    print("passed=%s" % ("true" if passed else "false"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
