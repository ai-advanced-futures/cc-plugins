# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Compute the S1 to S5 stress matrix for the pricing model of the input file and write the sensitivity-stress file.

    uv run "${CLAUDE_PLUGIN_ROOT}/scripts/sensitivity_stress.py" --input .pricing/sensitivity-stress-input.json --out .pricing/sensitivity-stress.json

The input file holds `archetype`, `headline_price` and `pricing_unit`. It can hold `cost_per_interaction_baseline`
(the raw baseline, before amplification); with none, the script uses the baseline of the archetype in
`_BASELINE_COST` of `pricing.lib.cost_taxonomy`. For the composite amplifier it holds `readout` (the path of a
cost-amplifier-readout file in `.pricing`), or `composite_p75` with `present_amplifiers` (a list of amplifier
numbers). The script calls `compute_sensitivity` of `pricing.lib.sensitivity_matrix` and writes the 5 margins and
`narrative_md_per_scenario`. Prints `s1=<m> s2=<m> s3=<m> s4=<m> s5=<m> baseline=<b> source=<s>` (margins in
percent; the source is `input`, `framework_table` or `inferred_v1_4_0`), then `wrote <file>`.
Each file is a `.json` file in the `.pricing` folder of the project.
Exit 1: an input error (1 line on stderr, no file). Exit 2: usage.
"""

import sys
from dataclasses import asdict
from pathlib import Path
from typing import get_args

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from pricing.lib import handoff_file  # noqa: E402
from pricing.lib.amplifier_composer import AmplifierCompositeResult  # noqa: E402
from pricing.lib.cost_taxonomy import _BASELINE_COST  # noqa: E402
from pricing.lib.sensitivity_matrix import PricingModelInput, PricingUnit, compute_sensitivity  # noqa: E402

MARGINS = ("s1_base_margin_pct", "s2_inference_50_margin_pct", "s3_volume_200_margin_pct", "s4_loop_3x_margin_pct",
           "s5_combined_margin_pct")


def composite(data):
    """The 2 values of the composite that `compute_sensitivity` reads: p75 and the present amplifiers."""
    if "readout" in data:
        readout = handoff_file.read_input(handoff_file.text(data, "readout"), "the readout file")
        amplifiers = readout.get("amplifiers")
        if not isinstance(amplifiers, dict):
            raise ValueError("the readout file has no amplifiers object")
        present = sorted(int(key) for key, entry in amplifiers.items()
                         if key.isdigit() and isinstance(entry, dict) and entry.get("present") is True)
        return handoff_file.number(readout, "composite_p75", "readout: "), present
    present = data.get("present_amplifiers")
    if not isinstance(present, list) or any(type(item) is not int or not 1 <= item <= 8 for item in present):
        raise ValueError("give readout, or composite_p75 with present_amplifiers (a list of numbers from 1 to 8)")
    return handoff_file.number(data, "composite_p75"), present


def build(data):
    archetype, unit = handoff_file.text(data, "archetype"), handoff_file.text(data, "pricing_unit")
    if unit not in get_args(PricingUnit):
        raise ValueError("pricing_unit %r is not one of %s" % (unit, ", ".join(get_args(PricingUnit))))
    if archetype not in _BASELINE_COST:
        raise ValueError("archetype %r is not one of %s" % (archetype, ", ".join(sorted(_BASELINE_COST))))
    price = handoff_file.number(data, "headline_price")
    if data.get("cost_per_interaction_baseline") is None:  # no raw baseline given: the value of the library table
        cost, source = _BASELINE_COST[archetype]
    else:
        cost, source = handoff_file.number(data, "cost_per_interaction_baseline"), "input"
    if price <= 0 or cost < 0:
        raise ValueError("headline_price must be more than 0, and cost_per_interaction_baseline must not be less than 0")
    p75, present = composite(data)
    if p75 < 1:
        raise ValueError("composite_p75 must be 1 or more")
    model = PricingModelInput(archetype=archetype, headline_price=price, pricing_unit=unit,
                              cost_per_interaction_baseline=cost)
    # compute_sensitivity reads only p75 and present_amplifiers of the composite.
    amplifier = AmplifierCompositeResult(mean=p75, p50=p75, p75=p75, p95=p75, present_amplifiers=present)
    result = asdict(compute_sensitivity(archetype, model, amplifier))
    line = " ".join("%s=%.1f" % (key.split("_")[0], result[key]) for key in MARGINS)
    return result, "%s baseline=%s source=%s" % (line, cost, source)


if __name__ == "__main__":
    sys.exit(handoff_file.run("sensitivity_stress.py", sys.argv[1:], build))
