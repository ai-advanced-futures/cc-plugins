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
from .textsafe import escape_controls, first_bad_character
from .tree import BUNDLES, bundle_dir

PROTECTED = ("type", "generated", "protected") + tuple(REFUSED_SET_FIELDS)


def parse_pair(item):
    if "=" not in item:
        raise UsageError(f"{item!r} is not KEY=VALUE")
    key, value = item.split("=", 1)
    return key.strip(), (load_set_value(value) if value.strip() else "")


def _bundle_of(root, path) -> str:
    for bundle in BUNDLES:
        try:
            path.relative_to(bundle_dir(root, bundle))
            return bundle
        except ValueError:
            continue
    raise DataError(f"{escape_controls(path)} is not in a bundle")


def _save(root, key, change, actor) -> Path:
    """Read, check, change and write 1 page, log the change, and run the regen,
    all inside 1 write lock (STORY-441, #1960). A read before the lock can hold
    an old copy of the page, and the write then loses the change that another
    run made in the meantime.

    `change(page, frontmatter)` checks its arguments, changes the copy of the
    frontmatter, and gives `(entry, written)`: the `(kind, text)` of the log
    line and the link fields that the call writes. Each check runs after the
    resolve and the load, as it did before STORY-441."""
    # D-024: `generated.by` names the plugin whose code writes the page. The
    # OKF actor of the stamp has no agent form, so an agent goes into 1 line
    # of log.md (STORY-24). A person keeps the stamp, and writes no line.
    agent = actor if actor and actor.startswith("agent:") else None
    with write_lock(root):
        path = ids.resolve(root, key)
        page = load_page(path)
        frontmatter = dict(page.frontmatter)
        entry, written = change(page, frontmatter)
        when = datetime.now(timezone.utc)
        frontmatter["generated"] = {
            "by": plugin_actor() if agent else (actor or plugin_actor()),
            "at": logbook.timestamp(when)}
        problems = validate_frontmatter(page.type, frontmatter)
        if problems:
            raise DataError("the page is not valid, so nothing is written: " + "; ".join(problems))
        bundle = _bundle_of(root, path)
        # Only the fields that this call writes (row 8 of the spec of FEATURE-31),
        # after the schema check, so a wrong form gets the text of the schema.
        check_targets(root, bundle, frontmatter, written)
        page.frontmatter = frontmatter
        write_page(page)
        if agent:
            base = bundle_dir(root, bundle)
            kind, text = entry
            logbook.append_entries(base / "log.md", [logbook.entry_line(
                kind, path.stem, path.relative_to(base).as_posix(), text,
                agent, when)], when)
        regen.write_locked(root)
    return path


def set_fields(root, key, pairs, actor=None) -> Path:
    def change(page, frontmatter):
        written = []
        for item in pairs:
            name, value = parse_pair(item)
            if name in PROTECTED:
                raise UsageError(f"set does not change {name}: use prd.py state, prd.py drift, or ask a person")
            frontmatter[name] = value
            written.append(name)
        return ("Set", ", ".join(dict.fromkeys(written))), written
    return _save(root, key, change, actor)


def link(root, key, field, target, actor=None, remove=False) -> Path:
    def change(page, frontmatter):
        if field in ("traces", "includes", "state"):
            raise UsageError(f"{field} changes through prd.py new --traces or the skills, not link")
        current = frontmatter.get(field)
        if not is_single_valued(page.type, field):
            values = list(current or [])
            kept = [v for v in values if v != target and not (isinstance(v, dict) and target in v.values())]
            if remove and kept == values:
                raise DataError(f"{escape_controls(key)} has no "
                                f"{escape_controls(field)} link to "
                                f"{escape_controls(target)}")
            frontmatter[field] = kept if remove else (values if target in values else values + [target])
        elif remove:
            if current != target:
                raise DataError(f"{escape_controls(key)} has no "
                                f"{escape_controls(field)} link to "
                                f"{escape_controls(target)}")
            frontmatter.pop(field)
        else:
            frontmatter[field] = target
        return (("Unlink" if remove else "Link", f"{field} {target}"),
                () if remove else (field,))
    return _save(root, key, change, actor)


def remove(root, key, actor=None) -> Path:
    """Take the lock, then remove the page (`_remove`)."""
    with write_lock(root):
        return _remove(root, key, actor)


def _remove(root, key, actor) -> Path:
    """`remove` with the lock held by the caller. The read of the page, the
    `protected` refusal, the write of the manifest or of `.retired-ids.json`,
    the unlink of the page, the `Forget` line and the regen are inside 1 lock
    (STORY-441)."""
    path = ids.resolve(root, key)
    page = load_page(path)
    if page.frontmatter.get("protected") is True:
        raise DataError(f"{escape_controls(key)} is protected. Only a person "
                        "can remove protected: true.")
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
    path.unlink()
    logbook.append_entries(base / "log.md", [logbook.entry_line(
        "Forget", path.stem, link_text.lstrip("/"), "removed", actor or plugin_actor(),
        datetime.now(timezone.utc))], datetime.now(timezone.utc))
    regen.write_locked(root)
    return path


def log(root, operation, text, bundle="prd", actor=None) -> None:
    # One line in log.md (issue 1915). The text folds its whitespace into
    # single spaces, as it always did, so a line break there is safe. What is
    # left after the fold must hold no control character: an ESC moves a
    # terminal cursor. The actor is checked once in `prd.py` `main`.
    text = " ".join(text.split())
    bad = first_bad_character(text)
    if bad:
        raise UsageError(f"the text of log must be one line, it holds the "
                         f"character {bad}")
    when = datetime.now(timezone.utc)
    line = f"* **{operation}**: {text}, by {actor or plugin_actor()}, at {logbook.timestamp(when)}"
    with write_lock(root):
        logbook.append_entries(bundle_dir(root, bundle) / "log.md", [line], when)
