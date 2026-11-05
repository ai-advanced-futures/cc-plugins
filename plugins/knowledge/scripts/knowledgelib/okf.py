"""OKF v0.2 pages: read, write, and find links. PyYAML only."""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from knowledgelib import changes

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
LINKS_START = "<!-- LINKS:START (generated, do not edit) -->"
LINKS_END = "<!-- LINKS:END -->"
GRAPH_LINK_RE = re.compile(r"^([a-z][a-z0-9-]*):(/[^/\s]\S*)$")
BODY_GRAPH_RE = re.compile(r"(?<![\w/:.-])([a-z][a-z0-9-]*):(/[A-Za-z0-9._-][A-Za-z0-9._/-]*\.md)")
BODY_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
EXTERNAL_RE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#)")
SKIP_KEYS = ("generated", "verified")


def oneline(value) -> str:
    return " ".join(str(value or "").split())


def label(value) -> str:
    """A title as the label of a markdown link: one line, with \\ [ ] < > and the backtick escaped."""
    return re.sub(r"([\\\[\]<>`])", r"\\\1", oneline(value))


def shown(root, path) -> str:
    try:
        return Path(path).relative_to(root).as_posix()
    except ValueError:
        return str(path)


@dataclass
class Page:
    path: Path
    frontmatter: dict | None
    body: str
    error: str = ""

    @property
    def type(self):
        return (self.frontmatter or {}).get("type")


def read_text(path) -> str:
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    changes.note(path)


def normalise(value):
    if isinstance(value, (_dt.datetime, _dt.date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: normalise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalise(v) for v in value]
    return value


def parse_text(path, text) -> Page:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return Page(Path(path), None, text, "the file has no frontmatter")
    rest = text[match.end():]
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        return Page(Path(path), None, rest, f"the frontmatter does not parse: {error.__class__.__name__}")
    if not isinstance(data, dict):
        return Page(Path(path), None, rest, "the frontmatter is not a mapping")
    return Page(Path(path), normalise(data), rest)


def read_page(path) -> Page:
    return parse_text(path, read_text(path))


def dump(frontmatter, body) -> str:
    head = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True, width=1000)
    return f"---\n{head}---\n{body}"


def strip_links_block(text) -> str:
    start = text.find(LINKS_START)
    if start < 0:
        return text
    end = text.find(LINKS_END, start)
    end = len(text) if end < 0 else end + len(LINKS_END)
    return text[:start] + text[end:].lstrip("\n")


def size_of(text) -> tuple[int, int]:
    rest = strip_links_block(text)
    return len(rest.splitlines()), len(rest.split())


def bundle_pages(bundle) -> list[Path]:
    bundle = Path(bundle)
    found = []
    for path in bundle.rglob("*.md"):
        rel = path.relative_to(bundle)
        if path.name == "index.md" or any(part.startswith(".") for part in rel.parts):
            continue
        if len(rel.parts) == 1 and path.name in ("log.md", "manifest.md"):
            continue
        found.append(path)
    return sorted(found)


def bundle_path(bundle, path) -> str:
    return "/" + Path(path).relative_to(Path(bundle)).as_posix()


def is_link(value: str) -> bool:
    if value.startswith("/") and not value.startswith("//"):
        return ".md" in value
    return bool(GRAPH_LINK_RE.match(value))


def frontmatter_links(data) -> list[tuple[str, str]]:
    found = []

    def walk(field, value):
        if isinstance(value, str):
            if is_link(value.strip()):
                found.append((field, value.strip()))
        elif isinstance(value, list):
            for item in value:
                walk(field, item)
        elif isinstance(value, dict):
            for item in value.values():
                walk(field, item)

    for key, value in (data or {}).items():
        if key not in SKIP_KEYS:
            walk(key, value)
    return found


def body_links(page_file, bundle, body) -> list[str]:
    text = strip_links_block(body)
    root = Path(bundle).resolve()
    found = []
    for match in BODY_LINK_RE.finditer(text):
        raw = match.group(1)
        target = raw.split("#", 1)[0]
        if not target or EXTERNAL_RE.match(raw):
            continue
        if target.startswith("/"):
            link = target
        else:
            try:
                link = "/" + (Path(page_file).parent / target).resolve().relative_to(root).as_posix()
            except ValueError:
                continue
        if link.endswith(".md") and link not in found:
            found.append(link)
    for match in BODY_GRAPH_RE.finditer(text):
        link = f"{match.group(1)}:{match.group(2)}"
        if link not in found:
            found.append(link)
    return found
