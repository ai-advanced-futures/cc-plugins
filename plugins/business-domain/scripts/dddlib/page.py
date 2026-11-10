"""One page: the raw frontmatter text, the frontmatter mapping, and the body.

`head` is the text from the first `---` to the end of the closing `---`
line, byte for byte. regen writes `head` back as it is, so a hand edit to
the frontmatter never changes when the generated parts are rewritten.
"""
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import yaml

from . import DataError
from .schema import types

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)


@dataclass
class Page:
    path: Path
    frontmatter: dict
    head: str
    body: str

    @property
    def id(self) -> str:
        """The file name is the ID."""
        return self.path.stem

    @property
    def type(self) -> str:
        return self.frontmatter["type"]

    @property
    def title(self) -> str:
        return str(self.frontmatter.get("title") or self.id)

    @property
    def status(self) -> str:
        return str(self.frontmatter.get("status") or "")

    @property
    def live(self) -> bool:
        return self.status != "deprecated"

    @property
    def text(self) -> str:
        return self.head + self.body


def read_text(path: Path) -> str:
    """The file as it is on disk, line endings included."""
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


class _TextTimeLoader(yaml.SafeLoader):
    """A SafeLoader that reads a date or a time as the text that the person gave (STORY-276, as STORY-186).

    Each field of the ddd schema is a string, so a value such as 2026-11-09T19:00:00Z
    stays that text, at each depth of a list or a map."""


_TextTimeLoader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_set_value(text):
    """The value of one `set` or `new --set` item, read as YAML with a date or a time kept as text."""
    return yaml.load(text, Loader=_TextTimeLoader)


def normalise(value):
    """YAML reads `2026-10-20` as a date and an unquoted time as a datetime.
    Each field of the schema is a string, so give the ISO form back."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [normalise(v) for v in value]
    if isinstance(value, dict):
        return {k: normalise(v) for k, v in value.items()}
    return value


def parse_text(path: Path, text: str) -> Page:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise DataError("the file has no frontmatter block")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        raise DataError(f"the frontmatter does not parse: {error}")
    if not isinstance(data, dict):
        raise DataError("the frontmatter is not a mapping")
    if not isinstance(data.get("type"), str) or not data["type"].strip():
        raise DataError("the frontmatter has no `type`")
    return Page(path=path, frontmatter=normalise(data),
                head=text[:match.end()], body=text[match.end():])


def parse(path: Path) -> Page:
    return parse_text(path, read_text(path))


def order_keys(frontmatter: dict) -> dict:
    """The keys of the type in schema order. An unknown key goes last,
    sorted, so rule E2 reports it and the writer does not lose it."""
    spec = types().get(frontmatter.get("type"), {})
    order = spec.get("key_order", [])
    known = [k for k in order if k in frontmatter]
    rest = sorted(k for k in frontmatter if k not in order)
    return {k: frontmatter[k] for k in known + rest}


def dump(frontmatter: dict, body: str) -> str:
    """The text of a page from its values. The frontmatter has no comments,
    so this keeps each value but not the original quoting."""
    text = yaml.safe_dump(order_keys(frontmatter), sort_keys=False,
                          allow_unicode=True, default_flow_style=False)
    body = body.lstrip("\n")
    if not body.endswith("\n"):
        body += "\n"
    return f"---\n{text.rstrip()}\n---\n\n{body}"


def line_of(page: Page, field: str) -> int:
    """The line of `field:` in the frontmatter, or 1."""
    for number, line in enumerate(page.head.splitlines(), start=1):
        if line.startswith(f"{field}:"):
            return number
    return 1
