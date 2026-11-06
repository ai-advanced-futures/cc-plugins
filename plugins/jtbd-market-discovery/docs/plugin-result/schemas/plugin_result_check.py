"""Check a plugin result file.

One file, standard library only, safe on Python 3.9 (hooks may run under the
macOS system python3). It holds two things:

1. A small JSON Schema checker for the keywords in SUPPORTED_KEYWORDS. Any other
   keyword raises UnsupportedSchema, so a schema never passes by accident.
2. The rules a schema cannot state. Each error message starts with its rule id:
   R-DEFAULT, R-IDS, R-KIND, R-VALUE, R-EMPTY, R-TIME (check_result), R-NAME
   (check_result_file), R-INPUTS and R-OPTIONS (check_questions).
3. The invocation block a coach puts in a plugin run's prompt (check_invocation).

Command line:
    python3 plugin_result_check.py result <path>
    python3 plugin_result_check.py questions <path>
    python3 plugin_result_check.py answers <path>
    python3 plugin_result_check.py invocation <path of a text file holding the block>
Exit 0 when the file is valid, 1 when it is not (errors on stderr), 2 on bad use.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCHEMA_DIR = Path(__file__).resolve().parent
RESULT_SCHEMA = "plugin-result.schema.json"
QUESTIONS_SCHEMA = "questions.schema.json"
ANSWERS_SCHEMA = "answers.schema.json"
KINDS_FILE = "kinds.json"
INVOCATION_KEYS = ("command", "automated", "answers_path", "case", "run_id", "inputs_from")
INPUT_KEYS = ("plugin", "run_id", "result_file")

SUPPORTED_KEYWORDS = frozenset(
    {
        "$schema",
        "$id",
        "$defs",
        "$ref",
        "title",
        "description",
        "type",
        "const",
        "enum",
        "properties",
        "required",
        "additionalProperties",
        "patternProperties",
        "items",
        "minItems",
        "minLength",
        "maxLength",
        "pattern",
        "minimum",
        "anyOf",
    }
)

_TYPE_NAMES = frozenset({"string", "integer", "number", "boolean", "object", "array", "null"})
_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
_NAME_TIME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})")
_SLUG_LIMIT = 40
_COMMAND = re.compile(r"[a-z0-9-]+(:[a-z0-9-]+)+\Z")
_RUN_ID = re.compile(r"[a-z0-9][a-z0-9-]{2,62}[a-z0-9]\Z")
_PLUGIN = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
_INVOCATION_FENCE = re.compile(r"^```plugin-run[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)


class UnsupportedSchema(Exception):
    """The schema uses a keyword or a form this checker does not implement."""


# ---------------------------------------------------------------- schema checker


def _check_pattern(pattern: str, where: str) -> None:
    """_search reads only a final `$` as end of string. Refuse every other `$` that is
    not escaped, and a final `$` after an escaped backslash, which _search would read
    as a literal `$`."""
    i, last = 0, len(pattern) - 1
    while i <= last:
        if pattern[i] == "\\":
            i += 2
            continue
        if pattern[i] == "$" and (i != last or pattern[i - 1 : i] == "\\"):
            raise UnsupportedSchema(
                "%s: pattern %r uses `$` other than as its last character" % (where, pattern)
            )
        i += 1


def _check_schema(node: Any, where: str) -> None:
    if not isinstance(node, dict):
        raise UnsupportedSchema("%s: a schema must be an object" % where)
    for key, value in node.items():
        if key not in SUPPORTED_KEYWORDS:
            raise UnsupportedSchema("%s: keyword %r is not supported" % (where, key))
        if key == "type":
            names = value if isinstance(value, list) else [value]
            if not names or not all(isinstance(n, str) and n in _TYPE_NAMES for n in names):
                raise UnsupportedSchema("%s: bad type %r" % (where, value))
        elif key == "additionalProperties":
            if value is not False:
                raise UnsupportedSchema("%s: additionalProperties must be false" % where)
        elif key in ("required",):
            if not isinstance(value, list) or not all(isinstance(k, str) for k in value):
                raise UnsupportedSchema("%s: required must be a list of strings" % where)
        elif key == "enum":
            if not isinstance(value, list):
                raise UnsupportedSchema("%s: enum must be a list" % where)
        elif key in ("minLength", "maxLength", "minItems"):
            if not isinstance(value, int) or isinstance(value, bool):
                raise UnsupportedSchema("%s: %s must be an integer" % (where, key))
        elif key == "minimum":
            if not _is_number(value):
                raise UnsupportedSchema("%s: minimum must be a number" % where)
        elif key == "pattern":
            if not isinstance(value, str):
                raise UnsupportedSchema("%s: pattern must be a string" % where)
            _check_pattern(value, where)
        elif key == "$ref":
            if not isinstance(value, str) or not value.startswith("#"):
                raise UnsupportedSchema("%s: only local $ref is supported" % where)
        elif key in ("properties", "patternProperties", "$defs"):
            if not isinstance(value, dict):
                raise UnsupportedSchema("%s: %s must be an object" % (where, key))
            for name, sub in value.items():
                if key == "patternProperties":
                    _check_pattern(name, "%s/%s" % (where, key))
                _check_schema(sub, "%s/%s/%s" % (where, key, name))
        elif key == "items":
            _check_schema(value, "%s/items" % where)
        elif key == "anyOf":
            if not isinstance(value, list) or not value:
                raise UnsupportedSchema("%s: anyOf must be a non-empty list" % where)
            for i, sub in enumerate(value):
                _check_schema(sub, "%s/anyOf/%d" % (where, i))


def _search(pattern: str, text: str) -> bool:
    """re.search with `$` meaning end of string, as in ECMA 262. Python's `$` also matches
    before a final newline, which would let "abcd\\n" into a run_id and a file name."""
    if pattern.endswith("$") and not pattern.endswith("\\$"):
        pattern = pattern[:-1] + r"\Z"
    return re.search(pattern, text) is not None


def _join(ptr: str, key: Any) -> str:
    return "%s/%s" % (ptr, str(key).replace("~", "~0").replace("/", "~1"))


def _resolve(root: dict, ref: str) -> dict:
    node: Any = root
    if ref == "#":
        return node
    if not ref.startswith("#/"):
        raise UnsupportedSchema("bad $ref %r" % ref)
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise UnsupportedSchema("$ref %r does not resolve" % ref)
        node = node[part]
    if not isinstance(node, dict):
        raise UnsupportedSchema("$ref %r does not point at a schema" % ref)
    return node


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _type_ok(value: Any, name: str) -> bool:
    if name == "string":
        return isinstance(value, str)
    if name == "boolean":
        return isinstance(value, bool)
    if name == "null":
        return value is None
    if name == "object":
        return isinstance(value, dict)
    if name == "array":
        return isinstance(value, list)
    if name == "number":
        return _is_number(value)
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool) or (
            isinstance(value, float) and value.is_integer()
        )
    return False


def _json_eq(a: Any, b: Any) -> bool:
    """JSON equality: True is not 1, and 1 equals 1.0."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if _is_number(a) and _is_number(b):
        return a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_json_eq(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_json_eq(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def _walk(inst: Any, node: dict, root: dict, ptr: str, errs: List[Tuple[str, str]]) -> None:
    if "$ref" in node:
        _walk(inst, _resolve(root, node["$ref"]), root, ptr, errs)
    if "type" in node:
        names = node["type"] if isinstance(node["type"], list) else [node["type"]]
        if not any(_type_ok(inst, n) for n in names):
            errs.append((ptr, "expected type %s" % "|".join(names)))
    if "const" in node and not _json_eq(inst, node["const"]):
        errs.append((ptr, "must equal %s" % json.dumps(node["const"])))
    if "enum" in node and not any(_json_eq(inst, v) for v in node["enum"]):
        errs.append((ptr, "must be one of %s" % json.dumps(node["enum"])))
    if isinstance(inst, str):
        if "minLength" in node and len(inst) < node["minLength"]:
            errs.append((ptr, "shorter than %d characters" % node["minLength"]))
        if "maxLength" in node and len(inst) > node["maxLength"]:
            errs.append((ptr, "longer than %d characters" % node["maxLength"]))
        if "pattern" in node and not _search(node["pattern"], inst):
            errs.append((ptr, "does not match %s" % node["pattern"]))
    if _is_number(inst) and "minimum" in node and inst < node["minimum"]:
        errs.append((ptr, "below the minimum %s" % node["minimum"]))
    if isinstance(inst, dict):
        for key in node.get("required", []):
            if key not in inst:
                errs.append((ptr, "missing required key %r" % key))
        props = node.get("properties", {})
        patterns = node.get("patternProperties", {})
        for key, value in inst.items():
            matched = False
            if key in props:
                matched = True
                _walk(value, props[key], root, _join(ptr, key), errs)
            for pattern, sub in patterns.items():
                if _search(pattern, key):
                    matched = True
                    _walk(value, sub, root, _join(ptr, key), errs)
            if not matched and node.get("additionalProperties", True) is False:
                errs.append((_join(ptr, key), "key is not allowed here"))
    if isinstance(inst, list):
        if "minItems" in node and len(inst) < node["minItems"]:
            errs.append((ptr, "fewer than %d items" % node["minItems"]))
        if "items" in node:
            for i, item in enumerate(inst):
                _walk(item, node["items"], root, _join(ptr, i), errs)
    if "anyOf" in node:
        for branch in node["anyOf"]:
            trial: List[Tuple[str, str]] = []
            _walk(inst, branch, root, ptr, trial)
            if not trial:
                break
        else:
            errs.append((ptr, "matches none of the anyOf branches"))


def _pairs(instance: Any, schema: dict) -> List[Tuple[str, str]]:
    _check_schema(schema, "")
    errs: List[Tuple[str, str]] = []
    _walk(instance, schema, schema, "", errs)
    return errs


def validate(instance: Any, schema: dict) -> List[str]:
    """Return errors as "<json pointer>: <message>". Raise UnsupportedSchema on any
    keyword outside SUPPORTED_KEYWORDS."""
    return ["%s: %s" % (ptr or "/", msg) for ptr, msg in _pairs(instance, schema)]


# ---------------------------------------------------------------- file names


def subject_slug(subject: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")
    slug = slug[:_SLUG_LIMIT].strip("-")
    return slug or "subject"


def command_part(command: str) -> str:
    """`gtm:marketing:launch` gives `marketing-launch`: drop the plugin, join the rest."""
    parts = command.split(":")
    return "-".join(parts[1:]) if len(parts) > 1 else command


def result_file_name(
    finished_at: str,
    command: str,
    subject: str,
    run_id: Optional[str],
    taken: Iterable[str] = (),
) -> str:
    match = _NAME_TIME.match(finished_at)
    if not match:
        raise ValueError("finished_at is not an ISO time: %r" % finished_at)
    stamp = "%s%s%sT%s%s%sZ" % match.groups()
    base = "%s-%s-%s" % (stamp, command_part(command), subject_slug(subject))
    if run_id:
        base = "%s-%s" % (base, run_id)
    taken_names = set(taken)
    name = base + ".json"
    if run_id and name in taken_names:
        raise ValueError("a result file with this run_id already exists: %s" % name)
    n = 2
    while name in taken_names:
        name = "%s-%d.json" % (base, n)
        n += 1
    return name


# ---------------------------------------------------------------- rules


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_kinds() -> Dict[str, dict]:
    return _load_json(SCHEMA_DIR / KINDS_FILE)["kinds"]


def _parse_time(text: str) -> datetime:
    base, _, fraction = text.rstrip("Z").partition(".")
    moment = datetime.strptime(base, _TIME_FORMAT)
    if fraction:
        moment += timedelta(microseconds=int(fraction[:6].ljust(6, "0")))
    return moment


def _rule_default(doc: dict) -> List[str]:
    errors = []
    for i, result in enumerate(doc["results"]):
        has_default = any(s["type"] == "default" for s in result["sources"]) or bool(
            result["defaults"]
        )
        if result["rests_on_default"] != has_default:
            errors.append(
                "R-DEFAULT: /results/%d: rests_on_default is %s, but a source of type default "
                "or a non-empty defaults list says %s"
                % (i, str(result["rests_on_default"]).lower(), str(has_default).lower())
            )
    return errors


def _rule_ids(doc: dict) -> List[str]:
    seen = set()
    errors = []
    for i, result in enumerate(doc["results"]):
        if result["id"] in seen:
            errors.append("R-IDS: /results/%d: id %r is used twice" % (i, result["id"]))
        seen.add(result["id"])
    return errors


def _rule_kind(doc: dict, kinds: Dict[str, dict]) -> List[str]:
    errors = []
    for section in ("results", "gaps"):
        for i, entry in enumerate(doc[section]):
            if entry["kind"] not in kinds:
                errors.append(
                    "R-KIND: /%s/%d: kind %r is not in kinds.json" % (section, i, entry["kind"])
                )
    return errors


def _rule_value(doc: dict, kinds: Dict[str, dict]) -> List[str]:
    errors = []
    for i, result in enumerate(doc["results"]):
        kind = kinds.get(result["kind"])
        if kind is None:
            continue
        for ptr, msg in _pairs(result["value"], kind["value"]):
            errors.append(
                "R-VALUE: /results/%d/value%s: %s (kind %s)" % (i, ptr, msg, result["kind"])
            )
        for field in ("unit", "period"):
            rule = kind[field]
            present = field in result
            if rule == "required" and not present:
                errors.append(
                    "R-VALUE: /results/%d: kind %s needs %s" % (i, result["kind"], field)
                )
            if rule == "none" and present:
                errors.append(
                    "R-VALUE: /results/%d: kind %s takes no %s" % (i, result["kind"], field)
                )
    return errors


def _rule_empty(doc: dict) -> List[str]:
    if not doc["results"] and not doc["gaps"]:
        return ["R-EMPTY: /results: a run with no results must list at least one gap"]
    return []


def _rule_time(doc: dict) -> List[str]:
    run = doc["run"]
    try:
        started = _parse_time(run["started_at"])
        finished = _parse_time(run["finished_at"])
    except ValueError as exc:
        return ["R-TIME: /run: not a real time (%s)" % exc]
    if finished < started:
        return ["R-TIME: /run/finished_at: is before started_at"]
    return []


def check_result(doc: Any) -> List[str]:
    """Schema errors first. When the shape is right, the rules the schema cannot state."""
    if not isinstance(doc, dict):
        return ["/: a result file is a JSON object"]
    errors = validate(doc, _load_json(SCHEMA_DIR / RESULT_SCHEMA))
    if errors:
        return errors
    kinds = load_kinds()
    return (
        _rule_default(doc)
        + _rule_ids(doc)
        + _rule_kind(doc, kinds)
        + _rule_value(doc, kinds)
        + _rule_empty(doc)
        + _rule_time(doc)
    )


def check_result_file(path: Path) -> List[str]:
    """R-NAME: the file name is the one result_file_name gives for the file's own
    fields. With no run_id, a `-<n>` suffix (n >= 2) is allowed before `.json`."""
    path = Path(path)
    try:
        doc = _load_json(path)
    except (OSError, ValueError) as exc:
        return ["file: cannot read %s as JSON (%s)" % (path.name, exc)]
    try:
        run = doc["run"]
        run_id = run.get("run_id")
        expected = result_file_name(run["finished_at"], doc["command"], run["subject"], run_id)
    except (KeyError, TypeError, AttributeError, ValueError):
        return []  # a malformed file is reported by check_result
    if path.name == expected:
        return []
    if not run_id:
        stem = expected[: -len(".json")]
        match = re.fullmatch(re.escape(stem) + r"-([2-9]|[1-9][0-9]+)\.json", path.name)
        if match:
            return []
    return ["R-NAME: file name is %s, expected %s" % (path.name, expected)]


# ---------------------------------------------------------------- questions, answers


def check_questions(doc: Any) -> List[str]:
    """Schema errors first. When the shape is right, R-INPUTS and R-OPTIONS."""
    if not isinstance(doc, dict):
        return ["/: a questions list is a JSON object"]
    errors = validate(doc, _load_json(SCHEMA_DIR / QUESTIONS_SCHEMA))
    if errors:
        return errors
    seen = set()
    for i, question in enumerate(doc["questions"]):
        if question["input"] in seen:
            errors.append(
                "R-INPUTS: /questions/%d: input %r is named twice" % (i, question["input"])
            )
        seen.add(question["input"])
        if question["type"] == "choice" and "options" not in question:
            errors.append("R-OPTIONS: /questions/%d: a choice question lists its options" % i)
    return errors


def check_answers(doc: Any) -> List[str]:
    if not isinstance(doc, dict):
        return ["/: an answers file is a JSON object"]
    return validate(doc, _load_json(SCHEMA_DIR / ANSWERS_SCHEMA))


# ---------------------------------------------------------------- invocation block


def parse_invocation_block(text: str) -> Optional[dict]:
    """The JSON object of the first ```plugin-run fence, or None when there is none.
    A fence whose body is not JSON raises ValueError."""
    match = _INVOCATION_FENCE.search(text)
    if not match:
        return None
    return json.loads(match.group(1))


def _text_ok(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def _matches(pattern: "re.Pattern[str]", value: Any) -> bool:
    return isinstance(value, str) and pattern.match(value) is not None


def check_invocation(block: Any, commands: Optional[Iterable[str]] = None) -> List[str]:
    """The six keys and nothing else; automated is true; the command, run_id and each
    inputs_from entry have their fixed shape. When `commands` is given, the command
    must be one of them (the standard's adopting commands)."""
    if not isinstance(block, dict):
        return ["invocation: /: the block is one JSON object"]
    errors = ["invocation: /: missing key %r" % k for k in INVOCATION_KEYS if k not in block]
    errors += ["invocation: /%s: key is not allowed" % k for k in block if k not in INVOCATION_KEYS]
    if "command" in block and not _matches(_COMMAND, block["command"]):
        errors.append("invocation: /command: not a canonical plugin:command name")
    elif "command" in block and commands is not None and block["command"] not in set(commands):
        errors.append("invocation: /command: %r is not an adopting command" % block["command"])
    if "automated" in block and block["automated"] is not True:
        errors.append("invocation: /automated: must be true")
    for key in ("answers_path", "case"):
        if key in block and not _text_ok(block[key]):
            errors.append("invocation: /%s: must be a non-empty string" % key)
    if "run_id" in block and not _matches(_RUN_ID, block["run_id"]):
        errors.append("invocation: /run_id: does not match the run_id pattern")
    entries = block.get("inputs_from", [])
    if not isinstance(entries, list):
        return errors + ["invocation: /inputs_from: must be a list"]
    for i, entry in enumerate(entries):
        where = "invocation: /inputs_from/%d" % i
        if not isinstance(entry, dict):
            errors.append("%s: must be an object" % where)
            continue
        errors += ["%s: missing key %r" % (where, k) for k in INPUT_KEYS if k not in entry]
        errors += ["%s/%s: key is not allowed" % (where, k) for k in entry if k not in INPUT_KEYS]
        if "plugin" in entry and not _matches(_PLUGIN, entry["plugin"]):
            errors.append("%s/plugin: not a plugin name" % where)
        if "run_id" in entry and not _matches(_RUN_ID, entry["run_id"]):
            errors.append("%s/run_id: does not match the run_id pattern" % where)
        if "result_file" in entry and not _text_ok(entry["result_file"]):
            errors.append("%s/result_file: must be a non-empty string" % where)
    return errors


# ---------------------------------------------------------------- command line

_USAGE = "usage: plugin_result_check.py result|questions|answers|invocation <path>\n"


def main(argv: List[str]) -> int:
    if len(argv) != 3 or argv[1] not in ("result", "questions", "answers", "invocation"):
        sys.stderr.write(_USAGE)
        return 2
    kind, path = argv[1], Path(argv[2])
    try:
        if kind == "invocation":
            block = parse_invocation_block(path.read_text(encoding="utf-8"))
        else:
            doc = _load_json(path)
    except (OSError, ValueError) as exc:
        sys.stderr.write("file: cannot read %s (%s)\n" % (path, exc))
        return 1
    if kind == "invocation":
        if block is None:
            errors = ["invocation: %s holds no ```plugin-run block" % path]
        else:
            errors = check_invocation(block)
    elif kind == "questions":
        errors = check_questions(doc)
    elif kind == "answers":
        errors = check_answers(doc)
    else:
        errors = check_result(doc) + check_result_file(path)
    for error in errors:
        sys.stderr.write(error + "\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
