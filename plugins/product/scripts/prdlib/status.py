"""The generated status table.

The Project page shows the milestones and the epics. A Milestone shows its
epics and features. A Feature shows its stories. A Story shows its tasks and
criteria. No page holds the full tree, so each page stays below 100 lines.
"""
from pathlib import Path

from .graph import relative_target
from .links import START as LINKS_START, join_parts, relative_link
from .registry import DELIVERED_STATES

START = "<!-- STATUS:START (generated, do not edit) -->"
END = "<!-- STATUS:END -->"
HEADER = ["| Item | State | Progress | Owner | Blocked by | Drift |",
          "| --- | --- | --- | --- | --- | --- |"]
DASH = "-"

# The type of a page -> the child types its table shows.
SHOWS = {
    "Project": ("Milestone", "Epic"),
    "Milestone": ("Epic", "Feature"),
    "Feature": ("Story",),
    "Story": ("Task", "AcceptanceCriterion"),
}


# The three fields a child uses to name its parent row.
CHILD_FIELDS = ("parent", "milestone", "item")


def child_index(pages: dict) -> dict:
    """The three lookups the status table needs, from one pass over the graph.

    A table row reads the children of a page, the states below it, and
    whether anything below it drifted. Each answer is a scan of every page,
    and `plan` writes a table for every page, so building them per page is
    one pass of the graph for each page. Built one time, as
    links.incoming_index is, each lookup is a dictionary hit.
    """
    by_type, by_field, drifted_parents = {}, {f: {} for f in CHILD_FIELDS}, set()
    for path, (_bundle, frontmatter) in pages.items():
        by_type.setdefault(frontmatter.get("type"), []).append(path)
        for field in CHILD_FIELDS:
            target = frontmatter.get(field)
            # A list never equals the target string, so only a plain string
            # names a row. This is the test the three scans used.
            if isinstance(target, str):
                by_field[field].setdefault(target, []).append(path)
        if frontmatter.get("drifted") and isinstance(
                frontmatter.get("parent"), str):
            drifted_parents.add(frontmatter["parent"])
    return {"by_type": by_type, "by_field": by_field,
            "drifted_parents": drifted_parents}


def _children(path: Path, bundle_root: Path, pages: dict,
              index: dict) -> list[Path]:
    """The Project holds the whole roadmap, so it shows every milestone and
    every epic. Every other page uses parent, milestone, or item."""
    own = relative_target(path, bundle_root)
    type_name = pages[path][1]["type"]
    wanted = SHOWS[type_name]
    if type_name == "Project":
        found = {other for name in wanted
                 for other in index["by_type"].get(name, [])}
    else:
        found = {other for field in CHILD_FIELDS
                 for other in index["by_field"][field].get(own, [])
                 if pages[other][1].get("type") in wanted}
    return sorted(found - {path})


def _progress(path: Path, bundle_root: Path, pages: dict, index: dict) -> str:
    own = relative_target(path, bundle_root)
    # A milestone gathers its items through `milestone`, never through
    # `parent`. Counting `parent` alone shows `-` on every milestone row.
    field = "milestone" if pages[path][1].get("type") == "Milestone" else "parent"
    states = [pages[other][1].get("state")
              for other in index["by_field"][field].get(own, [])]
    counted = [s for s in states if s != "cancelled"]
    if not counted:
        return DASH
    done = sum(1 for s in counted if s in DELIVERED_STATES)
    return f"{done}/{len(counted)} ({done * 100 // len(counted)}%)"


def _drift(path: Path, bundle_root: Path, pages: dict, index: dict) -> str:
    """A drifted Story or Task also marks its parent. The stored `drifted`
    field of the parent does not change."""
    if pages[path][1].get("drifted"):
        return "yes"
    if relative_target(path, bundle_root) in index["drifted_parents"]:
        return "yes"
    return DASH


def _cell(value) -> str:
    if not value:
        return DASH
    if isinstance(value, list):
        return ", ".join(Path(str(v)).stem for v in value)
    return str(value)


def block_for(path: Path, bundle_root: Path, pages: dict,
              index: dict | None = None) -> str | None:
    """`index` is the child_index of the same pages. A caller that writes
    more than one page builds it one time and passes it here."""
    frontmatter = pages[path][1]
    if frontmatter.get("type") not in SHOWS:
        return None
    if index is None:
        index = child_index(pages)
    rows = []
    for child in _children(path, bundle_root, pages, index):
        child_fm = pages[child][1]
        state = DASH if child_fm.get("type") == "Milestone" else \
            _cell(child_fm.get("state"))
        rows.append("| [{id}: {title}]({link}) | {state} | {progress} | "
                    "{owner} | {blocked} | {drift} |".format(
                        id=child.stem, title=child_fm.get("title", child.stem),
                        link=relative_link(path, child), state=state,
                        progress=_progress(child, bundle_root, pages,
                                           index),
                        owner=_cell(child_fm.get("owner")),
                        blocked=_cell(child_fm.get("blocked_by")),
                        drift=_drift(child, bundle_root, pages, index)))
    if not rows:
        return None
    return "\n".join([START, "", "## Status", ""] + HEADER + rows + [END])


def replace_block(body: str, block: str | None) -> str:
    """Anything after the old block (the LINKS block) is kept. `join_parts`
    owns the one-blank-line rule that keeps a second regen byte-identical."""
    head, marker, tail = body.partition(START)
    if marker:
        rest = tail.partition(END)[2].strip("\n")
    else:
        # The page has no STATUS block yet. It may already carry a LINKS
        # block, and the STATUS block always comes first, so cut the body
        # before the LINKS marker and keep that block as the tail. Appending
        # after it instead puts the new table where links.replace_block
        # discards it, and the page never gains a status table.
        head, links_marker, links_tail = body.partition(LINKS_START)
        rest = (links_marker + links_tail).strip("\n")
    return join_parts(head, block, rest)
