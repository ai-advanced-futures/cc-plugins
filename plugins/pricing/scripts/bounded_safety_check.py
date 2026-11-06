# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Print the bounded-product safety-check row for one class match and one cost ratio.

    uv run "${CLAUDE_PLUGIN_ROOT}/scripts/bounded_safety_check.py" <class slug | None> <ratio | None>

Prints `<determination>|<matched_row>|<reason>`. Exits 1 with the message on a bad value.
"""

import sys
from pathlib import Path

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from pricing.lib.bounded_product_safety_check import apply_matrix  # noqa: E402


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 1
    class_match = None if argv[0] == "None" else argv[0]
    try:
        ratio = None if argv[1] == "None" else float(argv[1])
        result = apply_matrix(class_match, ratio)
    except ValueError as err:
        print("bounded_safety_check.py: %s" % err, file=sys.stderr)
        return 1
    print("%s|%s|%s" % (result.determination, result.matched_row, result.reason))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
