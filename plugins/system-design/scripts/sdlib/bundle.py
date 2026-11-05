"""The bundle: its folder from the registry, and its pages."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from sdlib import UsageError
from sdlib.page import parse

GRAPH = "system-design"
DEFAULT_DIR = "docs/system-design"
REGISTRY = Path(".claude") / "knowledge.json"
ID_RE = re.compile(r"^([A-Z]+)-(\d{2,})$")
AREA_TITLES = {"quality": "Quality scenarios", "context": "Context", "strategy": "Solution strategy",
               "building-blocks": "Building blocks", "data": "Data and ownership", "contracts": "Contracts",
               "conventions": "Crosscutting conventions", "deployment": "Deployment"}


@dataclass
class Bundle:
    root: Path
    dir: Path
    pages: dict = field(default_factory=dict)


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


def bundle_dir(root) -> Path:
    entry = read_registry(root).get(GRAPH)
    if not entry:
        raise UsageError(f"the system-design graph is not in {REGISTRY}. Run /system-design:setup first.")
    directory = Path(root) / entry["path"]
    if not directory.is_dir():
        raise UsageError(f"the folder {entry['path']} does not exist. Run /system-design:setup first.")
    return directory


def page_files(directory) -> list[Path]:
    directory = Path(directory)
    out = []
    for path in directory.rglob("*.md"):
        rel = path.relative_to(directory)
        if path.name == "index.md" or any(part.startswith(".") for part in rel.parts):
            continue
        if len(rel.parts) == 1 and path.name in ("log.md", "manifest.md"):
            continue
        out.append(path)
    return sorted(out)


def read(root, directory=None) -> Bundle:
    directory = Path(directory) if directory else bundle_dir(root)
    return Bundle(Path(root), directory, {path: parse(path) for path in page_files(directory)})


def ref(directory, path) -> str:
    return "/" + Path(path).relative_to(Path(directory)).as_posix()
