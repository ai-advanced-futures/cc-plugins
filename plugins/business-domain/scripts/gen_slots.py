#!/usr/bin/env python3
"""Write schema/domain.slots.json from schema/domain.yaml.

The JSON Schema carries no LinkML annotation, so this step reads the edge
rules, the ID prefixes, and the key order from the source. It needs PyYAML
only, so ddd.py and the tests never need linkml.

    python3 gen_slots.py schema/domain.yaml > schema/domain.slots.json
"""
import json
import sys
from pathlib import Path

import yaml


def annotation(node: dict, name: str, default=None):
    value = (node.get("annotations") or {}).get(name, default)
    if isinstance(value, dict):  # the long form: {tag: name, value: ...}
        value = value.get("value", default)
    return value


def build(source: dict, base: dict | None = None) -> dict:
    types = {}
    for name, cls in (source.get("classes") or {}).items():
        prefix = annotation(cls, "id_prefix")
        if prefix is None:
            continue  # Stamp and SourceRef are parts of a page, not pages
        types[name] = {
            "prefix": prefix,
            "directory": annotation(cls, "directory"),
            "key_order": list(cls.get("slots") or []),
        }
    edges = {}
    for name, slot in (source.get("slots") or {}).items():
        slot = slot or {}
        targets = annotation(slot, "targets")
        if targets is None:
            continue
        edges[name] = {
            "targets": targets.split(),
            "kinds": (annotation(slot, "target_kinds") or "").split(),
            "multivalued": bool(slot.get("multivalued", False)),
            "acyclic": bool(annotation(slot, "acyclic", False)),
            "distinct": bool(annotation(slot, "distinct", False)),
            "inverse_label": annotation(slot, "inverse_label"),
        }
    enums = source.get("enums") or {}
    status_enum = enums.get("PageStatus") or (base or {}).get("enums", {}).get("OkfStatus")
    statuses = list(status_enum["permissible_values"])
    return {"statuses": statuses, "types": types, "edges": edges}


if __name__ == "__main__":
    path = Path(sys.argv[1])
    with open(path, encoding="utf-8") as handle:
        source = yaml.safe_load(handle)
    with open(path.parent / "../../knowledge/schema/base.yaml", encoding="utf-8") as handle:
        base = yaml.safe_load(handle)
    json.dump(build(source, base), sys.stdout, indent=2)
    sys.stdout.write("\n")
