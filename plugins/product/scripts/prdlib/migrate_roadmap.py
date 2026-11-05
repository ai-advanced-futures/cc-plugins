"""The v3 roadmap: the status table and the body grammar.

The table holds the status of each milestone and feature. The body holds the
tree, the traces, the criteria, and the estimates. A story takes its state
from its checkbox, and a feature takes its state from the table, because the
table is generated for a feature and a person edits a checkbox for a story.
"""
import re
from dataclasses import dataclass, field

TABLE_START = "<!-- ROADMAP-STATUS-TABLE:START -->"
TABLE_END = "<!-- ROADMAP-STATUS-TABLE:END -->"
MARK = "⚠"
MILESTONE_RE = re.compile(r"^#{2,}\s+(M\d+)\s*:\s*(.+?)\s*$")
CHECKBOX_RE = re.compile(r"^(?P<indent>\s*)- \[(?P<mark>[ xX])\]\s+(?P<text>.*)$")
ITEM_ID_RE = re.compile(r"^(?P<id>[FS]\d+(?:\.\d+)*)\s*:\s*(?P<title>.+?)\s*$")
# The four detail regexes are anchored the same way, so `_detail` uses
# `match` for all of them and a detail line is read wherever it is indented.
TRACE_RE = re.compile(r"^\s*-\s*\*\*Trace\*\*:\s*(?P<body>.+?)\s*$")
TRACE_ENTRY_RE = re.compile(r"([A-Z][A-Z0-9-]*-\d+)\s*@([0-9a-f]+)\s*(⚠)?")
DEPS_RE = re.compile(r"^\s*-\s*\*\*(?:Dependencies|Deps)\*\*:\s*(?P<body>.+?)\s*$")
SIZE_RE = re.compile(r"^\s*-\s*Size:\s*(?P<size>[SML])\b")
TARGET_RE = re.compile(r"^\s*-\s*\*\*Target\*\*:\s*(?P<date>\S+)\s*$")
ACCEPTANCE_RE = re.compile(r"^\s*-\s*Acceptance Criteria:\s*$")
# A dependency cell that holds one of these names no dependency.
NO_DEPS = {"none", "-", "n/a", "na", ""}
STATE_OF_STATUS = {
    "Not Started": "ready",
    "In Progress": "in_progress",
    "Completed": "done",
}


@dataclass
class V3Item:
    id: str
    kind: str                    # milestone, feature, or story
    title: str
    body: str = ""
    parent: str | None = None
    state: str = "ready"
    not_planned: bool = False
    deps: list = field(default_factory=list)
    traces: list = field(default_factory=list)   # (requirement ID, hash)
    marked: set = field(default_factory=set)     # requirement IDs with a mark
    criteria: list = field(default_factory=list)
    size: str | None = None
    target_date: str | None = None   # the `- **Target**: <date>` line


def parse_table(text: str) -> dict:
    """v3 ID -> {status, trace, marked, deps}. An absent table gives {}."""
    if TABLE_START not in text or TABLE_END not in text:
        return {}
    block = text.split(TABLE_START, 1)[1].split(TABLE_END, 1)[0]
    rows = {}
    for line in block.split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 8 or cells[0] in ("#", "---"):
            continue
        item = cells[2]
        if ":" not in item:
            continue
        identifier = item.split(":", 1)[0].strip()
        traces, marked = [], set()
        for entry in cells[7].split(","):
            entry = entry.strip()
            if not entry or entry == "-":
                continue
            name = entry.replace(MARK, "").strip()
            traces.append(name)
            if MARK in entry:
                marked.add(name)
        rows[identifier] = {"status": cells[4], "trace": traces,
                            "marked": marked,
                            "deps": [] if cells[6] == "-" else
                                    [d.strip() for d in cells[6].split(",")]}
    return rows


def parse_roadmap(text: str) -> list:
    """Each milestone, feature, and story of a v3 roadmap, in document order."""
    rows = parse_table(text)
    body = text.split(TABLE_END, 1)[-1]
    items, current = [], {"milestone": None, "feature": None, "story": None}
    in_criteria = False
    for line in body.split("\n"):
        heading = MILESTONE_RE.match(line)
        if heading:
            item = V3Item(id=heading.group(1), kind="milestone",
                          title=heading.group(2))
            item.not_planned = \
                rows.get(item.id, {}).get("status") == "Not Planned"
            items.append(item)
            current = {"milestone": item, "feature": None, "story": None}
            in_criteria = False
            continue
        box = CHECKBOX_RE.match(line)
        if box:
            found = ITEM_ID_RE.match(box.group("text"))
            if found:
                # A checkbox whose text starts with an item ID is an item. Any
                # other checkbox under an Acceptance Criteria line is a
                # criterion of the item above it.
                item = _new_item(found, box, current, rows)
                items.append(item)
                in_criteria = False
                continue
            if in_criteria:
                owner = current["story"] or current["feature"]
                if owner is not None:
                    owner.criteria.append(box.group("text").strip())
                continue
        if ACCEPTANCE_RE.match(line):
            in_criteria = True
            continue
        # A detail line closes the criteria list, so a checkbox that follows
        # the details of the next item is never read as a criterion.
        if _detail(line, current):
            in_criteria = False
    _apply_states(items, rows)
    return items


def _open(current):
    """The item a detail line belongs to: the deepest one that is open."""
    return current["story"] or current["feature"] or current["milestone"]


def _split_deps(body: str) -> list:
    """`None`, `-`, `n/a` and an empty cell all give an empty list."""
    out = []
    for name in body.split(","):
        name = name.strip()
        if name.lower() in NO_DEPS:
            continue
        out.append(name)
    return out


def _new_item(found, box, current, rows) -> V3Item:
    identifier = found.group("id")
    kind = "feature" if identifier.startswith("F") else "story"
    parent = current["feature"] if kind == "story" else current["milestone"]
    item = V3Item(id=identifier, kind=kind, title=found.group("title"),
                  parent=parent.id if parent is not None else None)
    item.state = "done" if box.group("mark").lower() == "x" else "ready"
    if kind == "feature":
        current["feature"], current["story"] = item, None
    else:
        current["story"] = item
    return item


def _detail(line: str, current) -> bool:
    """Write one detail line onto the open item. True when the line was a
    detail, which closes any open criteria list."""
    item = _open(current)
    if item is None:
        return False
    item.body += line + "\n"
    found = TRACE_RE.match(line)
    if found:
        for name, digest, mark in TRACE_ENTRY_RE.findall(found.group("body")):
            item.traces.append((name, digest))
            if mark:
                item.marked.add(name)
        return True
    found = DEPS_RE.match(line)
    if found:
        item.deps = _split_deps(found.group("body"))
        return True
    found = SIZE_RE.match(line)
    if found:
        item.size = found.group("size")
        return True
    found = TARGET_RE.match(line)
    if found:
        item.target_date = found.group("date")
        return True
    return False


def _apply_states(items, rows) -> None:
    for item in items:
        row = rows.get(item.id, {})
        for name in row.get("marked", set()):
            item.marked.add(name)
        # The table `Deps` column is the second source of a dependency, so a
        # milestone whose body has no Dependencies line still gets its deps.
        if not item.deps and row.get("deps"):
            item.deps = _split_deps(", ".join(row["deps"]))
        if item.kind == "milestone":
            continue
        if item.kind == "story":
            if item.state != "done" and "In Progress" in item.body:
                item.state = "in_progress"
            continue
        status = row.get("status")
        if status in STATE_OF_STATUS:
            item.state = STATE_OF_STATUS[status]
        elif item.state != "done" and "In Progress" in item.body:
            item.state = "in_progress"
