# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.17.0"]
# ///
"""Print the effective cost of one archetype, with telemetry baselines when a file is given.

    uv run "${CLAUDE_PLUGIN_ROOT}/scripts/telemetry_effective_cost.py" '<JSON object>'

The object holds `archetype`, `headline_price`, `p75`, `p95`, `present_amplifiers` and
`telemetry_path` (null when there is none). Prints `<data_source> <median> <p95>`, then
`raw_baseline <telemetry baseline, or None>`.
"""

import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from pricing.lib.amplifier_composer import AmplifierCompositeResult  # noqa: E402
from pricing.lib.archetype_baseline_loader import load_archetype_baselines  # noqa: E402
from pricing.lib.cost_taxonomy import effective_cost  # noqa: E402


def main(argv):
    if len(argv) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 1
    try:
        args = json.loads(argv[0])
        archetype, p75, p95 = args["archetype"], float(args["p75"]), float(args["p95"])
        tb = load_archetype_baselines(args["telemetry_path"])  # {} when absent
        comp = AmplifierCompositeResult(mean=p75, p50=p75 * 0.7, p75=p75, p95=p95,
                                        present_amplifiers=list(args["present_amplifiers"]))
        r = effective_cost(archetype, headline_price=float(args["headline_price"]),
                           amplifier_composite=comp, telemetry_baselines=tb)
    except (KeyError, TypeError, ValueError) as err:
        print("telemetry_effective_cost.py: %s" % err, file=sys.stderr)
        return 1
    print(r.data_source, r.median_effective_per_interaction, r.p95_effective_per_interaction)
    # the RAW baseline (before amplification) goes on to sensitivity_matrix, never the median
    print("raw_baseline", tb[archetype].baseline_cost_per_interaction if archetype in tb else None)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
