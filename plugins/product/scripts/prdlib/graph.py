"""The rules that the JSON Schema cannot hold.

LinkML outputs lose structure: a JSON Schema can say that `parent` is a string
with a path shape, but not that the target exists, that its type is permitted,
that its level is higher, or that the edges make no cycle. Those rules live
here. Each function names the schema slot it covers.
"""
from pathlib import Path

from . import DataError
from .registry import PRD_TYPES, TYPES, WORK_ITEMS
from .tree import bundle_dir

CROSS_BUNDLE_PREFIX = "prd:"

# slot -> the page types the target may have.
FIELD_TARGETS = {
    "serves": ("Persona",),
    "addresses": ("Need", "Journey", "Persona", "Problem"),
    "depends_on": ("Capability",),
    "includes": ("Capability",),
    "measures": ("Problem", "Need", "Journey", "Capability"),
    "guards": ("Metric",),
    "threatens": PRD_TYPES,
    "constrains": PRD_TYPES,
    "about": PRD_TYPES,
    "supersedes": ("Decision",),
    "parent": WORK_ITEMS,
    "blocked_by": WORK_ITEMS,
    "milestone": ("Milestone",),
    "discovered_from": WORK_ITEMS,
    "item": WORK_ITEMS,
    "traces": PRD_TYPES,
}
MAPPING_FIELDS = {"includes": "to", "traces": "to"}
CYCLE_FIELDS = {"parent": "E5", "blocked_by": "E6", "depends_on": "E6"}


def entries_of(frontmatter: dict, field: str) -> list[tuple[str, object]]:
    """(target, stored entry) pairs of one field. A mapping with no `to` and
    any non-string are dropped, so an index into the raw list reads a
    different entry and attaches the wrong priority. The pair keeps the
    target and its stored entry together."""
    value = frontmatter.get(field)
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    key = MAPPING_FIELDS.get(field)
    out = []
    for item in items:
        if key and isinstance(item, dict):
            if item.get(key):
                out.append((item[key], item))
        elif isinstance(item, str):
            out.append((item, item))
    return out


def targets_of(frontmatter: dict, field: str) -> list[str]:
    """Each stored target of one field, as a bundle-relative path string."""
    return [target for target, _entry in entries_of(frontmatter, field)]


def target_path(root: Path, bundle: str, target: str) -> Path:
    if target.startswith(CROSS_BUNDLE_PREFIX):
        rest = target[len(CROSS_BUNDLE_PREFIX):]
        return bundle_dir(root, "prd") / rest.lstrip("/")
    return bundle_dir(root, bundle) / target.lstrip("/")


def relative_target(path: Path, bundle_root: Path) -> str:
    """The target string of one page, below the root of its own bundle.

    The one encoder of the `/<directory>/<ID>.md` form. `target_path` is the
    decoder. A caller that spells the form itself drops out of step the day
    a directory of `registry._SPECS` is renamed.
    """
    return "/" + str(path.relative_to(bundle_root))


def own_target(root: Path, path: Path) -> str:
    """The bundle-relative target string of one roadmap page."""
    try:
        return relative_target(path, bundle_dir(root, "roadmap"))
    except ValueError:
        raise DataError(f"{path.stem} is not a roadmap page")


def level_of(type_name: str) -> int | None:
    spec = TYPES.get(type_name)
    return spec.level if spec else None


def find_cycle(edges: dict[str, list[str]]) -> list[str] | None:
    """The first cycle of a directed graph, or None. Node keys are paths."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {node: WHITE for node in edges}
    stack: list[str] = []

    def walk(node: str):
        colour[node] = GREY
        stack.append(node)
        for target in edges.get(node, ()):
            if colour.get(target, BLACK) == GREY:
                return stack[stack.index(target):] + [target]
            if colour.get(target, BLACK) == WHITE:
                found = walk(target)
                if found:
                    return found
        stack.pop()
        colour[node] = BLACK
        return None

    for node in list(edges):
        if colour[node] == WHITE:
            found = walk(node)
            if found:
                return found
    return None
