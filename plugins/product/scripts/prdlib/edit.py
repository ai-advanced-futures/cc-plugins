"""set, link, unlink, remove, and log (standard section 8)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import DataError, UsageError, ids, logbook, regen
from .graph import check_targets
from .lock import write_lock
from .new_page import REFUSED_SET_FIELDS
from .page import load_page, load_set_value, split_frontmatter, write_page
from .schema import is_single_valued, plugin_actor, validate_frontmatter
from .tree import BUNDLES, bundle_dir

PROTECTED = ("type", "generated", "protected") + tuple(REFUSED_SET_FIELDS)


def parse_pair(item):
    if "=" not in item:
        raise UsageError(f"{item!r} is not KEY=VALUE")
    key, value = item.split("=", 1)
    return key.strip(), (load_set_value(value) if value.strip() else "")


def _now() -> str:
    return logbook.timestamp(datetime.now(timezone.utc))


def _bundle_of(root, path) -> str:
    for bundle in BUNDLES:
        try:
            path.relative_to(bundle_dir(root, bundle))
            return bundle
        except ValueError:
            continue
    raise DataError(f"{path} is not in a bundle")


def _save(root, path, page, frontmatter, actor, written=()) -> Path:
    frontmatter["generated"] = {"by": actor or plugin_actor(), "at": _now()}
    problems = validate_frontmatter(page.type, frontmatter)
    if problems:
        raise DataError("the page is not valid, so nothing is written: " + "; ".join(problems))
    # Only the fields that this call writes (row 8 of the spec of FEATURE-31),
    # after the schema check, so a wrong form gets the text of the schema.
    check_targets(root, _bundle_of(root, path), frontmatter, written)
    page.frontmatter = frontmatter
    with write_lock(root):
        write_page(page)
    regen.write(root)
    return path


def set_fields(root, key, pairs, actor=None) -> Path:
    path = ids.resolve(root, key)
    page = load_page(path)
    frontmatter = dict(page.frontmatter)
    written = []
    for item in pairs:
        name, value = parse_pair(item)
        if name in PROTECTED:
            raise UsageError(f"set does not change {name}: use prd.py state, prd.py drift, or ask a person")
        frontmatter[name] = value
        written.append(name)
    return _save(root, path, page, frontmatter, actor, written)


def link(root, key, field, target, actor=None, remove=False) -> Path:
    path = ids.resolve(root, key)
    page = load_page(path)
    frontmatter = dict(page.frontmatter)
    if field in ("traces", "includes", "state"):
        raise UsageError(f"{field} changes through prd.py new --traces or the skills, not link")
    current = frontmatter.get(field)
    if not is_single_valued(page.type, field):
        values = list(current or [])
        kept = [v for v in values if v != target and not (isinstance(v, dict) and target in v.values())]
        if remove and kept == values:
            raise DataError(f"{key} has no {field} link to {target}")
        frontmatter[field] = kept if remove else (values if target in values else values + [target])
    elif remove:
        if current != target:
            raise DataError(f"{key} has no {field} link to {target}")
        frontmatter.pop(field)
    else:
        frontmatter[field] = target
    return _save(root, path, page, frontmatter, actor,
                 () if remove else (field,))


def remove(root, key, actor=None) -> Path:
    path = ids.resolve(root, key)
    page = load_page(path)
    if page.frontmatter.get("protected") is True:
        raise DataError(f"{key} is protected. Only a person can remove protected: true.")
    bundle = _bundle_of(root, path)
    base = bundle_dir(root, bundle)
    manifest = base / "manifest.md"
    if manifest.is_file():
        head, body = split_frontmatter(manifest.read_text("utf-8"))
        data = yaml.safe_load(head)
        data["retired_ids"] = sorted(set(data.get("retired_ids") or []) | {path.stem})
        manifest.write_text("---\n" + yaml.safe_dump(data, sort_keys=False, width=1000) + "---\n" + body, encoding="utf-8")
    else:
        # Before Task 62 writes a manifest, `remove` keeps its own record of retired IDs, so
        # `next_id` never gives one out again here. Task 62's `write_manifest` folds this file
        # into `retired_ids` the first time it writes a manifest, and removes the file. [inferred]
        retired_file = base / ".retired-ids.json"
        existing = json.loads(retired_file.read_text("utf-8")) if retired_file.is_file() else []
        retired_file.write_text(json.dumps(sorted(set(existing) | {path.stem})), encoding="utf-8")
    link_text = "/" + path.relative_to(base).as_posix()
    with write_lock(root):
        path.unlink()
        logbook.append_entries(base / "log.md", [logbook.entry_line(
            "Forget", path.stem, link_text.lstrip("/"), "removed", actor or plugin_actor(),
            datetime.now(timezone.utc))], datetime.now(timezone.utc))
    regen.write(root)
    return path


def log(root, operation, text, bundle="prd", actor=None) -> None:
    when = datetime.now(timezone.utc)
    line = f"* **{operation}**: {' '.join(text.split())}, by {actor or plugin_actor()}, at {logbook.timestamp(when)}"
    with write_lock(root):
        logbook.append_entries(bundle_dir(root, bundle) / "log.md", [line], when)
