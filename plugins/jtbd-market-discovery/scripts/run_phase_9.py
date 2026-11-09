# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas==3.1.1", "numpy==2.4.6"]
# ///
"""Phase 9: check the willingness to pay (WTP) of a survey file against the economic value.

usage: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_phase_9.py --input '<wtp survey>' --p7 '<session_dir>/p7.json' --out '<session_dir>/wtp-results.json' [--segment-column '<column>' [--p8 '<session_dir>/p8.json']]

The input is a CSV with the column `wtp_monthly`, one row for each respondent. The monthly EVC is
`total_annual_evc` of the opportunity with `rank` 1 in `top_evc_opportunities` of --p7, divided by 12.
The script calls `layer1_outlier_detection()` and `validate_all_layers()` of `scripts/wtp_validator.py`
with no benchmarks, and writes `{"monthly_evc", "layer1", "validation"}` to --out.
With --segment-column, the file also holds `segment_column` and `segments`: 1 entry for each value of that
column, in the order of the first row of each value. An entry holds `segment_id` (the value as text), `name`
(the `name` of the --p8 segment with that `segment_id`, else null), `rows`, `layer1`, `wtp_analysis` (the keys
of `wtp_analysis` in p9.json), `validation`, and `van_westendorp`. `van_westendorp` needs the columns too_cheap,
bargain, getting_expensive and too_expensive; without them it is null and `van_westendorp_gap` says why.
Exit 0: the file is written, and one line `passed=<true|false>` is on stdout. Exit 1: an input error,
for example no data or no column --segment-column (1 line on stderr, no file). Exit 2: usage.
"""
import argparse
import json
import math
import sys
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.wtp_validator import WTPValidator  # noqa: E402

WTP_COLUMN = "wtp_monthly"
VW_COLUMNS = ("too_cheap", "bargain", "getting_expensive", "too_expensive")


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


def _finite(value):
    """A number that JSON can hold: NaN and infinity become None (a 1-row segment has no std)."""
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: _finite(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_finite(v) for v in value]
    return value


def kept_rows(wtp):
    """The rows that layer 1 keeps: the IQR bounds of WTPValidator.layer1_outlier_detection."""
    q1, q3 = wtp.quantile(0.25), wtp.quantile(0.75)
    iqr = q3 - q1
    return wtp[(wtp >= q1 - 1.5 * iqr) & (wtp <= q3 + 1.5 * iqr)].index


def crossing(falling, rising):
    """The price where a falling curve meets a rising curve.

    `falling` holds the answers of a "cheap" question: its share at price p is the share of answers >= p.
    `rising` holds the answers of an "expensive" question: its share at price p is the share of answers <= p.
    The candidate prices are the answers of both columns. `low` is the highest candidate where the falling share
    is at or above the rising share, and `high` is the lowest candidate where it is at or below. So a price where
    the 2 shares are equal is part of the crossing. The crossing is the midpoint of `low` and `high`.
    """
    prices = sorted(set(falling.tolist()) | set(rising.tolist()))
    gap = [((falling >= p).mean() - (rising <= p).mean(), p) for p in prices]
    low = max((p for d, p in gap if d >= 0), default=prices[0])
    high = min((p for d, p in gap if d <= 0), default=prices[-1])
    return round((low + high) / 2, 2)


def van_westendorp(frame):
    """The Van Westendorp price points of the rows of 1 segment, or None when no row has 4 ordered answers."""
    answers = frame[list(VW_COLUMNS)].apply(pd.to_numeric, errors="coerce").dropna()
    ordered = answers[(answers["too_cheap"] <= answers["bargain"])
                      & (answers["bargain"] <= answers["getting_expensive"])
                      & (answers["getting_expensive"] <= answers["too_expensive"])]
    if ordered.empty:
        return None
    low = crossing(ordered["too_cheap"], ordered["getting_expensive"])
    high = crossing(ordered["bargain"], ordered["too_expensive"])
    result = {column: float(ordered[column].median()) for column in VW_COLUMNS}
    result.update({
        "rows": len(ordered),
        "point_of_marginal_cheapness": low,
        "optimal_price_point": crossing(ordered["too_cheap"], ordered["too_expensive"]),
        "indifference_price_point": crossing(ordered["bargain"], ordered["getting_expensive"]),
        "point_of_marginal_expensiveness": high,
        "acceptable_range": [low, high],
    })
    if low > high:  # the 2 crossings use other answer prices, so a small segment can give PMC above PME
        result["acceptable_range"] = None
        result["range_gap"] = "PMC %s is above PME %s, so the survey gives no acceptable range" % (low, high)
    return result


def wtp_analysis(wtp, layer1):
    """The `wtp_analysis` block of p9.json for 1 segment."""
    mean, std = layer1["clean_mean"], layer1["clean_std"]
    return {
        "raw_mean": float(wtp.mean()), "raw_median": float(wtp.median()), "raw_std_dev": float(wtp.std()),
        "sample_size": int(len(wtp)), "outliers_removed": int(layer1["outliers_removed"]),
        "cleaned_mean": mean, "cleaned_median": layer1["clean_median"], "cleaned_std_dev": std,
        "coefficient_of_variation": (std / mean) if mean and mean > 0 else None,
    }


def segment_names(p8_path):
    """The p8 segment names by segment_id (as text)."""
    if not p8_path:
        return {}
    p8 = json.loads(Path(p8_path).read_text(encoding="utf-8"))
    return {str(s.get("segment_id")): s.get("name") for s in (p8.get("segments") or [])
            if isinstance(s, dict) and s.get("segment_id") is not None}


def segments(df, column, evc, names):
    """1 entry for each value of the segment column."""
    has_vw = all(c in df.columns for c in VW_COLUMNS)
    found = []
    for value, rows in df.groupby(column, sort=False, dropna=True):
        wtp = pd.to_numeric(rows[WTP_COLUMN], errors="coerce").dropna()
        entry = {"segment_id": str(value), "name": names.get(str(value)), "rows": len(rows)}
        if wtp.empty:
            entry.update({"layer1": None, "wtp_analysis": None, "validation": None, "van_westendorp": None})
        else:
            validator = WTPValidator(wtp, evc=evc)
            layer1 = validator.layer1_outlier_detection()
            entry.update({"layer1": layer1, "wtp_analysis": wtp_analysis(wtp, layer1),
                          "validation": validator.validate_all_layers(),
                          "van_westendorp": van_westendorp(rows.loc[kept_rows(wtp)]) if has_vw else None})
        found.append(_finite(entry))
    return found


def run(input_path, p7_path, out_path, segment_column=None, p8_path=None):
    """Validate the file and write the result. Returns the overall result (bool)."""
    evc = monthly_evc(json.loads(Path(p7_path).read_text(encoding="utf-8")))
    df = pd.read_csv(input_path, dtype={segment_column: str} if segment_column else None)
    if WTP_COLUMN not in df.columns:
        raise ValueError("the input has no column %s" % WTP_COLUMN)
    if segment_column and segment_column not in df.columns:
        raise ValueError("the input has no column %s (--segment-column); its columns are: %s"
                         % (segment_column, ", ".join(map(str, df.columns))))
    validator = WTPValidator(df[WTP_COLUMN], evc=evc)  # raises ValueError on empty data
    layer1 = validator.layer1_outlier_detection()
    validation = validator.validate_all_layers()
    payload = {"monthly_evc": evc, "layer1": layer1, "validation": validation}
    if segment_column:
        payload["segment_column"] = segment_column
        payload["segments"] = segments(df, segment_column, evc, segment_names(p8_path))
        missing = [c for c in VW_COLUMNS if c not in df.columns]
        if missing:
            payload["van_westendorp_gap"] = "the input has no column %s" % ", ".join(missing)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=_plain), encoding="utf-8")
    return bool(validation["overall_passed"])


def main(argv=None):
    parser = argparse.ArgumentParser(prog="run_phase_9.py", description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="the WTP survey CSV")
    parser.add_argument("--p7", required=True, help="the file p7.json")
    parser.add_argument("--out", required=True, help="the result file")
    parser.add_argument("--segment-column", help="the column of the segment of each row, for example segment_id")
    parser.add_argument("--p8", help="the file p8.json, for the name of each segment (needs --segment-column)")
    args = parser.parse_args(argv)  # exits 2 on a usage error
    if args.p8 and not args.segment_column:
        parser.error("--p8 needs --segment-column")
    try:
        passed = run(args.input, args.p7, args.out, args.segment_column, args.p8)
    except (OSError, ValueError, KeyError, pd.errors.ParserError) as err:
        print("run_phase_9.py: %s" % err, file=sys.stderr)
        return 1
    print("passed=%s" % ("true" if passed else "false"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
