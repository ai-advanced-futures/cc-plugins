"""The generated LINKS block at the end of each page body.

Each edge is stored one time, on one page. The block of that page shows it
with the field name. The block of the target page shows the derived reverse
edge with the `inverse_label` of the schema. A body link is relative to its
own file, because GitHub and an editor do not resolve a `/` link.
"""
import os

from .bundle import Bundle, sort_key, stored_edges
from .schema import edges

START = "<!-- LINKS:START (generated, do not edit) -->"
END = "<!-- LINKS:END -->"


def incoming(bundle: Bundle) -> dict:
    """Target path -> [(field, source path)] for each stored edge. Built one
    time for each run, not one time for each page."""
    out = {}
    for path, page in bundle.pages.items():
        for field_name, _target_id, target in stored_edges(bundle, page):
            out.setdefault(target, []).append((field_name, path))
    return out


def _link(bundle: Bundle, source, target) -> str:
    other = bundle.pages[target]
    relative = os.path.relpath(target, source.parent).replace(os.sep, "/")
    return f"[{other.id}: {other.title}]({relative})"


def block_for(bundle: Bundle, path, incoming_edges: dict):
    """The LINKS block of one page, or None when the page has no edge."""
    page = bundle.pages[path]
    lines = []
    for field_name, target_id, target in stored_edges(bundle, page):
        label = field_name.replace("_", " ")
        if target in bundle.pages:
            lines.append(f"- {label}: {_link(bundle, path, target)}")
        else:
            # An edge to a missing page is plain text. Rule E4 reports it.
            lines.append(f"- {label}: {target_id} (missing)")
    order = list(edges())
    derived = sorted(incoming_edges.get(path, []),
                     key=lambda e: (order.index(e[0]), sort_key(e[1].stem)))
    for field_name, source in derived:
        if source == path:
            continue
        label = edges()[field_name]["inverse_label"]
        lines.append(f"- {label}: {_link(bundle, path, source)}")
    if not lines:
        return None
    return "\n".join([START, "", "## Links", ""] + lines + [END])


def marked_span(text: str, start: str, end: str):
    """(start offset, end offset) of the marked block, or None."""
    at = text.find(start)
    stop = text.find(end, at) if at != -1 else -1
    return None if stop == -1 else (at, stop + len(end))


def replace_marked(body: str, start: str, end: str, block):
    """The body with the marked block replaced where it stands, or added at
    the end. One blank line goes between the parts, every time, so a second
    run gives the same bytes. A body with no block and no new block is
    returned as it is."""
    span = marked_span(body, start, end)
    if span is None:
        if block is None:
            return body
        before, after = body, ""
    else:
        before, after = body[:span[0]], body[span[1]:]
    parts = [before.rstrip("\n"), block or "", after.strip("\n")]
    joined = "\n\n".join(part for part in parts if part)
    return joined + "\n" if joined else ""


def page_text(bundle: Bundle, path, incoming_edges: dict) -> str:
    """The full text that regen gives one page: the head byte for byte, then
    the body with the new block."""
    page = bundle.pages[path]
    block = block_for(bundle, path, incoming_edges)
    return page.head + replace_marked(page.body, START, END, block)
