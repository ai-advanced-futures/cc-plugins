"""IDs: the next free ID of a type, and an ID or alias to a path."""
from pathlib import Path

import yaml

from . import DataError, UsageError
from .bundle import ID_RE, Bundle, names
from .schema import type_of_prefix, types


def next_id(bundle: Bundle, type_name: str) -> str:
    """One more than the highest number in use. A deprecated page keeps its
    file, so its number is never given again. A removed page retires its
    number in `manifest.md`, so that number is never given again either."""
    spec = types()[type_name]
    directory = bundle.dir / spec["directory"]
    numbers = [0]
    if directory.is_dir():
        for path in directory.glob(f"{spec['prefix']}-*.md"):
            match = ID_RE.match(path.stem)
            if match and match.group(1) == spec["prefix"]:
                numbers.append(int(match.group(2)))
    manifest = bundle.dir / "manifest.md"
    if manifest.is_file():
        retired = yaml.safe_load(manifest.read_text("utf-8").split("---\n")[1]).get("retired_ids") or []
        for name in retired:
            match = ID_RE.match(str(name))
            if match and match.group(1) == spec["prefix"]:
                numbers.append(int(match.group(2)))
    return f"{spec['prefix']}-{max(numbers) + 1:02d}"


def _fold(text) -> str:
    return " ".join(str(text).split()).casefold()


def resolve(bundle: Bundle, key: str) -> Path:
    """The path of the page with the ID `key`, or of the one page that has
    `key` in `aliases`. Letter case does not matter for an alias."""
    match = ID_RE.match(key)
    if match:
        type_name = type_of_prefix(match.group(1))
        if type_name is not None:
            path = bundle.dir / types()[type_name]["directory"] / f"{key}.md"
            if path.is_file():
                return path
    found = [path for path, page in bundle.pages.items()
             if _fold(key) in {_fold(a) for a in names(page.frontmatter.get("aliases"))}]
    if len(found) == 1:
        return found[0]
    if not found:
        raise DataError(f"no page has the ID or the alias {key!r}")
    pages = ", ".join(path.stem for path in found)
    raise DataError(f"the alias {key!r} names more than one page: {pages}")


def require_type(type_name: str) -> dict:
    if type_name not in types():
        raise UsageError(f"unknown page type {type_name!r}. Use one of: "
                         f"{', '.join(types())}")
    return types()[type_name]
