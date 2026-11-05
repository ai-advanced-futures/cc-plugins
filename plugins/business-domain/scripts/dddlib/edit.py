"""set, link, unlink, and remove (standard section 8)."""
from __future__ import annotations

from pathlib import Path

import yaml

from dddlib import DataError, UsageError, logbook, regen, schema, standard
from dddlib.bundle import read, ref_of
from dddlib.config import bundle_dir
from dddlib.ids import resolve
from dddlib.page import dump, order_keys, parse, write_text

PROTECTED = ("type", "generated", "protected")


def parse_pair(item):
    if "=" not in item:
        raise UsageError(f"{item!r} is not KEY=VALUE")
    key, value = item.split("=", 1)
    return key.strip(), (yaml.safe_load(value) if value.strip() else "")


def _load(root, key):
    bundle = read(root)
    path = resolve(bundle, key)
    page = parse(path)
    if page.frontmatter is None:
        raise DataError(f"{path.name} has no frontmatter")
    return bundle, path, page


def _save(root, path, page, frontmatter, actor) -> Path:
    frontmatter["generated"] = {"by": actor, "at": logbook.timestamp(logbook.now())}
    problems = schema.validate_frontmatter(page.type, frontmatter)
    if problems:
        raise DataError("the page is not valid, so nothing is written: " +
                        "; ".join(f"{field}: {message}" for field, message in problems))
    write_text(path, dump(order_keys(frontmatter), page.body))
    regen.write(root)
    return path


def set_fields(root, key, pairs, actor) -> Path:
    _bundle, path, page = _load(root, key)
    frontmatter = dict(page.frontmatter)
    for item in pairs:
        name, value = parse_pair(item)
        if name in PROTECTED:
            raise UsageError(f"set does not change {name}. Only a person changes protected.")
        frontmatter[name] = value
    return _save(root, path, page, frontmatter, actor)


def link(root, key, field, target, actor, remove=False) -> Path:
    edges = schema.edges()
    if field not in edges:
        raise UsageError(f"{field} is not an edge of ddd: use {', '.join(edges)}")
    _bundle, path, page = _load(root, key)
    frontmatter = dict(page.frontmatter)
    current = frontmatter.get(field)
    if edges[field]["multivalued"]:
        values = list(current or [])
        if remove:
            kept = [v for v in values if v != target and not (isinstance(v, dict) and target in v.values())]
            if kept == values:
                raise DataError(f"{key} has no {field} link to {target}")
            frontmatter[field] = kept
        elif target not in values:
            frontmatter[field] = values + [target]
    elif remove:
        if current != target:
            raise DataError(f"{key} has no {field} link to {target}")
        frontmatter.pop(field)
    else:
        frontmatter[field] = target
    return _save(root, path, page, frontmatter, actor)


def retire(directory: Path, page_id: str) -> None:
    path = directory / "manifest.md"
    if not path.is_file():
        # A full manifest, so the general check finds no missing field.
        standard.write_manifest(directory)
    head, body = path.read_text("utf-8").split("---\n", 2)[1:]
    data = yaml.safe_load(head)
    data["retired_ids"] = sorted(set(data.get("retired_ids") or []) | {page_id})
    path.write_text("---\n" + yaml.safe_dump(data, sort_keys=False, width=1000) + "---\n" + body, encoding="utf-8")


def remove(root, key, actor) -> Path:
    bundle, path, page = _load(root, key)
    if page.frontmatter.get("protected") is True:
        raise DataError(f"{key} is protected. Only a person can remove protected: true.")
    page_ref = ref_of(bundle, path)
    path.unlink()
    retire(bundle_dir(root), path.stem)
    when = logbook.now()
    logbook.append(bundle_dir(root) / "log.md", logbook.entry("Forget", f"removed {page_ref}", actor, when), when)
    regen.write(root)
    return path
