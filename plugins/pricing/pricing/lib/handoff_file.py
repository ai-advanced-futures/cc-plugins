"""The input file and the output file of a Phase 1 skill script (STORY-325).

A skill writes its answers to an input file with the Write tool, and runs 1 script. The script calls the
library, checks the result against the Charter schema, and writes the output file. So no answer text goes
into a shell command, and a file that the script wrote passes its schema. Each file that a script reads or
writes is a `.json` file in the `.pricing` folder of the project, because the skill has the write grant
`Edit(/.pricing/**)` and no wider one.
"""
from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "agentic-pricing"
SCHEMA_VERSION = "1.0.0"
FOLDER = ".pricing"
# The handoff files that hold `engagement_id`, in the order of the Phase 1 workflow.
HANDOFF_FILES = ("cost-amplifier-readout.json", "agentic-pricing-diagnosis.json", "pattern-selection.json")


def inside(name, what) -> Path:
    """The path of a `.json` file in the `.pricing` folder of the current folder (the project)."""
    here = Path.cwd().resolve()
    folder = (here / FOLDER).resolve()
    if folder != here / FOLDER:  # .pricing is a link, also to a folder next to it (.claude)
        raise ValueError("the %s folder of the project must not be a link to another folder" % FOLDER)
    path = (here / str(name)).resolve()
    if not path.is_relative_to(folder) or path == folder:
        raise ValueError("%s must be in the %s folder of the project: %s" % (what, FOLDER, name))
    if path.suffix != ".json":
        raise ValueError("%s must be a .json file: %s" % (what, name))
    return path


def read_input(name, what="the input file") -> dict:
    """The JSON object of the file. Raises ValueError with a plain message."""
    path = inside(name, what)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as err:
        raise ValueError("cannot read %s %s: %s" % (what, name, err.strerror or err)) from None
    except RecursionError:
        raise ValueError("%s %s is nested too deep" % (what, name)) from None
    except ValueError as err:
        raise ValueError("%s %s is not JSON: %s" % (what, name, err)) from None
    if not isinstance(data, dict):
        raise ValueError("%s %s must hold a JSON object" % (what, name))
    return data


def text(data, key, default=None) -> str:
    value = data.get(key, default)
    if not isinstance(value, str):
        raise ValueError("%s must be text" % key)
    return value


def number(data, key, where="") -> float:
    """A finite number. A JSON file can hold `NaN`, `Infinity`, `1e999` and a 400-digit whole number."""
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s%s must be a number" % (where, key))
    try:
        value = float(value)
    except OverflowError:
        raise ValueError("%s%s is too large for a number" % (where, key)) from None
    if not math.isfinite(value):
        raise ValueError("%s%s must be a finite number" % (where, key))
    return value


def _engagement(data):
    """(the id, where it comes from). The input wins, then the first handoff file of `.pricing` that has one."""
    given = data.get("engagement_id")
    if given is not None:
        try:
            return str(uuid.UUID(given)) if isinstance(given, str) else None, "the input file"
        except ValueError:
            return None, "the input file"
    for name in HANDOFF_FILES:
        try:
            found = json.loads((Path.cwd() / FOLDER / name).read_text(encoding="utf-8")).get("engagement_id")
            return str(uuid.UUID(found)), name
        except (OSError, ValueError, AttributeError, TypeError, RecursionError):
            continue
    return str(uuid.uuid4()), "new"


def envelope(data) -> dict:
    """The 3 fields that each Charter handoff file starts with."""
    engagement, source = _engagement(data)
    if engagement is None:
        raise ValueError("engagement_id must be a UUID, or leave it out")
    produced = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    envelope.source = source  # `run` prints it
    return {"engagement_id": engagement, "produced_at": produced, "schema_version": SCHEMA_VERSION}


envelope.source = None


def check(result, schema_name) -> None:
    """Raises ValueError with the first schema fault of the result."""
    from jsonschema import Draft7Validator

    schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    faults = sorted(Draft7Validator(schema).iter_errors(result), key=lambda fault: list(fault.absolute_path))
    if faults:
        place = "/".join(str(part) for part in faults[0].absolute_path) or "the object"
        raise ValueError("the result does not pass %s: %s: %s" % (schema_name, place, faults[0].message[:200]))


def write(out, result) -> Path:
    """Write the output file. `allow_nan=False`: a value that is not finite never goes into a file."""
    path = inside(out, "the output file")
    try:
        body = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    except ValueError:
        raise ValueError("the result holds a number that is not finite") from None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    except OSError as err:
        raise ValueError("cannot write the output file %s: %s" % (out, err.strerror or err)) from None
    return path


def run(name, argv, build) -> int:
    """The command line of a script: `--input <file> --out <file>`. `build` gives (the result, the line to print)."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog=name)
    parser.add_argument("--input", required=True, help="the input file that the skill wrote, in .pricing")
    parser.add_argument("--out", required=True, help="the output file, in .pricing")
    args = parser.parse_args(argv)  # exits 2 on a usage error
    try:
        inside(args.out, "the output file")  # before the work, so a wrong path costs nothing
        result, line = build(read_input(args.input))
        path = write(args.out, result)
    except ValueError as err:
        print("%s: %s" % (name, " ".join(str(err).split())), file=sys.stderr)
        return 1
    except OverflowError:  # the product of numbers that are each finite, for example 8 multipliers of 1e40
        print("%s: the numbers of the input file are too large for the calculation" % name, file=sys.stderr)
        return 1
    print(line)
    if envelope.source:
        print("engagement_id=%s (%s)" % (result["engagement_id"], envelope.source))
    print("wrote %s" % path.relative_to(Path.cwd().resolve()))
    return 0
