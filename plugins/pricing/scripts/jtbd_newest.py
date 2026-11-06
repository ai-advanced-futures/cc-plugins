# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Print the path of the newest usable jtbd result file.

usage: uv run "${CLAUDE_PLUGIN_ROOT}/scripts/jtbd_newest.py"

It reads `.jtbd-market-discovery/results/*.json` under the working folder and prints
`.jtbd-market-discovery/results/<name>` for the file with the latest `run.finished_at`
whose `results` hold a `willingness_to_pay` entry. When two files have the same time,
the later name wins. It skips a file that is not JSON, a file with no `run.finished_at`
or one with no zone, and a name with a character outside A-Z, a-z, 0-9, '.', '_', '-'.
With no such file it prints nothing and exits 0. An argument exits 2.
Standard library only.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

RESULTS = Path(".jtbd-market-discovery") / "results"
_PLAIN = re.compile(r"[A-Za-z0-9._-]+")


def _finished_at(path):
    """Return the time of a usable file, or None."""
    if not _PLAIN.fullmatch(path.name) or not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        results = doc["results"]
        if not any(isinstance(r, dict) and r.get("kind") == "willingness_to_pay" for r in results):
            return None
        finished = datetime.fromisoformat(doc["run"]["finished_at"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return finished if finished.tzinfo is not None else None


def newest(folder):
    """Return the path of the usable file with the latest time, or None."""
    best = None
    for path in sorted(folder.glob("*.json")):
        finished = _finished_at(path)
        if finished is not None and (best is None or finished >= best[0]):
            best = (finished, path)
    return best[1] if best else None


def main(argv):
    if argv:
        print("usage: jtbd_newest.py (no argument)", file=sys.stderr)
        return 2
    path = newest(RESULTS)
    if path is not None:
        print((RESULTS / path.name).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
