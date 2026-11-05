"""Read the bundle: each page that parses, and each file that does not.

A page file is each `.md` file below the bundle directory, except each
`index.md` and the bundle-root `log.md` and `manifest.md`.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import DataError, UsageError
from .config import bundle_dir
from .page import Page, parse
from .schema import edges, types

PAGE_REF_RE = re.compile(r"^/[a-z]+/[A-Z]+-\d{2,}\.md$")
ID_RE = re.compile(r"^([A-Z]+)-(\d{2,})$")


@dataclass
class Bundle:
    root: Path
    dir: Path
    pages: dict = field(default_factory=dict)   # path -> Page
    broken: dict = field(default_factory=dict)  # path -> message
    edges: dict = field(default_factory=dict)   # path -> stored_edges, found once


def sort_key(page_id: str):
    """TERM-2 before TERM-10. An ID of another shape sorts by its text."""
    match = ID_RE.match(page_id)
    return (match.group(1), int(match.group(2))) if match else (page_id, 0)


def page_files(directory: Path) -> list:
    out = []
    for path in directory.rglob("*.md"):
        if path.name == "index.md":
            continue
        if path.parent == directory and path.name in ("log.md", "manifest.md"):
            continue
        out.append(path)
    return sorted(out, key=lambda p: (str(p.parent), sort_key(p.stem)))


def read(root: Path) -> Bundle:
    bundle = Bundle(root=root, dir=bundle_dir(root))
    for path in page_files(bundle.dir):
        try:
            bundle.pages[path] = parse(path)
        except (DataError, UnicodeDecodeError) as error:
            bundle.broken[path] = str(error)
        except OSError as error:
            raise UsageError(f"cannot read {path}: {error}")
    return bundle


def ref_of(bundle: Bundle, path: Path) -> str:
    """The bundle-relative form of a page path, as in /terms/TERM-01.md."""
    return "/" + path.relative_to(bundle.dir).as_posix()


def _target(bundle: Bundle, field_name: str, item):
    """(target ID, target path) of one stored entry, or None when the entry
    has the wrong shape. Rule E2 reports the shape."""
    if field_name == "sources":
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            return None
        page_id = item["id"]
        directory = types()[edges()["sources"]["targets"][0]]["directory"]
        return page_id, bundle.dir / directory / f"{page_id}.md"
    if not isinstance(item, str) or not PAGE_REF_RE.match(item):
        return None
    return Path(item).stem, bundle.dir / item[1:]


def names(value) -> list:
    """The string items of a list field. A value of the wrong shape gives an
    empty list: rule E2 reports the shape, and no other rule may fail on it."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def glossary_types() -> list:
    """The types that name a context with `context`: Term, Aggregate, and
    Event."""
    return [name for name, spec in types().items()
            if "context" in spec["key_order"]]


def stored_edges(bundle: Bundle, page: Page) -> list:
    """(field, target ID, target path) for each edge stored on the page, in
    the order of the edge table, then in list order. Found one time for each
    page: the pages of a bundle do not change after `read`."""
    if page.path in bundle.edges:
        return bundle.edges[page.path]
    out = []
    for field_name in edges():
        value = page.frontmatter.get(field_name)
        if value is None:
            continue
        for item in value if isinstance(value, list) else [value]:
            found = _target(bundle, field_name, item)
            if found is not None:
                out.append((field_name, *found))
    bundle.edges[page.path] = out
    return out


def context_page(bundle: Bundle, page):
    """The Context page of a page: a Context is its own context, and a Term,
    Aggregate, or Event names one with `context`. None when there is none."""
    if page is None:
        return None
    if page.type == "Context":
        return page
    for field_name, _target_id, target in stored_edges(bundle, page):
        if field_name == "context":
            found = bundle.pages.get(target)
            if found is not None and found.type == "Context":
                return found
    return None


def context_id(bundle: Bundle, page) -> str:
    """The ID of the context of a page, or `-` when there is none."""
    found = context_page(bundle, page)
    return found.id if found is not None else "-"
