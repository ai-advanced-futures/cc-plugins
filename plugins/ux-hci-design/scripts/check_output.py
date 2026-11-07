#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["jsonschema>=4.17.0"]
# ///
"""Check one output file of the plugin against one schema of schemas/outputs/.

usage: check_output.py FILE --schema NAME
  NAME is a file name in schemas/outputs/, for example evaluation-report-schema.json
exit 0: no error
exit 1: schema errors (the last line is "<n> schema errors in <FILE>")
exit 2: the file or the schema cannot be read, or another error
output: 1 line "<path>: <message>" for each error, then "<n> schema errors in <FILE>"
"""
import argparse
import json
import sys
from pathlib import Path

SCHEMAS = Path(__file__).resolve().parent.parent / "schemas" / "outputs"
MESSAGE_LIMIT = 200


def error_lines(document, schema):
    """Return one line for each schema error, sorted by path."""
    from jsonschema import Draft7Validator

    lines = []
    for error in Draft7Validator(schema).iter_errors(document):
        path = "/".join(str(part) for part in error.absolute_path) or "(root)"
        lines.append((path, f"{path}: {error.message[:MESSAGE_LIMIT]}"))
    return [line for _, line in sorted(lines)]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check an output file against a schema of schemas/outputs/.")
    parser.add_argument("file", help="the JSON file to check")
    parser.add_argument("--schema", required=True, help="a file name in schemas/outputs/")
    args = parser.parse_args(argv)
    if "/" in args.schema or "\\" in args.schema or not (SCHEMAS / args.schema).is_file():
        print(f"check_output.py: {args.schema} is not a schema file in schemas/outputs/")
        return 2
    try:
        lines = error_lines(load_json(args.file), load_json(SCHEMAS / args.schema))
    except Exception as exc:  # any failure is exit 2, so the caller never reads it as "no error"
        print(f"check_output.py: {exc}"[:MESSAGE_LIMIT + 20])
        return 2
    for line in lines:
        print(line)
    print(f"{len(lines)} schema errors in {args.file}")
    return 1 if lines else 0


if __name__ == "__main__":
    sys.exit(main())
