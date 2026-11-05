"""`prd.py stage`: the stage of each capability, early or mature.

A capability is mature when a roadmap work item in state `done` or `released` traces to it.
A Story or a Task stores a trace only when it narrows the traces of its
parent, so an item with no `traces` uses the traces of its parent chain.
`/product:simulate` reads the stage to choose how many gaps it asks the owner.
"""
from pathlib import Path

from . import DataError
from .graph import targets_of
from .ids import resolve
from .page import load_page
from .registry import DELIVERED_STATES, TYPES, WORK_ITEMS
from .tree import bundle_dir

CAPABILITY_DIR = TYPES["Capability"].directory


def _work_items(root: Path) -> dict[str, dict]:
    """The frontmatter of each work item, by its bundle-relative path."""
    roadmap = bundle_dir(root, "roadmap")
    out = {}
    for type_name in WORK_ITEMS:
        directory = roadmap / TYPES[type_name].directory
        for path in sorted(directory.glob("*.md")) if directory.is_dir() else []:
            if path.name in ("index.md", "closed.md"):
                continue
            frontmatter = load_page(path).frontmatter
            if frontmatter.get("type") == type_name:
                out[f"/{TYPES[type_name].directory}/{path.name}"] = frontmatter
    return out


def _traces(items: dict[str, dict], key: str) -> list[str]:
    """The own traces of an item, or the traces of the nearest parent that
    has some. A parent that is absent or a cycle ends the walk."""
    seen = set()
    while key in items and key not in seen:
        seen.add(key)
        own = targets_of(items[key], "traces")
        if own:
            return own
        parents = targets_of(items[key], "parent")
        if not parents:
            return []
        key = parents[0]
    return []


def mature(root: Path) -> dict[str, str]:
    """Each capability that a delivered item reaches, with the first such item."""
    items = _work_items(root)
    out: dict[str, str] = {}
    for key in sorted(items):
        if items[key].get("state") not in DELIVERED_STATES:
            continue
        for target in _traces(items, key):
            stem = Path(target).stem
            if f"/{CAPABILITY_DIR}/" in target:
                out.setdefault(stem, Path(key).stem)
    return out


def rows(root: Path, identifiers: list[str]) -> list[str]:
    if identifiers:
        paths = [resolve(root, i) for i in identifiers]
        for path, identifier in zip(paths, identifiers):
            if path.parent.name != CAPABILITY_DIR:
                raise DataError(f"{identifier} is not a capability")
    else:
        directory = bundle_dir(root, "prd") / CAPABILITY_DIR
        paths = [p for p in sorted(directory.glob("*.md"))
                 if p.name not in ("index.md", "closed.md")]
    done = mature(root)
    return [f"{p.stem}\tmature\t{done[p.stem]}" if p.stem in done
            else f"{p.stem}\tearly\t-" for p in paths]
