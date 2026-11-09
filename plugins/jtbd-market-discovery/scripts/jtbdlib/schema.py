"""The generated schema files: page types, edges, and validation."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = PLUGIN_ROOT / "schema" / "jtbd.schema.json"
SLOTS_PATH = PLUGIN_ROOT / "schema" / "jtbd.slots.json"

# The page types that a link field of each page type must have (manifest `required_links`, table "Page types").
REQUIRED_LINKS = {
    "Job": ["run"], "JobStep": ["job", "run"], "Outcome": ["step", "run"], "Segment": ["job", "run"],
    "WtpValidation": ["segment", "run"], "Result": ["run"],
}

# The fields of a WtpValidation page that only a survey gives (STORY-193): with a survey, 1 page of the run holds 1.
WTP_SURVEY_FIELDS = ("sample_size", "cleaned_median", "cleaned_mean", "optimal_price_point", "acceptable_range")


@lru_cache(maxsize=1)
def slots() -> dict:
    return json.loads(SLOTS_PATH.read_text("utf-8"))


def types() -> dict:
    return slots()["types"]


def edges() -> dict:
    return slots()["edges"]


def by_prefix() -> dict:
    return {spec["prefix"]: name for name, spec in types().items()}


def plugin_version() -> str:
    return json.loads((PLUGIN_ROOT / ".claude-plugin" / "plugin.json").read_text("utf-8"))["version"]


def plugin_actor() -> str:
    return f"jtbd-market-discovery/{plugin_version()}"


@lru_cache(maxsize=1)
def _defs() -> dict:
    return json.loads(SCHEMA_PATH.read_text("utf-8"))["$defs"]


@lru_cache(maxsize=None)
def _validator(type_name):
    from jsonschema import Draft7Validator

    return Draft7Validator({"$defs": _defs(), "$ref": f"#/$defs/{type_name}"})


def validate(type_name, frontmatter) -> list[str]:
    if type_name not in types():
        return [f"{type_name!r} is not a page type of the jtbd graph"]
    return sorted(f"{'.'.join(map(str, e.absolute_path)) or '(page)'}: {e.message}"
                  for e in _validator(type_name).iter_errors(frontmatter))


@lru_cache(maxsize=None)
def _slot_validator(type_name, slot):
    from jsonschema import Draft7Validator

    prop = _defs()[type_name]["properties"].get(slot)
    return None if prop is None else Draft7Validator({"$defs": _defs(), **prop})


def slot_ok(type_name, slot, value) -> bool:
    """True when `slot` exists on the page type and `value` is valid for it."""
    validator = _slot_validator(type_name, slot)
    return validator is not None and not any(True for _ in validator.iter_errors(value))


def edge_values(frontmatter, name) -> list[str]:
    value = (frontmatter or {}).get(name)
    if value in (None, "", []):
        return []
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]
