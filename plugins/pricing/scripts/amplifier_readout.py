# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.17.0"]
# ///
"""Compose the cost amplifiers of the input file and write the cost-amplifier-readout file.

    uv run "${CLAUDE_PLUGIN_ROOT}/scripts/amplifier_readout.py" --input .pricing/cost-amplifier-input.json --out .pricing/cost-amplifier-readout.json

The input file holds `amplifiers` (each of the keys `1` to `8`, with `present`; an amplifier that is present has
`multiplier_p75` and `multiplier_p95`, and it can have `detection_signal`), and it can hold `notes`, `mode` and
`engagement_id`. The script calls `compose_amplifiers` of `pricing.lib.amplifier_composer`, checks the result
against `cost-amplifier-readout.schema.json`, and writes it. Prints
`composite mean=<m> p50=<m> p75=<m> p95=<m> present=<ids>`, then the `engagement_id` and its source, then
`wrote <file>`.
Each file is a `.json` file in the `.pricing` folder of the project.
Exit 1: an input error (1 line on stderr, no file). Exit 2: usage.
"""

import sys
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from pricing.lib import handoff_file  # noqa: E402
from pricing.lib.amplifier_composer import AmplifierReading, compose_amplifiers  # noqa: E402

SCHEMA = "cost-amplifier-readout.schema.json"
IDS = tuple(str(number) for number in range(1, 9))


def build(data):
    amplifiers = data.get("amplifiers")
    if not isinstance(amplifiers, dict) or not amplifiers:
        raise ValueError("amplifiers must be an object with the keys 1 to 8")
    rows, readings = {}, []
    for key in sorted(amplifiers):
        entry, where = amplifiers[key], "amplifiers.%s: " % key
        if key not in IDS:
            raise ValueError("amplifiers: the key %r is not one of 1 to 8" % key)
        if not isinstance(entry, dict) or not isinstance(entry.get("present"), bool):
            raise ValueError(where + "present must be true or false")
        present = entry["present"]
        p75 = handoff_file.number(entry, "multiplier_p75", where) if present or "multiplier_p75" in entry else 1.0
        p95 = handoff_file.number(entry, "multiplier_p95", where) if present or "multiplier_p95" in entry else 1.0
        rows[key] = {"multiplier_p75": p75, "multiplier_p95": p95,
                     "detection_signal": handoff_file.text(entry, "detection_signal", "n/a"), "present": present}
        readings.append(AmplifierReading(amp_id=int(key), multiplier_p75=p75, multiplier_p95=p95, present=present))
    missing = [key for key in IDS if key not in rows]
    if missing:  # an amplifier with no entry would count as not present, with no sign
        raise ValueError("amplifiers: no entry for %s; give each of 1 to 8, with present false for one that is "
                         "not present" % ", ".join(missing))
    composite = compose_amplifiers(readings)  # ValueError names the amplifier
    result = {**handoff_file.envelope(data), "mode": handoff_file.text(data, "mode", "rule_of_thumb"),
              "amplifiers": rows, "composite_p75": round(composite.p75, 4), "composite_p95": round(composite.p95, 4),
              "notes": handoff_file.text(data, "notes", ""), "audience": "internal"}
    handoff_file.check(result, SCHEMA)
    line = "composite mean=%.4f p50=%.4f p75=%.4f p95=%.4f present=%s" % (
        composite.mean, composite.p50, composite.p75, composite.p95,
        ",".join(str(number) for number in composite.present_amplifiers) or "none")
    return result, line


if __name__ == "__main__":
    sys.exit(handoff_file.run("amplifier_readout.py", sys.argv[1:], build))
