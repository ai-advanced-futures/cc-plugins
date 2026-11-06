"""The case document, business-case.md: its sections, its paragraphs, and replacing one section.

Each section starts with a `## ` heading followed by a marker line:
    <!-- section: <key> lens: <lens> -->
A section's body is the lines after its marker, up to the next `## ` heading or the end.
"""
from __future__ import annotations

import hashlib
import re

SECTION_MARKER = re.compile(r"^<!-- section: (?P<key>[a-z-]+) lens: (?P<lens>[a-z-]+) -->$")

_BLANK_LINE = re.compile(r"\n[ \t]*\n")
_COMMENTS_ONLY = re.compile(r"(?:<!--.*?-->\s*)+", re.S)
_COMMENT = re.compile(r"<!--.*?-->", re.S)


class CaseDocError(ValueError):
    """The case document, a section key or a new section body is not valid."""


def _is_heading(line: str) -> bool:
    return line.startswith("## ")


def _marker(line: str):
    return SECTION_MARKER.match(line.rstrip("\r\n"))


def _spans(lines: list) -> dict:
    """Section key -> (first body line index, end index), over lines kept with their endings."""
    out, key, start = {}, None, 0
    for n, line in enumerate(lines):
        m = _marker(line)
        if m or _is_heading(line):
            if key is not None:
                out[key] = (start, n)
            key, start = (m.group("key") if m else None), n + 1
            if key is not None and key in out:
                raise CaseDocError(f"section {key} appears twice")
    if key is not None:
        out[key] = (start, len(lines))
    return out


def parse_sections(text: str) -> dict:
    """Section key -> body text."""
    lines = text.splitlines(keepends=True)
    return {key: "".join(lines[a:b]) for key, (a, b) in _spans(lines).items()}


def headings(text: str) -> dict:
    """Section key -> the `## ` heading above its marker, as the person reads it."""
    out, heading = {}, None
    for line in text.splitlines():
        m = _marker(line)
        if m and heading is not None:
            out[m.group("key")] = heading
        heading = line[3:].strip() if _is_heading(line) else None
    return out


def paragraphs(body: str) -> list:
    """The paragraphs of a section body: split on blank lines, with empty and comment-only ones dropped."""
    out = []
    for part in _BLANK_LINE.split(body.replace("\r\n", "\n")):
        part = part.strip()
        if part and not _COMMENTS_ONLY.fullmatch(part):
            out.append(part)
    return out


def normalize(p: str) -> str:
    """Whitespace runs collapsed to one space, ends stripped."""
    return " ".join(p.split())


def paragraph_anchor(section: str, p: str) -> str:
    """A stable anchor for a paragraph: the section key and a hash of its normalized text."""
    return f"{section}:" + hashlib.sha256(normalize(p).encode("utf-8")).hexdigest()[:16]


def _check_comments(key: str, body: str) -> None:
    """Refuse a comment that would change how `paragraphs` counts: one never closed, or one that
    spans a blank line. A bare `-->` opens nothing, so prose may use it as an arrow."""
    for comment in _COMMENT.findall(body):
        if _BLANK_LINE.search(comment.replace("\r\n", "\n")):
            raise CaseDocError(f"the new body of section {key} holds a comment that spans a blank line")
    if "<!--" in _COMMENT.sub("", body):
        raise CaseDocError(f"the new body of section {key} holds a comment that is not closed")


def replace_section(text: str, key: str, body: str) -> str:
    """The text with one section's body replaced. Every other byte is kept.
    The body may not hold a `## ` heading or a section marker, so the section count cannot change."""
    _check_comments(key, body)
    for line in body.splitlines():
        if _is_heading(line):
            raise CaseDocError(f"the new body of section {key} holds a `## ` heading: {line!r}")
        if _marker(line):
            raise CaseDocError(f"the new body of section {key} holds a section marker: {line!r}")
    lines = text.splitlines(keepends=True)
    spans = _spans(lines)
    if key not in spans:
        raise CaseDocError(f"the case has no section {key}; its sections are {sorted(spans)}")
    start, end = spans[key]
    if body.strip() == "":
        region = "\n"
    else:
        region = body if body.endswith("\n") else body + "\n"
        if end < len(lines) and not region.endswith("\n\n"):
            region += "\n"  # one blank line before the next heading
    if start == len(lines) and not lines[-1].endswith("\n"):
        lines[-1] += "\n"  # the marker is the last line and has no line ending
    return "".join(lines[:start]) + region + "".join(lines[end:])
