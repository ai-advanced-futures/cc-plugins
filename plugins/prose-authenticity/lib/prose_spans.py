"""Prose spans shared by every checker in this plugin.

Two checkers need the same thing: the prose lines of a document, with code and
exempt zones removed and line numbers true to the raw file. It lives here
rather than in whichever consumer happened to define it first. See ADR-010.
"""
import re
from pathlib import Path

import zone_parser

FENCE_RE = re.compile(r"^\s{0,3}(```|~~~)")
BLOCKQUOTE_RE = re.compile(r"^\s{0,3}>")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


class ProseLine(str):
    """Extracted prose text that remembers the block marker it lost.

    Extraction strips list bullets and heading hashes, which leaves a list item
    and a heading indistinguishable from a wrapped continuation of the line
    above. `paragraphs` needs that distinction to keep a list item from merging
    with its neighbours and a heading from merging with the body text below it.

    A `str` subclass, so every consumer that joins, strips, or regexes the text
    keeps working unchanged. Only `paragraphs` reads the two flags.
    """

    def __new__(cls, text, starts_block=False, is_heading=False):
        obj = super().__new__(cls, text)
        obj.starts_block = starts_block
        obj.is_heading = is_heading
        return obj


HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+")
BULLET_RE = re.compile(r"^\s*[-*+]\s+")
ORDERED_RE = re.compile(r"^\s*\d+\.\s+")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")

FRONTMATTER_RE = re.compile(r"^-{3,}\s*$")


def _frontmatter_line_numbers(raw_lines):
    """1-based line numbers of a leading YAML frontmatter block, delimiters
    included. Empty when the file does not open with one.

    Detection is by delimiter, not by parsing: 6 of the 693 files in this
    repository that open with `---` hold a block that is not a YAML mapping,
    and all 693 have a closing delimiter. An unterminated opener returns the
    empty set rather than running to EOF — the conservative direction, since
    the alternative blanks a whole document and reports it clean.
    """
    if not raw_lines or not FRONTMATTER_RE.match(raw_lines[0]):
        return set()
    for idx, raw in enumerate(raw_lines[1:], start=2):
        if FRONTMATTER_RE.match(raw):
            return set(range(1, idx + 1))
    return set()


def _exempt_line_numbers(zones):
    """1-based line numbers covered by an author="human" zone."""
    exempt = set()
    for z in zones:
        if z["author"] == "human":
            exempt.update(range(z["start_line"], z["end_line"] + 1))
    return exempt


def checked_spans(doc_path, meta=None):
    """Return (prose_lines, exempt_zone_count).

    prose_lines is [(lineno, text)] over the whole file, 1-based, with every
    non-prose line blanked to "" so line numbers stay true to the raw file.

    Zones are parsed from the path first, because zone markers are HTML
    comments and extraction removes HTML comments. Prose outside every
    declared zone in a partially-marked document is checked: zone_parser
    synthesizes a whole-document zone only when a file has no markers at all,
    so the gap spans are ours to cover.

    `meta`, when given a dict, receives `truncated_scan`: True when a code
    fence opened and never closed, so every line from the opener to EOF was
    blanked and never checked — a document like that can return a clean PASS
    that is indistinguishable from a genuinely clean one. The return shape
    here is pinned to the (prose_lines, exempt_zone_count) 2-tuple, so this
    flag threads out through the optional out-parameter instead.
    """
    zones = zone_parser.parse_zones(doc_path)
    exempt_lines = _exempt_line_numbers(zones)
    exempt_count = sum(1 for z in zones if z["author"] == "human")

    src = Path(doc_path).read_bytes().decode("utf-8")
    raw_lines = src.splitlines()
    frontmatter_lines = _frontmatter_line_numbers(raw_lines)

    out = []
    fence_marker = None
    for idx, raw in enumerate(raw_lines, start=1):
        opener = FENCE_RE.match(raw)
        if opener:
            # A fence closes only on the marker that opened it. Toggling on
            # either marker left `~~~` blocks that hold a ``` line open at EOF,
            # which blanked the rest of the document and never checked it.
            marker = opener.group(1)[0]
            if fence_marker is None:
                fence_marker = marker
            elif marker == fence_marker:
                fence_marker = None
            out.append((idx, ""))
            continue
        if (fence_marker or idx in exempt_lines or idx in frontmatter_lines
                or BLOCKQUOTE_RE.match(raw)):
            out.append((idx, ""))
            continue
        text = HTML_COMMENT_RE.sub(" ", raw)
        text = INLINE_CODE_RE.sub(" ", text)
        is_heading = bool(HEADING_RE.match(text))
        is_item = bool(BULLET_RE.match(text) or ORDERED_RE.match(text))
        text = HEADING_RE.sub("", text)
        text = BULLET_RE.sub("", text)
        text = ORDERED_RE.sub("", text)
        text = BOLD_RE.sub(r"\1", text)
        text = LINK_RE.sub(r"\1", text)
        if text.strip().startswith("|") or set(text.strip()) <= {"-", "|", ":", " "}:
            text = ""
        out.append((idx, ProseLine(text.rstrip(),
                                   starts_block=is_heading or is_item,
                                   is_heading=is_heading)))
    if meta is not None:
        meta["truncated_scan"] = fence_marker is not None
    return out, exempt_count
