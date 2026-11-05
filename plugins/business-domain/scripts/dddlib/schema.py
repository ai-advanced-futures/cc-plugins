"""The two generated schema files and the plugin version.

This is the one place that reads a path from the script's own location: the
schema ships inside the plugin. The repository root always comes from --root.
"""
import json
from functools import lru_cache
from pathlib import Path

from . import UsageError

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PLUGIN_ROOT / "schema" / "domain.schema.json"
SLOTS_PATH = PLUGIN_ROOT / "schema" / "domain.slots.json"
MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
DEFS_KEY = "$defs"


def _read(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise UsageError(f"cannot read {path}: {error}")


@lru_cache(maxsize=1)
def slots() -> dict:
    return _read(SLOTS_PATH)


@lru_cache(maxsize=1)
def document() -> dict:
    return _read(SCHEMA_PATH)


def types() -> dict:
    """Page type -> {prefix, directory, key_order}, in schema order."""
    return slots()["types"]


def edges() -> dict:
    """Edge field -> {targets, kinds, multivalued, acyclic, distinct,
    inverse_label}, in schema order."""
    return slots()["edges"]


def type_of_prefix(prefix: str):
    return next((name for name, spec in types().items()
                 if spec["prefix"] == prefix), None)


@lru_cache(maxsize=1)
def plugin_version() -> str:
    return _read(MANIFEST)["version"]


def plugin_actor() -> str:
    """The OKF actor of the plugin, as in ddd/0.1.0."""
    return f"ddd/{plugin_version()}"


def _jsonschema():
    """Imported here and not at the top: only rule E2 and `new` need it."""
    try:
        import jsonschema
    except ImportError:
        raise UsageError(
            "the jsonschema package is missing. Run this script with "
            "`uv run`, or install it: pip install jsonschema")
    return jsonschema


@lru_cache(maxsize=None)
def _validator(type_name: str):
    """One validator for each page type, built one time."""
    wrapper = {DEFS_KEY: document()[DEFS_KEY],
               "$ref": f"#/{DEFS_KEY}/{type_name}"}
    return _jsonschema().Draft7Validator(wrapper)


def validate_frontmatter(type_name: str, frontmatter: dict) -> list:
    """One (field, message) pair for each violation. Empty means valid."""
    if type_name not in types():
        return [("type", f"the type '{type_name}' is not a page type of "
                         f"domain.yaml")]
    errors = sorted(_validator(type_name).iter_errors(frontmatter),
                    key=lambda e: [str(p) for p in e.absolute_path])
    out = []
    for error in errors:
        where = [str(p) for p in error.absolute_path]
        out.append((where[0] if where else "type",
                    f"{'/'.join(where) or type_name}: {error.message}"))
    return out
