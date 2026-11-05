"""The generated schema files: page types, areas, edges, and validation."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = PLUGIN_ROOT / "schema" / "system-design.schema.json"
SLOTS_PATH = PLUGIN_ROOT / "schema" / "system-design.slots.json"


@lru_cache(maxsize=1)
def slots() -> dict:
    return json.loads(SLOTS_PATH.read_text("utf-8"))


def types() -> dict:
    return slots()["types"]


def edges() -> dict:
    return slots()["edges"]


def areas() -> list:
    return slots()["areas"]


def anchors() -> dict:
    return slots()["anchors"]


def by_prefix() -> dict:
    return {spec["prefix"]: name for name, spec in types().items() if spec["prefix"]}


def plugin_version() -> str:
    return json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text("utf-8"))["version"]


def plugin_actor() -> str:
    return f"system-design/{plugin_version()}"


@lru_cache(maxsize=1)
def _defs() -> dict:
    return json.loads(SCHEMA_PATH.read_text("utf-8"))["$defs"]


@lru_cache(maxsize=None)
def _validator(type_name):
    from jsonschema import Draft7Validator

    return Draft7Validator({"$defs": _defs(), "$ref": f"#/$defs/{type_name}"})


def validate(type_name, frontmatter) -> list[str]:
    if type_name not in types():
        return [f"{type_name!r} is not a page type of system-design"]
    return sorted(f"{'.'.join(map(str, e.absolute_path)) or '(page)'}: {e.message}"
                  for e in _validator(type_name).iter_errors(frontmatter))


def edge_values(frontmatter, name) -> list[str]:
    frontmatter = frontmatter or {}
    if "." in name:
        parent, part = name.split(".", 1)
        items = frontmatter.get(parent) or []
        items = [items] if isinstance(items, dict) else items
        return [str(item[part]) for item in items if isinstance(item, dict) and item.get(part)]
    value = frontmatter.get(name)
    if value in (None, "", []):
        return []
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]
