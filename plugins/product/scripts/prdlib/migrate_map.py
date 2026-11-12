"""The type of each v3 ID.

The script never guesses a type. A prefix of the v3 lens catalog has a fixed
type. Every other prefix is unknown until the user gives a migration map,
because a wrong type is a silent defect.
"""
import yaml

from . import UsageError
from .page import safe_load
from .registry import PRD_TYPES
from .textsafe import escape_controls

KEYS = ("prefixes", "ids")

FIXED_PREFIXES = {
    "PRB": "Problem", "PER": "Persona", "JRN": "Journey",
    "CAP": "Capability", "SCP": "Scope", "MET": "Metric",
    "BIZ": "Business", "GTM": "GTM", "RSK": "Risk", "CON": "Constraint",
}


def type_of(block, mapping: dict | None = None) -> str | None:
    """The type of one block, or None when no rule gives one."""
    mapping = mapping or {}
    ids = mapping.get("ids") or {}
    if block.id in ids:
        return ids[block.id]
    prefixes = mapping.get("prefixes") or {}
    if block.prefix in prefixes:
        return prefixes[block.prefix]
    return FIXED_PREFIXES.get(block.prefix)


def load_map(path) -> dict:
    """Read the migration map. Each value is a page type of the registry."""
    try:
        data = safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        # PyYAML text holds line breaks and a snippet of the map. One line
        # of it must not read as a second finding.
        raise UsageError(
            f"the migration map does not load: {escape_controls(error)}")
    if not isinstance(data, dict):
        raise UsageError("the migration map is a mapping with `prefixes` "
                         "and `ids` keys")
    out = {}
    for key in KEYS:
        section = data.get(key) or {}
        if not isinstance(section, dict):
            raise UsageError(f"`{key}` in the migration map is a mapping")
        for type_name in section.values():
            # PRD_TYPES, not TYPES: the map types a requirement block, which
            # always lands in the PRD bundle. TYPES also holds each roadmap
            # type and Product. Product has no prefix and no directory, so a
            # block with that type has no page to go in.
            if type_name not in PRD_TYPES:
                raise UsageError(
                    f"{escape_controls(type_name)} is not a PRD page type. "
                    f"The map gives one of: {', '.join(sorted(PRD_TYPES))}.")
        out[key] = dict(section)
    return out


def types_for(blocks, mapping: dict | None) -> dict:
    """block ID -> type. Every block has a type, or this raises.

    The script never guesses. A PRD with 60 IDs that have no lens prefix
    needs 60 decisions, and the skill takes them with the user.
    """
    out, missing = {}, []
    for block in blocks:
        type_name = type_of(block, mapping)
        if type_name is None:
            missing.append(block.id)
        else:
            out[block.id] = type_name
    if missing:
        raise UsageError(
            "these IDs have no type. Give a migration map with --map: "
            + ", ".join(missing))
    return out
