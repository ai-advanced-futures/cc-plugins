#!/usr/bin/env python3
"""Turn gen-json-schema output into the subset that adr_lint.py reads.

Standard library only. The vendored lint has no jsonschema package and no
install step, so it reads a small, flat keyword set. LinkML writes `$defs`,
`$ref`, a `type` list and a null branch in every `anyOf`, and the raw output
stops the lint with a TypeError. This step removes all four shapes.

    python3 flatten_schema.py <raw json schema> > adr.schema.json
"""
import json
import sys

DROP = {"$defs", "$schema", "$id", "title", "description", "format",
        "metamodel_version", "version"}
NULL = {"type": "null"}


def _resolve(node, defs, seen=()):
    if isinstance(node, list):
        return [_resolve(item, defs, seen) for item in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        name = node["$ref"].rsplit("/", 1)[-1]
        if not node["$ref"].startswith("#/$defs/") or name not in defs:
            raise ValueError(f"cannot resolve {node['$ref']}")
        if name in seen:
            raise ValueError(f"recursive $ref: {name}")
        target = _resolve(defs[name], defs, seen + (name,))
        rest = {k: v for k, v in node.items() if k != "$ref"}
        node = {**target, **rest}
    return {k: _resolve(v, defs, seen) for k, v in node.items()}


def _simplify(node):
    # A `properties` map is walked by name, so an ADR key named `title` or
    # `description` stays; only annotation keywords are dropped.
    if isinstance(node, list):
        return [_simplify(item) for item in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for key, value in node.items():
        if key in DROP:
            continue
        if key == "properties":
            out[key] = {name: _simplify(sub) for name, sub in value.items()}
        else:
            out[key] = _simplify(value)
    if isinstance(out.get("type"), list):
        names = [name for name in out.pop("type") if name != "null"]
        rest = out
        out = ({**rest, "type": names[0]} if len(names) == 1
               else {"anyOf": [{**rest, "type": name} for name in names]})
    if "anyOf" in out:
        options = [option for option in out["anyOf"] if option != NULL]
        if len(options) == 1:
            rest = {k: v for k, v in out.items() if k != "anyOf"}
            out = {**options[0], **rest}
        else:
            out["anyOf"] = options
    return out


def flatten(schema):
    resolved = _resolve(schema, schema.get("$defs", {}))
    return _simplify(resolved)


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as handle:
        json.dump(flatten(json.load(handle)), sys.stdout, indent=2)
    sys.stdout.write("\n")
