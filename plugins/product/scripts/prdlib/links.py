"""The generated LINKS block.

A relationship is stored one time, on the page of the later lens, and it
points to the earlier lens. This module writes both directions into the body:
the stored one with the field name, and the derived one with the label below.
A body link is relative to its own file, because GitHub and an editor do not
resolve a link that starts with `/` from the bundle root.
"""
import os
from pathlib import Path

from .graph import FIELD_TARGETS, MAPPING_FIELDS, entries_of, target_path

START = "<!-- LINKS:START (generated, do not edit) -->"
END = "<!-- LINKS:END -->"

# The inverse of `serves` reads as "served by" on the persona page.
INVERSE_LABEL = {
    "serves": "served by", "addresses": "addressed by",
    "depends_on": "depended on by", "includes": "included by",
    "measures": "measured by", "guards": "guarded by",
    "threatens": "threatened by", "constrains": "constrained by",
    "about": "subject of", "supersedes": "superseded by",
    "parent": "child", "blocked_by": "blocks", "milestone": "item of",
    "discovered_from": "discovered", "item": "criterion or run of",
    "traces": "traced by", "describes": "described by",
}


def forward_label(field: str) -> str:
    return field.replace("_", " ")


def relative_link(source: Path, target: Path) -> str:
    return os.path.relpath(target, source.parent)


def priority_suffix(field: str, item) -> str:
    """The priority of one stored entry, on both the forward line and the
    derived line. The spec puts `(must)` on the derived line too."""
    if field in MAPPING_FIELDS and isinstance(item, dict):
        priority = item.get("priority")
        if priority:
            return f" ({priority})"
    return ""


def _line(label: str, target: Path, frontmatter: dict, source: Path,
          suffix: str = "") -> str:
    title = frontmatter.get("title", target.stem)
    link = relative_link(source, target)
    return f"- {label}: [{target.stem}: {title}]({link}){suffix}"


def incoming_index(pages: dict, root: Path) -> dict:
    """Every stored edge, keyed by the page it points at: target path ->
    [(source page, field, stored entry)].

    A derived line is the inverse of an edge stored on another page, so
    finding it means reading every edge of every page. Built one time for the
    whole run, the cost is one pass over the graph. Built inside `block_for`,
    it is one pass for each page.
    """
    out = {}
    for other in sorted(pages):
        other_bundle, other_fm = pages[other]
        for field in FIELD_TARGETS:
            for target, item in entries_of(other_fm, field):
                out.setdefault(target_path(root, other_bundle, target),
                               []).append((other, field, item))
    return out


def block_for(source: Path, pages: dict, root: Path,
              incoming: dict | None = None) -> str | None:
    """The LINKS block of one page, or None when the page has no link.

    pages maps an absolute path to (bundle, frontmatter). `incoming` is the
    incoming_index of the same pages; a caller that writes more than one page
    builds it one time and passes it here.
    """
    bundle, frontmatter = pages[source]
    lines = []
    for field in FIELD_TARGETS:
        for target, item in entries_of(frontmatter, field):
            resolved = target_path(root, bundle, target)
            if resolved not in pages:
                continue
            lines.append(_line(forward_label(field), resolved,
                               pages[resolved][1], source,
                               priority_suffix(field, item)))

    if incoming is None:
        incoming = incoming_index(pages, root)
    for other, field, item in incoming.get(source, ()):
        if other == source:
            continue
        # The derived line carries the same priority.
        lines.append(_line(INVERSE_LABEL[field], other, pages[other][1],
                           source, priority_suffix(field, item)))

    if not lines:
        return None
    return "\n".join([START, "", "## Links", ""] + lines + [END])


def join_parts(head: str, block: str | None, rest: str) -> str:
    """One blank line between parts, every time: a second regen must give the
    same bytes. The one owner of that rule; `status` writes its block with it
    as well, so the two generated regions cannot drift apart."""
    parts = [head.rstrip("\n")]
    if block:
        parts.append(block)
    if rest:
        parts.append(rest)
    return "\n\n".join(part for part in parts if part) + "\n"


def replace_block(body: str, block: str | None) -> str:
    """The old block is replaced where it stands, and the text after it is
    kept: regen never deletes prose a person wrote below the block, and rule
    E10 compares the block only, so a silent delete has no guard."""
    head, marker, tail = body.partition(START)
    rest = tail.partition(END)[2].strip("\n") if marker else ""
    return join_parts(head, block, rest)
