"""IDs: the next free ID, and the page of an ID, an alias, a fixed name, or a path."""
from __future__ import annotations

from sdlib import DataError, UsageError, manifest, schema
from sdlib.bundle import ID_RE


def fold(text) -> str:
    return " ".join(str(text).split()).casefold()


def next_id(directory, type_name) -> str:
    spec = schema.types()[type_name]
    prefix = spec["prefix"]
    if prefix is None:
        raise UsageError(f"{type_name} has a fixed name and no ID")
    names = [p.stem for p in (directory / spec["directory"]).glob(f"{prefix}-*.md")]
    names += list((manifest.read(directory) or {}).get("retired_ids") or [])
    numbers = [0]
    for name in names:
        match = ID_RE.match(name)
        if match and match.group(1) == prefix:
            numbers.append(int(match.group(2)))
    return f"{prefix}-{max(numbers) + 1:02d}"


def resolve(bundle, key):
    directory = bundle.dir
    if key.startswith("/"):
        file = directory / key.lstrip("/")
        if file.is_file():
            return file
        raise DataError(f"no page is at {key}")
    if key == "system":
        return directory / "system.md"
    if key in schema.areas():
        return directory / "areas" / f"{key}.md"
    match = ID_RE.match(key)
    if match and match.group(1) in schema.by_prefix():
        file = directory / schema.types()[schema.by_prefix()[match.group(1)]]["directory"] / f"{key}.md"
        if file.is_file():
            return file
    hits = [path for path, page in bundle.pages.items()
            if fold(key) in {fold(a) for a in (page.frontmatter or {}).get("aliases") or []}]
    if len(hits) == 1:
        return hits[0]
    if hits:
        raise DataError(f"the alias {key!r} names more than one page")
    raise DataError(f"no page has the ID or the alias {key!r}")
