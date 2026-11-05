#!/usr/bin/env python3
"""Write schema/system-design.slots.json from schema/system-design.yaml.

The JSON Schema carries no LinkML annotation, so this step reads the types,
the areas, and the edges from the source. It needs PyYAML only.

    python3 gen_slots.py schema/system-design.yaml > schema/system-design.slots.json
"""
import json
import sys
from pathlib import Path

import yaml


def annotation(node, name, default=None):
    value = ((node or {}).get("annotations") or {}).get(name, default)
    if isinstance(value, dict):
        value = value.get("value", default)
    return value


def edge(slot):
    return {"targets": str(annotation(slot, "targets")).split(),
            "multivalued": bool(slot.get("multivalued", False)),
            "acyclic": bool(annotation(slot, "acyclic", False)),
            "inverse_label": annotation(slot, "inverse_label")}


def build(source: dict, base: dict) -> dict:
    slots, classes = source.get("slots") or {}, source.get("classes") or {}
    types = {}
    for name, cls in classes.items():
        prefix, fixed = annotation(cls, "id_prefix"), annotation(cls, "fixed")
        if prefix is None and fixed is None:
            continue
        types[name] = {"prefix": prefix, "directory": annotation(cls, "directory") or "",
                       "fixed": fixed, "key_order": list(cls.get("slots") or [])}
    edges = {}
    for name in types:
        for slot_name in classes[name].get("slots") or []:
            slot = slots.get(slot_name) or {}
            if annotation(slot, "targets"):
                edges.setdefault(slot_name, edge(slot))
            inner = classes.get(slot.get("range"))
            for part in (inner or {}).get("slots") or []:
                if annotation(slots.get(part), "targets"):
                    edges.setdefault(f"{slot_name}.{part}", edge(slots[part]))
    area_values = source["enums"]["AreaSlug"]["permissible_values"]
    return {"statuses": list(base["enums"]["OkfStatus"]["permissible_values"]),
            "areas": list(area_values),
            "anchors": {slug: annotation(value, "anchor") for slug, value in area_values.items()},
            "types": types, "edges": edges}


if __name__ == "__main__":
    path = Path(sys.argv[1])
    with open(path, encoding="utf-8") as handle:
        source = yaml.safe_load(handle)
    with open(path.parent / "../../knowledge/schema/base.yaml", encoding="utf-8") as handle:
        base = yaml.safe_load(handle)
    json.dump(build(source, base), sys.stdout, indent=2)
    sys.stdout.write("\n")
