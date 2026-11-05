"""`ddd.py new`: assign the next ID and write one page."""
from pathlib import Path

import yaml

from . import DataError, UsageError
from . import logbook, regen
from .bundle import read
from .ids import next_id, require_type
from .page import dump, normalise, write_text
from .schema import plugin_actor, validate_frontmatter


def _sets(pairs) -> dict:
    """`key=value` pairs. The value is YAML, so a list is `[a, b]`."""
    out = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep or not key.strip():
            raise UsageError(f"--set needs KEY=VALUE, got {pair!r}")
        try:
            out[key.strip()] = yaml.safe_load(value)
        except yaml.YAMLError as error:
            raise UsageError(f"--set {key}: the value does not parse: {error}")
    return out


def create(root: Path, type_name: str, title: str, description: str,
           status: str = "draft", sets=()) -> Path:
    spec = require_type(type_name)
    bundle = read(root)
    page_id = next_id(bundle, type_name)
    frontmatter = {"type": type_name, "title": title,
                   "description": description, "status": status}
    frontmatter.update(_sets(sets))
    frontmatter["generated"] = {"by": plugin_actor(),
                                "at": logbook.timestamp(logbook.now())}
    errors = validate_frontmatter(type_name, normalise(frontmatter))
    if errors:
        raise DataError("the page is not valid, so new writes nothing: "
                        + "; ".join(message for _field, message in errors))
    body = f"# {page_id}: {title}\n\n{description}\n"
    if type_name == "Aggregate":
        # Rule W3 warns until the section has one item.
        body += "\n## Invariants\n"
    path = bundle.dir / spec["directory"] / f"{page_id}.md"
    write_text(path, dump(frontmatter, body))
    regen.write(root)
    return path
