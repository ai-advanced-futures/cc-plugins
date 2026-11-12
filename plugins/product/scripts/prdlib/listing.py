"""`prd.py list`: one line for each page, from the frontmatter only.

A skill asks a whole-graph question here instead of reading every file of a
directory.
"""
from pathlib import Path

from . import DataError, UsageError
from .page import load_page
from .registry import TYPES
from .textsafe import escape_controls
from .tree import bundle_dir

MISSING = "-"


def _cell(value) -> str:
    if value is None:
        return MISSING
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ",".join(str(v) for v in value) or MISSING
    return str(value)


def _filters(where: list[str] | None) -> list[tuple[str, str]]:
    """(key, value) for each --where option.

    A value with no `=` filters on the empty string, which no page carries,
    so the run prints nothing and exits 0. A skill reads that as an answer.
    It is a usage mistake, so it exits 2 with the correct form.
    """
    out = []
    for item in where or []:
        key, sign, value = item.partition("=")
        if not sign or not key:
            raise UsageError(
                f"--where {escape_controls(item)} has no `=`. Use --where KEY=VALUE, "
                f"such as --where state=ready.")
        out.append((key, value))
    return out


def rows(root: Path, type_name: str, where: list[str] | None = None,
         fields: str = "title") -> list[str]:
    if type_name not in TYPES:
        raise DataError(f"{escape_controls(type_name)} is not a page type")
    spec = TYPES[type_name]
    if spec.directory is None:
        raise DataError(f"a {type_name} page is not in a directory")
    directory = bundle_dir(root, spec.bundle) / spec.directory
    names = [f.strip() for f in fields.split(",") if f.strip()]
    filters = _filters(where)

    out = []
    for path in sorted(directory.glob("*.md")) if directory.is_dir() else []:
        if path.name in ("index.md", "closed.md"):
            continue
        frontmatter = load_page(path).frontmatter
        if frontmatter.get("type") != type_name:
            continue
        if any(_cell(frontmatter.get(key)) != value for key, value in filters):
            continue
        out.append("\t".join(
            [escape_controls(path.stem)]
            + [escape_controls(_cell(frontmatter.get(n))) for n in names]))
    return out
