"""The bundle: its folder from the registry, and its pages."""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from uxlib import UsageError
from uxlib.page import parse

GRAPH = "ux-hci-design"
DEFAULT_DIR = "docs/ux-hci-design"
REGISTRY = Path(".claude") / "knowledge.json"
ID_RE = re.compile(r"^([A-Z]+)-(\d{2,})$")
# The folder name goes into a shell command and into CLAUDE.md, so it holds no quote, space, `$` or new line (#692).
DIR_RE = re.compile(r"[A-Za-z0-9._/-]{1,100}")


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


def registry_add(root, name, path, git=None) -> bool:
    """Write the entry of the graph. `git` False writes `"git": false`; True writes no key; None keeps the entry's answer."""
    file = Path(root) / REGISTRY
    data = json.loads(file.read_text("utf-8")) if file.is_file() else {"graphs": {}}
    data.setdefault("graphs", {})
    if git is None:
        git = (data["graphs"].get(name) or {}).get("git", True) is not False
    entry = {"path": path} if git else {"path": path, "git": False}
    if data["graphs"].get(name) == entry:
        return False
    data["graphs"][name] = entry
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def exclude_file(root) -> Path:
    """Return the exclude file of this clone: the file that `git rev-parse --git-path info/exclude` names."""
    try:
        done = subprocess.run(["git", "rev-parse", "--git-path", "info/exclude"], cwd=root,
                              capture_output=True, text=True)
    except OSError as error:
        raise UsageError(f"cannot run git: {error}") from error
    if done.returncode != 0 or not done.stdout.strip():
        raise UsageError(f"{root} is not a git clone, so git cannot keep the brain out of it: {done.stderr.strip()}")
    return Path(root) / done.stdout.strip()


def exclude_folder(root, directory, keep=True) -> bool:
    """Add (`keep` True) or remove (`keep` False) `/<directory>/` in the exclude file of this clone. Return True on a change.

    `.gitignore` does not change, and a linked worktree writes the file that git reads for it.
    """
    file = exclude_file(root)
    line = f"/{directory.strip('/')}/"
    lines = file.read_text("utf-8").splitlines() if file.is_file() else []
    if (line in lines) == keep:
        return False
    lines = [*lines, line] if keep else [item for item in lines if item != line]
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("".join(f"{item}\n" for item in lines), encoding="utf-8")
    return True


def inside(root, value) -> Path:
    """Return root/value, and refuse a path that leaves the project root (an absolute path, `..`, or a link)."""
    root = Path(root)
    given = Path(str(value))
    if given.is_absolute() or ".." in given.parts:
        raise UsageError(f"the path must be relative to the project root and stay inside it: {value!r}")
    target = root / given
    # The root is not one of its own parents, so this also refuses the root itself.
    if root.resolve() not in target.resolve().parents:
        raise UsageError(f"the path must stay inside the project root, and is not the root itself: {value!r}")
    return target


def bundle_dir(root) -> Path:
    entry = read_registry(root).get(GRAPH)
    if not entry:
        raise UsageError(f"the ux-hci-design graph is not in {REGISTRY}. "
                         "Run /ux-hci-design:setup first.")
    if not DIR_RE.fullmatch(str(entry["path"])):
        raise UsageError(f"the bundle folder in {REGISTRY} must match [A-Za-z0-9._/-]{{1,100}}: {entry['path']!r}")
    directory = inside(root, entry["path"])
    if not directory.is_dir():
        raise UsageError(f"the folder {entry['path']} does not exist. Run /ux-hci-design:setup first.")
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
