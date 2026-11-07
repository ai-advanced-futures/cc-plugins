"""One page: frontmatter, head bytes, and body."""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)


@dataclass
class Page:
    path: Path
    frontmatter: dict | None
    head: str
    body: str
    error: str = ""

    @property
    def type(self):
        return (self.frontmatter or {}).get("type")

    @property
    def id(self) -> str:
        return self.path.stem

    @property
    def title(self) -> str:
        return " ".join(str((self.frontmatter or {}).get("title") or self.path.stem).split())

    @property
    def live(self) -> bool:
        return (self.frontmatter or {}).get("status") != "deprecated"


def read_text(path) -> str:
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


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
        return Page(Path(path), None, "", text, "the file has no frontmatter")
    try:
        data = yaml.load(match.group(1), Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
    except yaml.YAMLError as error:
        return Page(Path(path), None, text[: match.end()], text[match.end():],
                    f"the frontmatter does not parse: {error.__class__.__name__}")
    if not isinstance(data, dict):
        return Page(Path(path), None, text[: match.end()], text[match.end():], "the frontmatter is not a mapping")
    return Page(Path(path), normalise(data), text[: match.end()], text[match.end():])


def parse(path) -> Page:
    try:
        text = read_text(path)
    except (OSError, UnicodeDecodeError) as error:
        # A file that cannot be read is a page with an error: check names it, and a reader stops (STORY-214).
        reason = getattr(error, "strerror", None) or error.__class__.__name__
        return Page(Path(path), None, "", "", f"cannot read the file: {reason}")
    return parse_text(path, text)


def ordered(frontmatter: dict, key_order) -> dict:
    first = [k for k in key_order if k in frontmatter]
    rest = sorted(k for k in frontmatter if k not in key_order)
    return {k: frontmatter[k] for k in first + rest}


def dump(frontmatter, body) -> str:
    return "---\n" + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True, width=1000) + "---\n" + body
