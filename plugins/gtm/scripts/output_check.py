# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.17.0"]
# ///
"""Check the JSON outputs of one integrity pass against their schemas.

Run it by its path. It puts its own plugin folder on sys.path, never the cwd:
    uv run "${CLAUDE_PLUGIN_ROOT}/scripts/output_check.py" --root <project> --agent brand|marketing|sales|funnel
    uv run "${CLAUDE_PLUGIN_ROOT}/scripts/output_check.py" --root <project> --context

`--agent` checks the files of gtm-output/ that the pass of that agent wrote (the funnel pass
also checks consolidated-audit.json). `--context` checks gtm-context.json. The schema of
each file is the file of the same name in the schemas/ folder of this plugin.

It prints one line for each schema error: `<file>: <path>: <message>`. The path is `(root)`
for the top of the file. The last line is `<n> schema errors in <k> files`, where <k> is
the count of files that it checked.

Exit 0: no schema error. Exit 1: 1 or more schema errors, with that last line.
Exit 2: any other failure (a file that is absent, cannot be read or is not JSON, an
exception, a bad argument). It prints 1 line `output_check.py: <the error>` for each
failure, after the error lines of the files that it could check, and no last line.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):  # run by path: uv run "<plugin root>/scripts/<file>.py"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # its own package, never the cwd

from jsonschema.validators import validator_for  # noqa: E402

from scripts._jsonschema_formats import FORMAT_CHECKER, SCHEMAS_DIR  # noqa: E402
from scripts.gtm_constants import INTEGRITY_AGENTS  # noqa: E402
from scripts.integrity_manifest import CONTEXT_FILE, OUTPUT_SCHEMAS, get_checked_outputs  # noqa: E402

_MESSAGE_LIMIT = 200


def _errors(root: Path, rel: str) -> list[str]:
    """The error lines of 1 file. Raise OSError or ValueError when the file or its schema cannot be read."""
    schema = json.loads((SCHEMAS_DIR / OUTPUT_SCHEMAS[rel]).read_text(encoding="utf-8"))
    data: Any = json.loads((root / rel).read_text(encoding="utf-8"))
    validator = validator_for(schema)(schema, format_checker=FORMAT_CHECKER)
    found = sorted(validator.iter_errors(data), key=lambda e: ([str(p) for p in e.absolute_path], e.message))
    return [
        f"{rel}: {'.'.join(str(p) for p in e.absolute_path) or '(root)'}: "
        f"{' '.join(e.message.split())[:_MESSAGE_LIMIT]}"
        for e in found
    ]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="output_check.py", description="Check the JSON outputs of one integrity pass against their schemas."
    )
    parser.add_argument("--root", required=True, help="the project root")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--agent", choices=INTEGRITY_AGENTS, help="check the files of the pass of this agent")
    group.add_argument("--context", action="store_true", help="check gtm-context.json")
    args = parser.parse_args(argv)
    files = [CONTEXT_FILE] if args.context else get_checked_outputs(args.agent)

    lines: list[str] = []
    failures: list[str] = []
    checked = 0
    try:
        for rel in files:
            try:
                lines.extend(_errors(Path(args.root), rel))
                checked += 1
            except (OSError, ValueError) as error:
                failures.append(f"output_check.py: {rel}: {error}")
    except Exception as error:  # noqa: BLE001 - no failure may give exit 0 or exit 1
        failures.append(f"output_check.py: {error}")
    for line in lines + failures:
        print(line)
    if failures:
        return 2
    print(f"{len(lines)} schema errors in {checked} files")
    return 1 if lines else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
