"""`ddd.py merge FROM INTO`: one page takes the place of another.

Each edge that points to FROM points to INTO. FROM gets
`status: deprecated` and keeps its file. INTO gets FROM's ID and title in
`aliases`. A list that then names one page two times keeps one, and an edge
of INTO to itself goes.
"""
from pathlib import Path

from . import DataError, UsageError
from . import logbook, regen
from .bundle import read, ref_of
from .ids import resolve
from .page import dump, write_text
from .schema import edges


def _unique(items: list) -> list:
    out = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def _repoint(frontmatter: dict, old: str, new: str, old_id: str,
             new_source: dict, own: str) -> bool:
    """Point each edge of one frontmatter from `old` to `new`. Returns True
    when a value changed."""
    changed = False
    for field_name in edges():
        value = frontmatter.get(field_name)
        if value is None:
            continue
        if field_name == "sources":
            items = [dict(new_source) if isinstance(item, dict)
                     and item.get("id") == old_id else item for item in value]
            items = _unique(items)
        elif isinstance(value, list):
            items = _unique([new if item == old else item for item in value])
            items = [item for item in items if item != own]
        elif value == old:
            items = new
        else:
            continue
        if items != value:
            frontmatter[field_name] = items
            changed = True
    return changed


def merge(root: Path, source_key: str, into_key: str, actor: str) -> list:
    bundle = read(root)
    source_path = resolve(bundle, source_key)
    into_path = resolve(bundle, into_key)
    if source_path == into_path:
        raise UsageError("FROM and INTO are the same page")
    source = bundle.pages.get(source_path)
    into = bundle.pages.get(into_path)
    if source is None or into is None:
        raise DataError("FROM or INTO does not parse. Run `ddd.py check`.")
    if source.type != into.type:
        raise DataError(f"{source.id} is a {source.type} and {into.id} is a "
                        f"{into.type}. merge joins two pages of one type.")
    if not source.live or not into.live:
        raise DataError("FROM and INTO must not be deprecated")

    old, new = ref_of(bundle, source_path), ref_of(bundle, into_path)
    new_source = {"id": into.id, "resource": into.frontmatter.get("resource", new)}
    written = []
    for path, page in bundle.pages.items():
        if path == source_path:
            continue
        frontmatter = dict(page.frontmatter)
        changed = _repoint(frontmatter, old, new, source.id, new_source,
                           ref_of(bundle, path))
        if path == into_path:
            # A single value stays one alias: list() of a string gives
            # its letters, and list() of a number fails.
            value = frontmatter.get("aliases")
            aliases = list(value) if isinstance(value, list) else \
                ([value] if value is not None else [])
            for alias in (source.id, source.title):
                if alias not in aliases:
                    aliases.append(alias)
                    changed = True
            frontmatter["aliases"] = aliases
        if changed:
            write_text(path, dump(frontmatter, page.body))
            written.append(path)
    frontmatter = dict(source.frontmatter, status="deprecated")
    write_text(source_path, dump(frontmatter, source.body))
    written.append(source_path)

    when = logbook.now()
    logbook.append(bundle.dir / "log.md", logbook.entry(
        "Merge", f"{source.id} ({source.title}) into {into.id} ({into.title})",
        actor, when), when)
    written.append(bundle.dir / "log.md")
    for path in regen.write(root):
        if path not in written:
            written.append(path)
    return written
