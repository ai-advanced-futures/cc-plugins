#!/usr/bin/env python3
"""Write schema/competitive-intelligence.slots.json from schema/competitive-intelligence.yaml.

The JSON Schema carries no LinkML annotation, so this step reads the types and
the edges from the source. It needs PyYAML only.

    python3 gen_slots.py schema/competitive-intelligence.yaml ../knowledge/schema/base.yaml > schema/competitive-intelligence.slots.json
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
            "inverse_label": annotation(slot, "inverse_label")}


def build(source: dict, base: dict) -> dict:
    slots, classes = source.get("slots") or {}, source.get("classes") or {}
    types = {}
    for name, cls in classes.items():
        prefix = annotation(cls, "id_prefix")
        if prefix is None:
            continue
        types[name] = {"prefix": prefix, "directory": annotation(cls, "directory") or "",
                       "key_order": list(cls.get("slots") or [])}
    edges = {}
    for name in types:
        for slot_name in classes[name].get("slots") or []:
            slot = slots.get(slot_name) or {}
            if annotation(slot, "targets"):
                edges.setdefault(slot_name, edge(slot))
    return {"statuses": list(base["enums"]["OkfStatus"]["permissible_values"]), "types": types, "edges": edges}


if __name__ == "__main__":
    path, base_path = Path(sys.argv[1]), Path(sys.argv[2])
    with open(path, encoding="utf-8") as handle:
        source = yaml.safe_load(handle)
    with open(base_path, encoding="utf-8") as handle:
        base = yaml.safe_load(handle)
    json.dump(build(source, base), sys.stdout, indent=2)
    sys.stdout.write("\n")
