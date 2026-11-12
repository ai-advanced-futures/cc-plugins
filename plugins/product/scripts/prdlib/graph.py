"""The rules that the JSON Schema cannot hold.

LinkML outputs lose structure: a JSON Schema can say that `parent` is a string
with a path shape, but not that the target exists, that its type is permitted,
that its level is higher, or that the edges make no cycle. Those rules live
here. Each function names the schema slot it covers.
"""
import re
from pathlib import Path

from . import DataError
from .registry import PRD_TYPES, TYPES, WORK_ITEMS
from .textsafe import escape_controls
from .tree import bundle_dir

CROSS_BUNDLE_PREFIX = "prd:"

# slot -> the page types the target may have.
FIELD_TARGETS = {
    "serves": ("Persona",),
    "addresses": ("Need", "Journey", "Persona", "Problem"),
    "describes": ("Capability", "Journey"),
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


def check_targets(root: Path, bundle: str, frontmatter: dict,
                  fields) -> None:
    """The E4 texts of `check`, for the fields that one write names.

    A page that `check` would refuse must not be written at all, so `new`,
    `set` and `link` call this inside the lock, before the first write. It
    reads only the fields it
    is given: a page with a link that broke after a `remove` still takes a
    `set` of another field, and a `set` of the full correct list repairs the
    link. It raises DataError on the first target that does not exist or that
    has a type the field refuses.
    """
    from .page import load_page  # local import: page imports DataError only
    for field in fields:
        permitted = FIELD_TARGETS.get(field)
        if permitted is None:
            continue
        for target in targets_of(frontmatter, field):
            resolved = target_path(root, bundle, target)
            if not resolved.is_file():
                raise DataError(f"`{field}` names {escape_controls(target)}, "
                                "which does not exist")
            target_type = load_page(resolved).type
            if target_type not in permitted:
                raise DataError(f"`{field}` does not accept a "
                                f"{escape_controls(target_type)} target")


# The pattern of RoadmapPath in schema/product.yaml, for `fullmatch`. Never
# use `$` here: it also matches before a final line break.
ROADMAP_PATH_RE = re.compile(r"/[a-z-]+/[A-Z]+-[0-9A-Za-z-]+\.md")


def milestone_difference(milestone, parent: str, parent_milestone):
    """The text of W9, or None. A Story is in the milestone of its parent.

    It is None when the parent has no milestone. It is also None when a value
    that the text would print (the parent, the milestone of the parent, the
    milestone of the Story) is not a RoadmapPath: rule E2 reports that value,
    and the text of W9 and the note of `new` must not print it raw, because a
    line break or an ESC in it would forge a line. Each valid value is a
    RoadmapPath, whose pattern allows one form for each page, so a string
    compare is exact. `check` (rule W9) and `new` (its note) both call this,
    so the 2 texts cannot drift apart.
    """
    if not isinstance(parent_milestone, str) \
            or not ROADMAP_PATH_RE.fullmatch(parent_milestone) \
            or not ROADMAP_PATH_RE.fullmatch(parent):
        return None
    parent_id, wanted = Path(parent).stem, Path(parent_milestone).stem
    if not isinstance(milestone, str) or not milestone:
        return f"the Story has no milestone, and its parent {parent_id} is in {wanted}"
    if not ROADMAP_PATH_RE.fullmatch(milestone):
        return None
    if milestone != parent_milestone:
        return (f"the milestone {Path(milestone).stem} differs from {wanted} "
                f"of the parent {parent_id}")
    return None


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
        raise DataError(f"{escape_controls(path.stem)} is not a roadmap page")


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
