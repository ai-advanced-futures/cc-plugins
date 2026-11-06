"""IDs: the next free ID, and the page of an ID, an alias, or a path."""
from __future__ import annotations

from jtbdlib import DataError, UsageError, manifest, schema
from jtbdlib.bundle import ID_RE


def fold(text) -> str:
    return " ".join(str(text).split()).casefold()


def next_id(directory, type_name) -> str:
    spec = schema.types()[type_name]
    prefix = spec["prefix"]
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
        file = (directory / key.lstrip("/")).resolve()
        # A path key must name a page of a type folder inside the bundle. A key such as /../x.md would leave the bundle.
        folders = {spec["directory"] for spec in schema.types().values()}
        if file.parent.parent != directory.resolve() or file.parent.name not in folders:
            raise UsageError(f"{key} is not a page path: use /<type folder>/<page>.md inside the bundle")
        if file.is_file():
            return file
        raise DataError(f"no page is at {key}")
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


def require_type(type_name):
    spec = schema.types().get(type_name)
    if spec is None:
        raise UsageError(f"{type_name!r} is not a page type: use {', '.join(schema.types())}")
    return spec
