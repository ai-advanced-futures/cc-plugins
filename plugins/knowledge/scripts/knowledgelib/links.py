"""Resolve a link to a file (standard section 5)."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from knowledgelib import DataError, UsageError, manifest, okf, registry, remote

FOUND, MISSING, UNKNOWN, NO_CACHE, REMOTE_MISSING = (
    "found", "missing", "unknown-graph", "no-cache", "remote-missing")


@dataclass(frozen=True)
class Target:
    graph: str
    path: str
    file: Path | None
    state: str

    @property
    def node(self) -> str:
        return f"{self.graph}:{self.path}"


def split(link: str, current: str = "") -> tuple[str, str]:
    link = link.strip().split("#", 1)[0]
    match = okf.GRAPH_LINK_RE.match(link)
    if match:
        return match.group(1), match.group(2)
    if link.startswith("/"):
        return current, link
    raise UsageError(f"{link!r} is not a link: use /<path> or <graph>:/<path>")


def bundle_dir(root, graph, cache_only=False) -> Path | None:
    if not graph.remote:
        return Path(root) / graph.path
    clone = remote.cache_dir(graph.repo)
    if not (clone / ".git").is_dir():
        if cache_only:
            return None
        clone = remote.ensure_cache(graph.repo)
    return clone / graph.path


def inside(bundle: Path, candidate: Path) -> bool:
    """A file counts only when it resolves inside the bundle: no `..` and no symbolic link leaves it."""
    return candidate.is_file() and candidate.resolve().is_relative_to(bundle.resolve())


def find_file(bundle: Path, path: str) -> Path | None:
    direct = bundle / path.lstrip("/")
    if inside(bundle, direct):
        return direct
    try:
        data = manifest.read(bundle)
    except DataError:
        data = None
    for folder in (data or {}).get("id_folders") or []:
        candidate = bundle / folder / Path(path).name
        if inside(bundle, candidate):
            return candidate
    return None


def resolve(root, graphs, current, link, cache_only=False) -> Target:
    name, path = split(link, current)
    graph = graphs.get(name)
    if graph is None:
        return Target(name, path, None, UNKNOWN)
    bundle = bundle_dir(root, graph, cache_only)
    if bundle is None:
        return Target(name, path, None, NO_CACHE)
    file = find_file(bundle, path)
    if file is None:
        return Target(name, path, None, REMOTE_MISSING if graph.remote else MISSING)
    return Target(name, path, file, FOUND)


def cmd_resolve(args) -> int:
    graphs = registry.read(args.root)
    target = resolve(args.root, graphs, args.graph, args.link, args.cache_only)
    if target.state == UNKNOWN:
        registry.check_root(graphs)
    if target.file is None:
        print(f"MISSING {target.node} ({target.state})", file=sys.stderr)
        return 1
    print(okf.shown(args.root, target.file))
    return 0


def cmd_show(args) -> int:
    graphs = registry.read(args.root)
    out = []
    for link in args.links:
        target = resolve(args.root, graphs, args.graph, link, args.cache_only)
        page = okf.read_page(target.file) if target.file else None
        out.append({"link": link, "graph": target.graph, "path": target.path, "state": target.state,
                    "file": okf.shown(args.root, target.file) if target.file else None,
                    "frontmatter": page.frontmatter if page else None})
    print(json.dumps(out, indent=2, default=str))
    return 0


def register(sub) -> None:
    for name, run, help_text in (("resolve", cmd_resolve, "print the file of one link"),
                                 ("show", cmd_show, "print the frontmatter of links as JSON")):
        parser = sub.add_parser(name, help=help_text)
        if name == "resolve":
            parser.add_argument("link")
        else:
            parser.add_argument("links", nargs="+")
        parser.add_argument("--graph", default="", help="the graph of a / link")
        parser.add_argument("--cache-only", action="store_true", help="never clone a remote graph")
        parser.set_defaults(run=run)
