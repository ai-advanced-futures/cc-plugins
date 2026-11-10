"""The registry of graphs: .claude/knowledge.json (standard section 5)."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from knowledgelib import UsageError, rootpath

REGISTRY = Path(".claude") / "knowledge.json"
NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")


@dataclass(frozen=True)
class Graph:
    name: str
    path: str
    repo: str | None = None
    git: bool = True  # False: git does not keep the folder, so a new clone has no folder until the setup of its brain

    @property
    def remote(self) -> bool:
        return self.repo is not None


class Graphs(dict):
    """The graphs of the registry of one root. found is False when the registry file does not exist there."""

    def __init__(self, graphs, root, found: bool):
        super().__init__(graphs)
        self.root, self.found = Path(root), found


def registry_file(root) -> Path:
    return Path(root) / REGISTRY


def check_path(value, name) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UsageError(f"the graph {name!r} has no path")
    path = value.strip()
    if path.startswith("/") or ".." in Path(path).parts:
        raise UsageError(f"the path of {name!r} must be relative to the project root "
                         f"and stay inside it: {value!r}")
    while path.startswith("./"):
        path = path[2:]
    return path.rstrip("/")


def check_name(name) -> str:
    if not isinstance(name, str) or not NAME_RE.match(name):
        raise UsageError(f"{name!r} is not a graph name: use lowercase letters, digits, and '-'")
    return name


def _load(root) -> dict:
    file = registry_file(root)
    if not file.is_file():
        return {"graphs": {}}
    try:
        data = json.loads(file.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UsageError(f"cannot read {REGISTRY}: {error}") from error
    if not isinstance(data, dict) or not isinstance(data.get("graphs"), dict):
        raise UsageError(f"{REGISTRY} has no 'graphs' map")
    return data


def read(root) -> Graphs:
    graphs = {}
    for name, entry in _load(root)["graphs"].items():
        check_name(name)
        if not isinstance(entry, dict):
            raise UsageError(f"the entry of {name!r} in {REGISTRY} is not a map")
        repo = entry.get("repo")
        if repo is not None and (not isinstance(repo, str) or not repo.strip()):
            raise UsageError(f"the repo of {name!r} in {REGISTRY} is not a string")
        git = entry.get("git", True)
        if not isinstance(git, bool):
            raise UsageError(f"the git key of {name!r} in {REGISTRY} is not true or false")
        graphs[name] = Graph(name, check_path(entry.get("path"), name), repo.strip() if repo else None, git)
    return Graphs(graphs, root, registry_file(root).is_file())


def add(root, name, path, repo=None) -> bool:
    check_name(name)
    data = _load(root)
    read(root)
    entry = {"path": check_path(path, name)}
    if repo:
        entry["repo"] = repo
    if data["graphs"].get(name) == entry:
        return False
    data["graphs"][name] = entry
    file = registry_file(root)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def check_root(graphs) -> None:
    """Raise when the registry file does not exist at the root, so the root and the registry do not match.
    A plain dict has no found attribute, so it passes."""
    if getattr(graphs, "found", True) is False:
        raise UsageError(f"the root does not match a path in {REGISTRY.as_posix()}: "
                         f"{registry_file(graphs.root)} does not exist (--root {rootpath.given(graphs.root)}). "
                         "Give the project root, or run /knowledge:setup first.")


def require(graphs, name) -> Graph:
    if name not in graphs:
        check_root(graphs)
        raise UsageError(f"the graph {name!r} is not in {REGISTRY}")
    return graphs[name]


def cmd_list(args) -> int:
    for graph in read(args.root).values():
        print(f"{graph.name}\t{graph.repo or 'local'}\t{graph.path}")
    return 0


def cmd_get(args) -> int:
    graph = require(read(args.root), args.name)
    print(json.dumps({"name": graph.name, "path": graph.path, "repo": graph.repo}))
    return 0


def cmd_add(args) -> int:
    changed = add(args.root, args.name, args.path, args.repo)
    print(f"registry: {'added' if changed else 'unchanged'} {args.name}")
    return 0


def register(sub) -> None:
    parser = sub.add_parser("registry", help="read and change .claude/knowledge.json")
    rsub = parser.add_subparsers(dest="registry_command", required=True)
    rsub.add_parser("list", help="list the graphs").set_defaults(run=cmd_list)
    get = rsub.add_parser("get", help="print one entry as JSON")
    get.add_argument("name")
    get.set_defaults(run=cmd_get)
    add_parser = rsub.add_parser("add", help="add or replace one entry")
    add_parser.add_argument("name")
    add_parser.add_argument("--path", required=True)
    add_parser.add_argument("--repo")
    add_parser.set_defaults(run=cmd_add)
