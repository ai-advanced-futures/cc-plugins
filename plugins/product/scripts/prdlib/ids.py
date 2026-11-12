"""ID allocation and lookup.

The script finds the highest number in the directory, deprecated pages
included, and adds one. An ID is permanent: a removed requirement keeps its
file with `status: deprecated`, so the number is never assigned twice. Call
next_id inside write_lock().
"""
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import DataError
from .page import load_page, split_frontmatter
from .registry import ID_RE, TYPES
from .textsafe import escape_controls
from .tree import BUNDLES, bundle_dir, iter_pages

MIN_DIGITS = 2


def _retired_ids(base: Path) -> list[str]:
    """The IDs `remove` retired, from the manifest when one exists and from
    its stand-in file otherwise (`edit.remove`, before Task 62)."""
    manifest = base / "manifest.md"
    if manifest.is_file():
        head, _body = split_frontmatter(manifest.read_text("utf-8"))
        return yaml.safe_load(head).get("retired_ids") or []
    retired_file = base / ".retired-ids.json"
    if retired_file.is_file():
        return json.loads(retired_file.read_text("utf-8"))
    return []


def next_id(root: Path, type_name: str) -> str:
    spec = TYPES[type_name]
    if spec.prefix is None:
        raise DataError(f"{type_name} pages have no ID")
    directory = bundle_dir(root, spec.bundle) / spec.directory
    highest = 0
    if directory.is_dir():
        for path in directory.glob(f"{spec.prefix}-*.md"):
            match = ID_RE.match(path.stem)
            if match and match.group(1) == spec.prefix:
                highest = max(highest, int(match.group(2)))
    for retired in _retired_ids(bundle_dir(root, spec.bundle)):
        match = ID_RE.match(retired)
        if match and match.group(1) == spec.prefix:
            highest = max(highest, int(match.group(2)))
    return f"{spec.prefix}-{highest + 1:0{MIN_DIGITS}d}"


def new_run_id(when: datetime | None = None, token: str | None = None) -> str:
    """A time and 4 random characters. Two agents with no lock between clones
    cannot get the same ID."""
    when = when or datetime.now(timezone.utc)
    token = token or secrets.token_hex(2)
    return f"RUN-{when.strftime('%Y%m%d')}-{when.strftime('%H%M%S')}-{token}"


def resolve(root: Path, identifier: str, tree: dict | None = None) -> Path:
    """The path of a page, by ID first and by alias second.

    `tree` is a `regen.collect` map the caller already holds. Given it, the
    lookup reads no file: a loop that resolves one page per item (`github
    pull`, `github apply`, `expire`) otherwise walks both bundles again for
    each item, and parses every page again on an alias miss.
    """
    if tree is not None:
        for path in tree:
            if path.stem == identifier:
                return path
        for path, (_bundle, frontmatter, _body) in tree.items():
            if identifier in (frontmatter.get("aliases") or []):
                return path
        raise DataError(
            f"no page has the ID or the alias {escape_controls(identifier)}")

    candidates = []
    for bundle in BUNDLES:
        base = bundle_dir(root, bundle)
        if base.is_dir():
            candidates.extend(iter_pages(base))
    for path in candidates:
        if path.stem == identifier:
            return path
    for path in candidates:
        try:
            aliases = load_page(path).frontmatter.get("aliases") or []
        except DataError:
            continue
        if identifier in aliases:
            return path
    raise DataError(
            f"no page has the ID or the alias {escape_controls(identifier)}")
