"""Frontmatter validation against the generated JSON Schema.

This is the one place the script reads a path from its own file location: the
schema ships inside the plugin. The bundle root always comes from --root.
"""
import json
from functools import lru_cache
from pathlib import Path

from . import UsageError

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema" / "product.schema.json"
# gen-schema.sh pins the generator, and the committed schema is a Draft 2019-09
# document, so the class map is always under `$defs`.
DEFS_KEY = "$defs"


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
        return [f"the type '{type_name}' is not in {SCHEMA_PATH.name}"]
    errors = sorted(_validator(type_name).iter_errors(frontmatter),
                    key=lambda e: list(e.absolute_path))
    return [f"{'/'.join(str(p) for p in e.absolute_path) or type_name}: {e.message}"
            for e in errors]
