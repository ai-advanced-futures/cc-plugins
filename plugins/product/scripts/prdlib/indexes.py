"""Every index.md and every closed.md.

An index has no frontmatter, except okf_version in the two bundle-root
indexes. Each line is `* [<ID>: <title>](<file>) - <description>`. A work-item
index lists open items only and groups them by milestone, so the file stays
short.
"""
from pathlib import Path

from .registry import CLOSED_STATES, DIRECTORY_ORDER, WORK_ITEMS

OKF_VERSION = "0.2"
NO_MILESTONE = "No milestone"
NO_WORK_ITEM = "No work item"
RUNS_PER_ITEM = 10


def line(page_id: str, frontmatter: dict, link: str) -> str:
    return (f"* [{page_id}: {frontmatter.get('title', page_id)}]({link}) - "
            f"{frontmatter.get('description', '')}")


def _sort_key(path: Path):
    stem = path.stem
    prefix, _, number = stem.rpartition("-")
    return (prefix, int(number)) if number.isdigit() else (stem, 0)


def _target_title(target, pages: dict, bundle_root: Path, fallback: str,
                  with_title: bool = True) -> str:
    """The heading of the group a page belongs to: the ID of the page its
    `milestone` or its `item` names, and that page's title. `fallback` is the
    heading for a target that is empty or that names no page.
    """
    if not target:
        return fallback
    path = bundle_root / str(target).lstrip("/")
    if path not in pages:
        return fallback
    if not with_title:
        return path.stem
    return f"{path.stem}: {pages[path][1].get('title', path.stem)}"


def _grouped(entries: list[tuple[str, list[str]]]) -> list[str]:
    out = []
    for heading, lines in entries:
        out.extend(["", f"## {heading}", ""] + lines)
    return out


def by_parent(pages: dict) -> dict:
    """directory -> its pages, in ID order.

    `plan` renders 24 type directories plus a root index for each bundle,
    and each one filtered the whole page map on `p.parent`. One pass here
    answers all of them.
    """
    out = {}
    for path in pages:
        out.setdefault(path.parent, []).append(path)
    return {parent: sorted(paths, key=_sort_key)
            for parent, paths in out.items()}


def _in(directory: Path, pages: dict, index: dict | None) -> list:
    if index is not None:
        return index.get(directory, [])
    return sorted((p for p in pages if p.parent == directory), key=_sort_key)


def directory_index(directory: Path, bundle_root: Path, type_name: str,
                    pages: dict, index: dict | None = None) -> str | None:
    """The index.md of one type directory, or None when it holds no page.

    `index` is a by_parent() map the caller already built."""
    own = _in(directory, pages, index)
    if not own:
        return None
    head = [f"# {directory.name}"]

    if type_name in WORK_ITEMS:
        open_pages = [p for p in own
                      if pages[p][1].get("state") not in CLOSED_STATES]
        return "\n".join(head + _grouped(
            _by_milestone(open_pages, pages, bundle_root))).rstrip() + "\n"

    if type_name == "AcceptanceCriterion":
        groups = {}
        for path in own:
            key = _target_title(pages[path][1].get("item", ""), pages,
                                bundle_root, NO_WORK_ITEM)
            groups.setdefault(key, []).append(
                line(path.stem, pages[path][1], path.name))
        return "\n".join(head + _grouped(sorted(groups.items()))).rstrip() + "\n"

    if type_name == "Run":
        groups = {}
        for path in sorted(own, key=lambda p: p.stem, reverse=True):
            key = _target_title(pages[path][1].get("item", ""), pages,
                                bundle_root, NO_WORK_ITEM, with_title=False)
            groups.setdefault(key, [])
            if len(groups[key]) < RUNS_PER_ITEM:
                groups[key].append(line(path.stem, pages[path][1], path.name))
        return "\n".join(head + _grouped(sorted(groups.items()))).rstrip() + "\n"

    lines = [line(p.stem, pages[p][1], p.name) for p in own]
    return "\n".join(head + [""] + lines).rstrip() + "\n"


def _by_milestone(paths, pages, bundle_root):
    groups = {}
    for path in paths:
        key = _target_title(pages[path][1].get("milestone", ""), pages,
                            bundle_root, NO_MILESTONE)
        groups.setdefault(key, []).append(
            line(path.stem, pages[path][1], path.name))
    ordered = sorted(k for k in groups if k != NO_MILESTONE)
    if NO_MILESTONE in groups:
        ordered.append(NO_MILESTONE)
    return [(k, groups[k]) for k in ordered]


def closed_index(directory: Path, bundle_root: Path, type_name: str,
                 pages: dict, index: dict | None = None) -> str | None:
    """closed.md for one work-item directory, or None when nothing is closed."""
    if type_name not in WORK_ITEMS:
        return None
    closed = [p for p in _in(directory, pages, index)
              if pages[p][1].get("state") in CLOSED_STATES]
    if not closed:
        return None
    items = [(p, pages[p][1]) for p in closed]
    title = f"Closed {directory.name}"
    head = ["---", "type: ClosedItems", f"title: {title}",
            f"description: The {directory.name} that are done or cancelled.",
            "status: stable",
            "generated:", "  by: process:prd-regen", f"  at: '{_latest_at(items)}'", "---", "",
            f"# {title}"]
    return "\n".join(head + _grouped(
        _by_milestone(closed, pages, bundle_root))).rstrip() + "\n"


def _latest_at(items) -> str:
    """The newest generated.at of the listed items: a fixed value, so regen stays stable."""
    stamps = [str((fm.get("generated") or {}).get("at")) for _path, fm in items
              if isinstance(fm.get("generated"), dict) and fm["generated"].get("at")]
    return max(stamps) if stamps else "1970-01-01T00:00:00Z"


def root_index(bundle: str, bundle_root: Path, pages: dict,
               index: dict | None = None) -> str:
    head = ["---", f"okf_version: '{OKF_VERSION}'", "---", "", f"# {bundle}", ""]
    lines = []
    if bundle == "prd":
        product = bundle_root / "product.md"
        if product in pages:
            lines.append(f"* [Product](product.md) - "
                         f"{pages[product][1].get('description', '')}")
    else:
        for path in sorted(p for p in pages
                           if pages[p][1].get("type") == "Project"):
            lines.append(f"* [Project]({path.relative_to(bundle_root)}) - "
                         f"{pages[path][1].get('description', '')}")
    for name in DIRECTORY_ORDER[bundle]:
        # The directory path is built one time, not one time for each page.
        directory = bundle_root / name
        count = len(_in(directory, pages, index))
        if count:
            lines.append(f"* [{name}/]({name}/index.md) - {count} pages")
    return "\n".join(head + lines).rstrip() + "\n"
