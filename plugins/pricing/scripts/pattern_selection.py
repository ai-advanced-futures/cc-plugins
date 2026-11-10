# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.17.0", "pyyaml>=6.0"]
# ///
"""Print rows of the pattern catalogue, or write the pattern-selection file for the patterns of the input file.

    uv run "${CLAUDE_PLUGIN_ROOT}/scripts/pattern_selection.py" --catalogue P4 P9 P15
    uv run "${CLAUDE_PLUGIN_ROOT}/scripts/pattern_selection.py" --input .pricing/pattern-selection-input.json --out .pricing/pattern-selection.json

`--catalogue` prints 1 line `<pattern_id>|<acv_band>|<audience_default>|<name>` for each pattern id (for each
pattern of the catalogue when no id is given). The input file holds `patterns` (a list, each item with `pattern_id`,
and it can have `rationale`), and it can hold `customer_facing_name`, `dependencies` and `engagement_id`. The
script reads `PATTERNS` of `pricing.lib.pattern_catalogue`, takes `acv_band` from it, checks the result against
`pattern-selection.schema.json`, and writes it. Prints `selected=<ids> name=<customer_facing_name>`, then the
`engagement_id` and its source, then `wrote <file>`. Each file is a `.json` file in the `.pricing` folder of the project.
Exit 1: an input error (1 line on stderr, no file). Exit 2: usage.
"""

import sys
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from pricing.lib import handoff_file  # noqa: E402
from pricing.lib.pattern_catalogue import PATTERNS  # noqa: E402

SCHEMA = "pattern-selection.schema.json"
NAME = "pattern_selection.py"


def pattern(pattern_id):
    if not isinstance(pattern_id, str) or pattern_id not in PATTERNS:
        raise ValueError("%r is not a pattern id of the catalogue" % (pattern_id,))
    return PATTERNS[pattern_id]


def build(data):
    patterns = data.get("patterns")
    if not isinstance(patterns, list) or not patterns:
        raise ValueError("patterns must be a list with one item or more")
    selected, names = [], []
    for index, entry in enumerate(patterns):
        if not isinstance(entry, dict):
            raise ValueError("patterns[%d] must be an object" % index)
        found = pattern(entry.get("pattern_id"))
        if found.pattern_id in [row["pattern_id"] for row in selected]:
            raise ValueError("patterns: %s is there 2 times" % found.pattern_id)
        selected.append({"pattern_id": found.pattern_id, "acv_band": found.acv_band,
                         "rationale": handoff_file.text(entry, "rationale", found.description[:500])})
        names.append(found.name)
    ids = [row["pattern_id"] for row in selected]
    dependencies = data.get("dependencies", [])
    if not isinstance(dependencies, list):
        raise ValueError("dependencies must be a list")
    for index, entry in enumerate(dependencies):
        for key in ("pattern_id", "depends_on_pattern_id"):
            if not isinstance(entry, dict) or entry.get(key) not in ids:
                raise ValueError("dependencies[%d]: %s must be one of the selected patterns" % (index, key))
        if entry["pattern_id"] == entry["depends_on_pattern_id"]:
            raise ValueError("dependencies[%d]: a pattern cannot depend on itself" % index)
    name = handoff_file.text(data, "customer_facing_name", " + ".join(names))
    result = {**handoff_file.envelope(data), "selected_patterns": selected, "customer_facing_name": name,
              "dependencies": dependencies, "audience": "mixed"}
    handoff_file.check(result, SCHEMA)
    return result, "selected=%s name=%s" % (",".join(ids), name)


def catalogue(ids):
    try:
        rows = [pattern(pattern_id) for pattern_id in ids] if ids else list(PATTERNS.values())
    except ValueError as err:
        print("%s: %s" % (NAME, err), file=sys.stderr)
        return 1
    for row in rows:
        print("%s|%s|%s|%s" % (row.pattern_id, row.acv_band, row.audience_default, row.name))
    return 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["--catalogue"]:
        sys.exit(catalogue(sys.argv[2:]))
    sys.exit(handoff_file.run(NAME, sys.argv[1:], build))
