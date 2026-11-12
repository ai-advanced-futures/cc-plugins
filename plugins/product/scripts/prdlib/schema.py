"""Frontmatter validation against the generated JSON Schema.

This is the one place the script reads a path from its own file location: the
schema ships inside the plugin. The bundle root always comes from --root.
"""
import json
from functools import lru_cache
from pathlib import Path

from . import UsageError
from .graph import MAPPING_FIELDS
from .linkstsv import links_in
from .textsafe import escape_controls, first_bad_character

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema" / "product.schema.json"
# gen-schema.sh pins the generator, and the committed schema is a Draft 2019-09
# document, so the class map is always under `$defs`.
DEFS_KEY = "$defs"
# What `regen` copies from a page into a generated file (issues 1915, 1928).
# Each of these prints on one line, so a line break or another control
# character there forges a line, or moves a terminal cursor:
# - title and description: the index, a STATUS row, a LINKS line;
# - owner, state and blocked_by: a STATUS row;
# - the priority of an `includes` or `traces` entry: a LINKS suffix;
# - `generated.by` and `generated.at`: closed.md;
# - every link of every field, and the name of the field: links.tsv;
# - aliases: not printed today. They are in the rule since issue 1915.
# - the file name and the folders of the page: `path_problems` below.
# The body is not here: it keeps its line breaks.
# A field that `regen` starts to copy into a generated file MUST join this
# list (or the checks of `single_line_problems`) in the same change. Else a
# hand-edited value reaches the generated file raw. Tests: the sweep in
# tests/test_single_line.py, one row for each copied value.
SINGLE_LINE_FIELDS = ("title", "description", "aliases", "owner", "state",
                      "blocked_by")


@lru_cache(maxsize=1)
def _document() -> dict:
    try:
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except OSError as error:
        raise UsageError(f"cannot read {SCHEMA_PATH}: {error}")


def plugin_actor() -> str:
    """The default `generated.by` and `actor` value: this plugin and its own
    shipped version, read from its own plugin.json."""
    data = json.loads(
        (Path(__file__).resolve().parents[2] / ".claude-plugin" / "plugin.json")
        .read_text(encoding="utf-8"))
    return f"prd/{data['version']}"


def is_single_valued(type_name: str, field: str) -> bool:
    """Whether the schema declares the slot as one value and not a list.

    A field the schema does not declare is not single-valued: `new` keeps
    writing it as a list, and rule E2 reports the unknown key.
    """
    definition = _document().get(DEFS_KEY, {}).get(type_name, {})
    declared = definition.get("properties", {}).get(field)
    if declared is None:
        return False
    types = declared.get("type")
    return "array" not in (types if isinstance(types, list) else [types])


def _jsonschema():
    """The import is here, not at the top: it costs about half of the startup
    time of the script and only this function uses it. Three subcommands of
    sixteen reach it, so the other thirteen no longer pay for it."""
    try:
        import jsonschema
    except ImportError:
        raise UsageError(
            "the jsonschema package is missing. Run this script with "
            "`uv run`, or install it: pip install jsonschema")
    return jsonschema


@lru_cache(maxsize=None)
def _validator(type_name: str):
    """One validator for each page type, built one time.

    `check` validates every page of the bundle, and there are 23 types. A
    validator built per page compiles the whole `$defs` document again for
    each file, which is most of the cost of rule E2.
    """
    definitions = _document().get(DEFS_KEY, {})
    wrapper = {DEFS_KEY: definitions, "$ref": f"#/{DEFS_KEY}/{type_name}"}
    return _jsonschema().Draft7Validator(wrapper)


def validate_frontmatter(type_name: str, frontmatter: dict) -> list[str]:
    """One message for each violation. An empty list means the page is valid."""
    if type_name not in _document().get(DEFS_KEY, {}):
        return [f"the type '{escape_controls(type_name)}' is not in {SCHEMA_PATH.name}"]
    errors = sorted(_validator(type_name).iter_errors(frontmatter),
                    key=lambda e: list(e.absolute_path))
    # The key path holds frontmatter keys, so it is escaped. `e.message` is
    # not: jsonschema writes each value with `repr`, and `repr` writes a
    # control character as `\xNN` or `\n` already.
    problems = [f"{_path_of(e) or escape_controls(type_name)}: {e.message}"
                for e in errors]
    return problems + single_line_problems(frontmatter)


def path_problems(relative_path) -> list[str]:
    """One message when the path of a page, relative to the root, holds a
    line break or another control character. The file name and the folders
    go into each index, each STATUS row, each LINKS block and links.tsv, and
    no frontmatter rule sees them. `check` (E2) and `regen` both call this
    function."""
    bad = first_bad_character(str(relative_path))
    if bad is None:
        return []
    return [f"the file name: must be one line, it holds the character {bad}"]


def single_line_problems(frontmatter: dict) -> list[str]:
    """One message for each value that `regen` copies into a generated file
    and that holds a line break or another control character (SINGLE_LINE_FIELDS
    above). A value that is not text is the schema's.
    This is the one place of the rule: `check` (E2), `new`, `set` and `link`
    all call `validate_frontmatter`, so no page with such a value is written,
    and a page that holds one fails the gate. `regen` calls this function too,
    so a page that someone edited by hand cannot reach a generated file."""
    problems = []

    def report(where, value):
        bad = first_bad_character(value) if isinstance(value, str) else None
        if bad:
            problems.append(f"{where}: must be one line, it holds the "
                            f"character {bad}")

    for field in SINGLE_LINE_FIELDS:
        value = frontmatter.get(field)
        if isinstance(value, list):
            for index, item in enumerate(value):
                report(f"{field}/{index}", item)
        else:
            report(field, value)
    stamp = frontmatter.get("generated")
    if isinstance(stamp, dict):
        for key in ("by", "at"):
            report(f"generated/{key}", stamp.get(key))
    for field in MAPPING_FIELDS:
        entries = frontmatter.get(field)
        for entry in entries if isinstance(entries, list) else [entries]:
            if isinstance(entry, dict):
                report(f"{field}/priority", entry.get("priority"))
    for key, value in frontmatter.items():
        if not isinstance(key, str) or key in ("generated", "verified"):
            continue
        shown = escape_controls(key)
        report(f"{shown} (name of a field)", key)
        for link in links_in(value):
            report(f"{shown} (link)", link)
    return problems


def _path_of(error) -> str:
    return escape_controls("/".join(str(p) for p in error.absolute_path))
