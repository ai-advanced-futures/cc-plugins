"""One page: the frontmatter mapping and the markdown body."""
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import yaml

from . import DataError

try:
    # libyaml reads a frontmatter about 7 times faster. The pure-Python
    # loader is the fallback: pyyaml ships without the C extension on some
    # platforms. Reading is safe to speed up, because both loaders give the
    # same values for the same text.
    from yaml import CSafeLoader as _Loader
except ImportError:  # pragma: no cover - depends on the pyyaml build
    from yaml import SafeLoader as _Loader


def safe_load(text):
    """yaml.safe_load through the fastest loader this pyyaml build has."""
    return yaml.load(text, Loader=_Loader)


class _TextTimeLoader(yaml.SafeLoader):
    """A SafeLoader that reads a date or a time as the text that the person gave (STORY-276, as STORY-186).

    Each date field of the product schema is a string, so a value such as
    2026-11-09T19:00:00Z stays that text, at each depth of a list or a map."""


_TextTimeLoader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_set_value(text):
    """The value of one `set` or `new --set` item, read as YAML with a date or a time kept as text."""
    return yaml.load(text, Loader=_TextTimeLoader)


def safe_dump(data, **kwargs) -> str:
    """The pure-Python dumper, on purpose.

    CSafeDumper is about 4 times faster, but it escapes a character above
    the basic plane: an emoji in a title becomes "\U0001F3AF". regen
    compares its output with the file on disk, so that difference would
    rewrite the page and change text a person wrote. Writing stays exact.
    """
    return yaml.safe_dump(data, **kwargs)

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)

# Spec rule 1: the OKF fields first, then the type fields, then the
# relationships.
OKF_FIELDS = ("type", "title", "description", "status", "tags", "generated",
              "verified", "aliases", "protected", "resource", "sources",
              "usage_window", "stale_after")
TYPE_FIELDS = (
    "created", "updated", "lenses", "primary", "kind", "kano",
    "role", "target", "validation", "decided_at", "alternatives",
    "state", "size", "target_date",
    "planned_start_date", "planned_end_date",
    "actual_start_date", "actual_end_date",
    "github", "claim", "check", "check_declared_by",
    "agent", "started_at", "ended_at", "outcome", "spec", "pull_request",
    "commit", "results",
)
RELATIONSHIP_FIELDS = (
    "serves", "addresses", "depends_on", "includes", "measures", "guards",
    "threatens", "constrains", "about", "supersedes",
    "parent", "blocked_by", "milestone", "owner", "discovered_from", "item",
    "traces", "drifted",
)
KEY_ORDER = OKF_FIELDS + TYPE_FIELDS + RELATIONSHIP_FIELDS


@dataclass
class Page:
    path: Path
    frontmatter: dict
    body: str

    @property
    def type(self) -> str:
        return self.frontmatter.get("type", "")

    @property
    def id(self) -> str:
        """The file name is the ID. product.md and closed.md have none."""
        return self.path.stem


def split_frontmatter(text: str):
    """Return (frontmatter text or None, body)."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, text
    return match.group(1), text[match.end():]


def normalise(value):
    """YAML reads `2026-12-01` as a date object and `2026-01-01T00:30:00Z` as
    a datetime. Every field of this schema is a string, so give the ISO form
    back. Each reader of a page calls this, so a hand-written page with an
    unquoted date is not a rule E2 error."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [normalise(v) for v in value]
    if isinstance(value, dict):
        return {k: normalise(v) for k, v in value.items()}
    return value


def load_page(path: Path) -> Page:
    fm_text, body = split_frontmatter(path.read_text(encoding="utf-8"))
    if fm_text is None:
        raise DataError(f"{path}: the page has no frontmatter")
    try:
        data = safe_load(fm_text)
    except yaml.YAMLError as error:
        raise DataError(f"{path}: the frontmatter does not parse: {error}")
    if not isinstance(data, dict):
        raise DataError(f"{path}: the frontmatter is not a mapping")
    return Page(path=path, frontmatter=normalise(data), body=body)


def order_keys(frontmatter: dict) -> dict:
    """Known keys in schema order. An unknown key goes last, sorted, so the
    checker reports it instead of the writer losing it. Rule E2 is what
    reports it: `gen-schema.sh` runs the generator with `--closed`, so each
    class rejects a key the schema does not declare."""
    known = [k for k in KEY_ORDER if k in frontmatter]
    rest = sorted(k for k in frontmatter if k not in KEY_ORDER)
    return {k: frontmatter[k] for k in known + rest}


def dump_page(page: Page) -> str:
    """Write the page again from its values.

    The limit: the writer builds the frontmatter from the values, so it
    does not keep a comment and it does not keep the original quoting. Each
    value stays the same. The spec forbids a comment in the frontmatter (page
    format rule 1), and a round-trip YAML library is not a permitted
    dependency, so the script states this limit instead of holding the
    original lines.
    """
    text = safe_dump(order_keys(page.frontmatter), sort_keys=False,
                          allow_unicode=True, default_flow_style=False)
    # One blank line between the frontmatter and the body, every time, so a
    # second write of the same page gives the same bytes.
    body = page.body.lstrip("\n")
    if not body.endswith("\n"):
        body += "\n"
    return f"---\n{text.rstrip()}\n---\n\n{body}"


def write_page(page: Page) -> None:
    page.path.parent.mkdir(parents=True, exist_ok=True)
    page.path.write_text(dump_page(page), encoding="utf-8")
