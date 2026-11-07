"""The bundle: its folder from the registry, and its pages."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from jtbdlib import DataError, UsageError
from jtbdlib.page import parse

GRAPH = "jtbd"
DEFAULT_DIR = "docs/jtbd"
REGISTRY = Path(".claude") / "knowledge.json"
ID_RE = re.compile(r"^([A-Z]+)-(\d{2,})$")


@dataclass
class Bundle:
    root: Path
    dir: Path
    pages: dict = field(default_factory=dict)
    unreadable: list = field(default_factory=list)  # (folder, reason) for each folder that cannot be listed


def shown(root, path) -> str:
    try:
        return Path(path).relative_to(root).as_posix()
    except ValueError:
        return str(path)


def read_registry(root) -> dict:
    file = Path(root) / REGISTRY
    if not file.is_file():
        return {}
    try:
        return json.loads(file.read_text("utf-8")).get("graphs") or {}
    except (OSError, json.JSONDecodeError) as error:
        raise UsageError(f"cannot read {REGISTRY}: {error}") from error


def registry_add(root, name, path) -> bool:
    file = Path(root) / REGISTRY
    data = json.loads(file.read_text("utf-8")) if file.is_file() else {"graphs": {}}
    data.setdefault("graphs", {})
    if data["graphs"].get(name) == {"path": path}:
        return False
    data["graphs"][name] = {"path": path}
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def has_entry(root) -> bool:
    return GRAPH in read_registry(root)


def check_dir(directory) -> str:
    value = str(directory).strip()
    if not value or value.startswith("/") or ".." in Path(value).parts:
        raise UsageError(f"the folder must be relative to the project root and stay inside it: {directory!r}")
    # A skill puts this name in a command, so a shell character must not pass (issue 673).
    if not re.fullmatch(r"[A-Za-z0-9._/-]{1,100}", value):
        raise UsageError(f"the folder name may hold only letters, digits, and the characters . _ / - (at most 100): {directory!r}")
    while value.startswith("./"):
        value = value[2:]
    return value.rstrip("/")


def bundle_dir(root) -> Path:
    entry = read_registry(root).get(GRAPH)
    if not entry:
        raise UsageError(f"the jtbd graph is not in {REGISTRY}. "
                         "Run /jtbd-market-discovery:setup first.")
    directory = Path(root) / check_dir(entry["path"])
    if not directory.is_dir():
        raise UsageError(f"the folder {entry['path']} does not exist. Run /jtbd-market-discovery:setup first.")
    return directory


def page_files(directory, unreadable=None) -> list[Path]:
    """Each page file of the bundle, sorted. When `unreadable` is a list, it gets (folder, reason) for each folder
    that cannot be listed: rglob skips such a folder with no error (STORY-214)."""
    directory = Path(directory)
    out = []

    def note(error):
        if unreadable is not None:
            unreadable.append((Path(error.filename), error.strerror or error.__class__.__name__))

    for folder, folders, files in os.walk(directory, onerror=note):
        folders[:] = [name for name in folders if not name.startswith(".")]
        for name in files:
            path = Path(folder) / name
            rel = path.relative_to(directory)
            if not name.endswith(".md") or name.startswith(".") or name == "index.md":
                continue
            if len(rel.parts) == 1 and name in ("log.md", "manifest.md"):
                continue
            out.append(path)
    return sorted(out)


def read(root, directory=None) -> Bundle:
    directory = Path(directory) if directory else bundle_dir(root)
    unreadable = []
    files = page_files(directory, unreadable)
    return Bundle(Path(root), directory, {path: parse(path) for path in files}, sorted(unreadable))


def read_whole(root) -> Bundle:
    """The bundle for a command that gives an answer from it. Stop on a folder or a page that cannot be read (STORY-214).

    A page that does not parse has no type, so no command can know that it does not need the page.
    """
    bundle = read(root)
    faults = [(folder, f"cannot read the folder: {reason}") for folder, reason in bundle.unreadable]
    faults += [(path, page.error or "the page has no type") for path, page in sorted(bundle.pages.items())
               if page.error or not page.type]
    if faults:
        path, why = faults[0]
        # 1 line with no final period: a reader such as gtm puts the line into its own sentence.
        raise DataError(f"{shown(root, path)}: {why}. The command stops at a page or a folder of the graph that it "
                        f"cannot read ({len(faults)} in all): run jtbd_graph.py check, then fix or remove each one")
    return bundle


def ref(directory, path) -> str:
    return "/" + Path(path).relative_to(Path(directory)).as_posix()
