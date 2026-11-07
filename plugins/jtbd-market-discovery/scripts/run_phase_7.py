# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Phase 7: compute the economic value (EVC) of each need.

usage: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/run_phase_7.py --input '<session_dir>/evc-input.json' --out '<session_dir>/evc-results.json'

The input is the file `evc-input.json` that the agent evc-calculator wrote (step `inputs`):

    {"assumptions": {"labor_rate", "average_error_cost", "average_revenue", "revenue_margin", "risk_tolerance"},
     "assumption_sources": {...}, "differentiation_level": "low|medium|high",
     "needs": [{"need_id", "need", "opportunity_score", "hours_saved_per_year", "errors_avoided_per_year",
                "revenue_increase_per_year", "risk_probability", "prevention_rate", "risk_impact", "basis"}]}

For each need the script makes a new `EVCCalculator` and calls `add_time_savings`, `add_error_reduction`,
`add_revenue_increase` (the revenue times `revenue_margin`), `add_risk_reduction` (the probability times
`prevention_rate`) and `calculate_total_evc`. It writes the input fields and one result for each need to --out.
Exit 0: the file is written, and one line `needs=<n>` is on stdout. Exit 1: an input error (1 line on
stderr, no file). Exit 2: usage.
"""
import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run ${CLAUDE_PLUGIN_ROOT}/scripts/<file>.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from scripts.evc_calculator import EVCCalculator  # noqa: E402

ASSUMPTIONS = ("labor_rate", "average_error_cost", "average_revenue", "revenue_margin", "risk_tolerance")
NEED_NUMBERS = (
    "hours_saved_per_year",
    "errors_avoided_per_year",
    "revenue_increase_per_year",
    "risk_probability",
    "prevention_rate",
    "risk_impact",
)


def _number(source, key, where):
    """A number from the input, with a plain error when it is missing or not a number."""
    value = source.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s: %s must be a number" % (where, key))
    return float(value)


def evaluate(data):
    """The result of each need of the input. Raises ValueError for a bad input."""
    if not isinstance(data, dict):
        raise ValueError("the input must be a JSON object")
    assumptions = data.get("assumptions")
    if not isinstance(assumptions, dict):
        raise ValueError("assumptions must be an object")
    for key in ASSUMPTIONS:
        if key not in assumptions:
            raise ValueError("assumptions: %s is missing" % key)
    needs = data.get("needs")
    if not isinstance(needs, list) or not needs:
        raise ValueError("needs must be a list with one item or more")
    level = data.get("differentiation_level")
    labor_rate = _number(assumptions, "labor_rate", "assumptions")
    error_cost = _number(assumptions, "average_error_cost", "assumptions")
    margin = _number(assumptions, "revenue_margin", "assumptions")
    results = []
    for index, need in enumerate(needs):
        where = "needs[%d]" % index
        if not isinstance(need, dict):
            raise ValueError("%s must be an object" % where)
        values = {key: _number(need, key, where) for key in NEED_NUMBERS}
        calc = EVCCalculator()
        calc.add_time_savings(values["hours_saved_per_year"], hourly_rate=labor_rate)
        calc.add_error_reduction(values["errors_avoided_per_year"], cost_per_error=error_cost)
        calc.add_revenue_increase(values["revenue_increase_per_year"] * margin)
        calc.add_risk_reduction(
            probability=values["risk_probability"] * values["prevention_rate"],
            impact=values["risk_impact"],
        )
        total = calc.calculate_total_evc(level)
        results.append(
            {
                "need_id": need.get("need_id"),
                "need": need.get("need"),
                "opportunity_score": need.get("opportunity_score"),
                "basis": need.get("basis"),
                **total,
            }
        )
    return results


def run(input_path, out_path):
    """Read the input, write the result file. Returns the number of needs."""
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    results = evaluate(data)
    payload = {
        "assumptions": data["assumptions"],
        "assumption_sources": data.get("assumption_sources", {}),
        "differentiation_level": data.get("differentiation_level"),
        "results": results,
    }
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return len(results)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="run_phase_7.py", description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, help="the file evc-input.json")
    parser.add_argument("--out", required=True, help="the result file")
    args = parser.parse_args(argv)  # exits 2 on a usage error
    try:
        count = run(args.input, args.out)
    except (OSError, ValueError, KeyError) as err:  # json.JSONDecodeError is a ValueError
        print("run_phase_7.py: %s" % err, file=sys.stderr)
        return 1
    print("needs=%d" % count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
